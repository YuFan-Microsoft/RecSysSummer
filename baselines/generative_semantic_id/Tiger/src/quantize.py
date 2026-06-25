"""Step 2: learn semantic IDs from item embeddings via residual quantization.

Three methods (pick with --method):
    rqkmeans : residual K-means (normalize residuals each level)   [OneRec-style]
    rvq      : residual vector quantization (no residual normalize)
    rqvae    : residual-quantized VAE (encoder/decoder + commitment loss)

Each item gets D codes (one per hierarchy). Because different items can collapse
to the same D-tuple, we append ONE extra "tie-breaker" digit so every item has a
unique code. The saved semantic ids therefore have H = D + 1 hierarchies.

Example:
    python quantize.py \
        --data.embeddings outputs/embeddings.pt \
        --data.output outputs/semantic_ids.pt \
        --method rqkmeans --num_hierarchies 3 --codebook_width 256
"""

import argparse
import os
import sys

# Make sibling modules importable regardless of how this script is launched.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm

from common import get_device, hierarchize, save_pt, set_seed


# --------------------------------------------------------------------------- #
# Pure-torch K-means (k-means++ init + Lloyd iterations)
# --------------------------------------------------------------------------- #
def kmeans(x: torch.Tensor, k: int, iters: int = 50):
    """Cluster rows of x into k centroids. Returns (centroids, assignments)."""
    n = x.shape[0]
    # k-means++ initialization
    centroids = torch.empty(k, x.shape[1], device=x.device, dtype=x.dtype)
    centroids[0] = x[torch.randint(0, n, (1,), device=x.device)]
    closest = torch.cdist(x, centroids[:1]).squeeze(1) ** 2
    for i in range(1, k):
        probs = closest / closest.sum().clamp(min=1e-12)
        idx = torch.multinomial(probs, 1)
        centroids[i] = x[idx]
        dist = torch.cdist(x, centroids[i : i + 1]).squeeze(1) ** 2
        closest = torch.minimum(closest, dist)

    # Lloyd iterations
    assignments = torch.zeros(n, dtype=torch.long, device=x.device)
    for _ in range(iters):
        assignments = torch.cdist(x, centroids).argmin(dim=1)
        new_centroids = centroids.clone()
        for c in range(k):
            members = x[assignments == c]
            if members.numel() > 0:
                new_centroids[c] = members.mean(dim=0)
        if torch.allclose(new_centroids, centroids, atol=1e-6):
            centroids = new_centroids
            break
        centroids = new_centroids
    return centroids, assignments


# --------------------------------------------------------------------------- #
# Residual K-means / RVQ (no gradient training; just fit codebooks per level)
# --------------------------------------------------------------------------- #
def residual_quantize(embeddings, num_hierarchies, codebook_width, normalize_residuals, iters):
    residual = embeddings.clone()
    codes = []
    for level in range(num_hierarchies):
        if normalize_residuals:
            residual = F.normalize(residual, dim=-1)
        centroids, assign = kmeans(residual, codebook_width, iters=iters)
        codes.append(assign)
        residual = residual - centroids[assign]
    return torch.stack(codes, dim=1)  # (num_items, num_hierarchies)


# --------------------------------------------------------------------------- #
# RQ-VAE: encoder -> residual VQ (straight-through) -> decoder, trained jointly
# --------------------------------------------------------------------------- #
class RQVAE(nn.Module):
    def __init__(self, in_dim, latent_dim, num_hierarchies, codebook_width, commitment=0.25):
        super().__init__()
        self.num_hierarchies = num_hierarchies
        self.commitment = commitment
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 512), nn.ReLU(), nn.Linear(512, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 512), nn.ReLU(), nn.Linear(512, in_dim)
        )
        self.codebooks = nn.ParameterList(
            [nn.Parameter(torch.randn(codebook_width, latent_dim) * 0.1)
             for _ in range(num_hierarchies)]
        )

    def quantize(self, z):
        """Residual VQ over the latent. Returns (quantized, codes, vq_loss)."""
        residual = z
        quantized = torch.zeros_like(z)
        codes = []
        vq_loss = z.new_zeros(())
        for codebook in self.codebooks:
            dist = torch.cdist(residual, codebook)
            idx = dist.argmin(dim=1)
            chosen = codebook[idx]
            vq_loss = vq_loss + F.mse_loss(chosen, residual.detach())
            vq_loss = vq_loss + self.commitment * F.mse_loss(chosen.detach(), residual)
            quantized = quantized + residual + (chosen - residual).detach()  # straight-through
            residual = residual - chosen
            codes.append(idx)
        return quantized, torch.stack(codes, dim=1), vq_loss

    def forward(self, x):
        z = self.encoder(x)
        quantized, codes, vq_loss = self.quantize(z)
        recon = self.decoder(quantized)
        recon_loss = F.mse_loss(recon, x)
        return codes, recon_loss + vq_loss


