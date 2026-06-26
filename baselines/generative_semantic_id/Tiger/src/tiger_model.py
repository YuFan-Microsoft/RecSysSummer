"""TIGER generative recommender: a small T5 encoder-decoder over semantic IDs.

Faithful to the original GRID/TIGER implementation:
  - one embedding table shared by encoder and decoder, with a per-hierarchy
    offset (h * codebook_width) so a single table serves all levels;
  - independent per-hierarchy linear output heads (bias-free), exactly the
    original `decoder_mlp`;
  - a learnable separator token appended after each item in the encoder input
    (`should_add_sep_token=True`);
  - feed-forward "bloating": each T5 FF block is replaced by a multi-layer MLP
    (`mlp_layers`, default 2);
  - optional user embedding prepended to the history (`num_user_bins`, off by
    default, matching the original config).

Reference: Rajput et al., "Recommender Systems with Generative Retrieval"
(NeurIPS 2023), https://arxiv.org/abs/2305.05065
"""

import copy

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import T5Config
from transformers.models.t5.modeling_t5 import T5LayerNorm, T5Stack


# --------------------------------------------------------------------------- #
# Feed-forward bloating (the original T5MultiLayerFF): replaces T5's single FF
# layer with an `num_layers`-deep MLP, keeping T5's layernorm + residual.
# --------------------------------------------------------------------------- #
class _MLP(nn.Module):
    def __init__(self, dim, hidden, num_layers, dropout):
        super().__init__()
        layers, prev = [], dim
        for _ in range(num_layers):
            layers += [nn.Linear(prev, hidden), nn.ReLU(), nn.Dropout(dropout)]
            prev = hidden
        layers += [nn.Linear(prev, dim)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class T5MultiLayerFF(nn.Module):
    def __init__(self, config, num_layers):
        super().__init__()
        self.mlp = _MLP(config.d_model, config.d_ff, num_layers, config.dropout_rate)
        self.layer_norm = T5LayerNorm(config.d_model, eps=config.layer_norm_epsilon)
        self.dropout = nn.Dropout(config.dropout_rate)

    def forward(self, hidden_states):
        h = self.layer_norm(hidden_states)
        h = self.mlp(h)
        return hidden_states + self.dropout(h)


class TigerModel(nn.Module):
    def __init__(self, num_hierarchies, codebook_width, d_model=128, num_layers=4,
                 num_heads=6, d_ff=1024, d_kv=64, dropout=0.10, mlp_layers=2,
                 add_sep_token=True, num_user_bins=None):
        super().__init__()
        self.num_hierarchies = num_hierarchies  # H (includes tie-breaker digit)
        self.codebook_width = codebook_width    # V
        self.pad_id = num_hierarchies * codebook_width  # dedicated padding row

        # Shared embedding table: H * V real tokens + 1 padding row.
        self.embedding = nn.Embedding(num_hierarchies * codebook_width + 1, d_model)
        self.bos = nn.Parameter(torch.randn(d_model) * 0.02)
        self.sep_token = nn.Parameter(torch.randn(d_model) * 0.02) if add_sep_token else None
        self.user_embedding = nn.Embedding(num_user_bins, d_model) if num_user_bins else None

        base = T5Config(
            vocab_size=codebook_width, d_model=d_model, d_kv=d_kv, d_ff=d_ff,
            num_layers=num_layers, num_heads=num_heads, dropout_rate=dropout,
            is_encoder_decoder=False, use_cache=False,
        )
        enc_cfg = copy.deepcopy(base)
        enc_cfg.is_decoder = False
        dec_cfg = copy.deepcopy(base)
        dec_cfg.is_decoder = True
        dec_cfg.add_cross_attention = True
        self.encoder = T5Stack(enc_cfg)
        self.decoder = T5Stack(dec_cfg)

        if mlp_layers:
            # The feed-forward sub-layer is always the last entry of T5Block.layer.
            for block in self.encoder.block:
                block.layer[-1] = T5MultiLayerFF(enc_cfg, mlp_layers)
            for block in self.decoder.block:
                block.layer[-1] = T5MultiLayerFF(dec_cfg, mlp_layers)

        self.heads = nn.ModuleList(
            [nn.Linear(d_model, codebook_width, bias=False) for _ in range(num_hierarchies)]
        )

    # --------------------------------------------------------------------- #
    def _embed_history(self, input_tokens, mask):
        """input_tokens: (B, L) raw codes; add hierarchy offsets, mask padding."""
        L = input_tokens.shape[1]
        offsets = (torch.arange(L, device=input_tokens.device) % self.num_hierarchies)
        offsets = offsets * self.codebook_width
        tokens = input_tokens + offsets.unsqueeze(0)
        tokens = torch.where(mask.bool(), tokens, torch.full_like(tokens, self.pad_id))
        return self.embedding(tokens)

    def _inject_sep_token(self, emb, mask):
        """Append a sep token after each item's H tokens. emb: (B, L, d)."""
        B, L, d = emb.shape
        n_items = L // self.num_hierarchies
        emb = emb.view(B, n_items, self.num_hierarchies, d)
        sep = self.sep_token.view(1, 1, 1, d).expand(B, n_items, 1, d)
        emb = torch.cat([emb, sep], dim=2).reshape(B, n_items * (self.num_hierarchies + 1), d)
        m = mask.view(B, n_items, self.num_hierarchies)
        m = torch.cat([m, m[:, :, -1:]], dim=2).reshape(B, n_items * (self.num_hierarchies + 1))
        return emb, m

    def encode(self, input_tokens, mask, user_id=None):
        """Returns (encoder_hidden, encoder_mask). The mask may grow if a sep
        token and/or a user token are added."""
        emb = self._embed_history(input_tokens, mask)
        if self.sep_token is not None:
            emb, mask = self._inject_sep_token(emb, mask)
        if self.user_embedding is not None and user_id is not None:
            ue = self.user_embedding(torch.remainder(user_id, self.user_embedding.num_embeddings))
            emb = torch.cat([ue.unsqueeze(1), emb], dim=1)
            ones = torch.ones(mask.shape[0], 1, dtype=mask.dtype, device=mask.device)
            mask = torch.cat([ones, mask], dim=1)
        hidden = self.encoder(inputs_embeds=emb, attention_mask=mask).last_hidden_state
        return hidden, mask

    def _decode(self, decoder_inputs_embeds, enc_hidden, enc_mask):
        return self.decoder(
            inputs_embeds=decoder_inputs_embeds,
            encoder_hidden_states=enc_hidden,
            encoder_attention_mask=enc_mask,
        ).last_hidden_state

    # --------------------------------------------------------------------- #
    def forward(self, input_tokens, mask, target_tokens, user_id=None):
        """Teacher-forced training. Returns the summed cross-entropy loss."""
        B = input_tokens.shape[0]
        H, V = self.num_hierarchies, self.codebook_width
        enc_hidden, enc_mask = self.encode(input_tokens, mask, user_id)

        # decoder input = [BOS, emb(tgt_0..tgt_{H-2})] with per-hierarchy offsets
        offsets = torch.arange(H - 1, device=input_tokens.device) * V
        prev_emb = self.embedding(target_tokens[:, :-1] + offsets.unsqueeze(0))  # (B,H-1,d)
        dec_in = torch.cat([self.bos.expand(B, 1, -1), prev_emb], dim=1)         # (B,H,d)
        dec_out = self._decode(dec_in, enc_hidden, enc_mask)                     # (B,H,d)

        loss = dec_out.new_zeros(())
        for h in range(H):
            logits = self.heads[h](dec_out[:, h])      # (B, V)
            loss = loss + F.cross_entropy(logits, target_tokens[:, h])
        return loss

    @torch.no_grad()
    def generate(self, input_tokens, mask, beam_size=10, user_id=None):
        """Beam search. Returns (beams (B, beam, H) raw codes, scores (B, beam)).

        Ranks by cumulative log-prob, which is the same ordering as the
        original's cumulative-probability (product) beam scoring.
        """
        B = input_tokens.shape[0]
        H, V = self.num_hierarchies, self.codebook_width
        d = self.embedding.embedding_dim
        enc_hidden, enc_mask = self.encode(input_tokens, mask, user_id)
        L = enc_hidden.shape[1]

        # Hierarchy 0
        dec_in = self.bos.expand(B, 1, -1)
        dec_out = self._decode(dec_in, enc_hidden, enc_mask)[:, -1]   # (B, d)
        logp = F.log_softmax(self.heads[0](dec_out), dim=-1)          # (B, V)
        scores, idx = logp.topk(beam_size, dim=-1)                    # (B, beam)
        beams = idx.unsqueeze(-1)                                     # (B, beam, 1)

        enc_b = enc_hidden.unsqueeze(1).expand(B, beam_size, L, d).reshape(B * beam_size, L, d)
        mask_b = enc_mask.unsqueeze(1).expand(B, beam_size, L).reshape(B * beam_size, L)

        for h in range(1, H):
            cur = beams.reshape(B * beam_size, h)                 # (B*beam, h)
            offsets = torch.arange(h, device=input_tokens.device) * V
            emb = self.embedding(cur + offsets.unsqueeze(0))      # (B*beam, h, d)
            dec_in = torch.cat([self.bos.expand(B * beam_size, 1, -1), emb], dim=1)
            dec_out = self._decode(dec_in, enc_b, mask_b)[:, -1]  # (B*beam, d)
            logp = F.log_softmax(self.heads[h](dec_out), dim=-1)  # (B*beam, V)

            total = scores.reshape(B * beam_size, 1) + logp        # (B*beam, V)
            total = total.reshape(B, beam_size * V)
            scores, flat = total.topk(beam_size, dim=-1)           # (B, beam)
            beam_idx = flat // V
            token_idx = flat % V
            prev = torch.gather(beams, 1, beam_idx.unsqueeze(-1).expand(B, beam_size, h))
            beams = torch.cat([prev, token_idx.unsqueeze(-1)], dim=2)
        return beams, scores