def train_rqvae(embeddings, num_hierarchies, codebook_width, epochs, batch_size, lr, device):
    model = RQVAE(embeddings.shape[1], 32, num_hierarchies, codebook_width).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    data = embeddings.to(device)
    for epoch in range(epochs):
        perm = torch.randperm(data.shape[0], device=device)
        total = 0.0
        for start in range(0, data.shape[0], batch_size):
            batch = data[perm[start : start + batch_size]]
            _, loss = model(batch)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"  rqvae epoch {epoch + 1}/{epochs}  loss={total:.4f}")
    model.eval()
    with torch.no_grad():
        codes, _ = model(data)
    return codes.cpu()


# --------------------------------------------------------------------------- #
# Tie-breaker: append one extra digit so every item is unique
# --------------------------------------------------------------------------- #
def append_dedup_digit(codes):
    """codes: (num_items, D) -> (num_items, D + 1) with a unique tie-breaker."""
    extra = torch.zeros(codes.shape[0], dtype=torch.long)
    seen = {}
    for i in range(codes.shape[0]):
        key = tuple(codes[i].tolist())
        extra[i] = seen.get(key, 0)
        seen[key] = extra[i].item() + 1
    return torch.cat([codes, extra.unsqueeze(1)], dim=1)


def quantize(args):
    set_seed(args.seed)
    device = get_device(args.device)

    embeddings = torch.load(args.data.embeddings, map_location=device).float()
    print(f"Loaded embeddings {tuple(embeddings.shape)} from {args.data.embeddings}")

    if args.method == "rqkmeans":
        codes = residual_quantize(embeddings, args.num_hierarchies, args.codebook_width,
                                  normalize_residuals=True, iters=args.kmeans_iters)
    elif args.method == "rvq":
        codes = residual_quantize(embeddings, args.num_hierarchies, args.codebook_width,
                                  normalize_residuals=False, iters=args.kmeans_iters)
    elif args.method == "rqvae":
        codes = train_rqvae(embeddings, args.num_hierarchies, args.codebook_width,
                            args.rqvae.epochs, args.rqvae.batch_size, args.rqvae.lr, device)
    else:
        raise ValueError(f"Unknown method: {args.method}")
    codes = codes.cpu()

    codes = append_dedup_digit(codes)
    num_hierarchies = codes.shape[1]
    max_dup = int(codes[:, -1].max().item()) + 1
    if max_dup > args.codebook_width:
        raise ValueError(
            f"Tie-breaker needs {max_dup} slots > codebook_width {args.codebook_width}. "
            "Increase --codebook_width or --num_hierarchies."
        )

    save_pt(
        {"codes": codes, "codebook_width": args.codebook_width, "num_hierarchies": num_hierarchies},
        args.data.output,
    )
    print(f"Saved semantic ids {tuple(codes.shape)} (H={num_hierarchies}, "
          f"max tie-break={max_dup}) -> {args.data.output}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data.embeddings", type=str, required=True)
    p.add_argument("--data.output", type=str, required=True)
    p.add_argument("--method", type=str, default="rqkmeans", choices=["rqkmeans", "rvq", "rqvae"])
    p.add_argument("--num_hierarchies", type=int, default=3, help="codes per item BEFORE tie-break")
    p.add_argument("--codebook_width", type=int, default=256)
    p.add_argument("--kmeans_iters", type=int, default=50)
    p.add_argument("--rqvae.epochs", type=int, default=100)
    p.add_argument("--rqvae.batch_size", type=int, default=1024)
    p.add_argument("--rqvae.lr", type=float, default=1e-3)
    p.add_argument("--device", type=str, default="auto")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


if __name__ == "__main__":
    quantize(hierarchize(parse_args()))
