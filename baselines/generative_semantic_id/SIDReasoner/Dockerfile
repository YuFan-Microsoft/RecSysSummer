# Base image: ACPT PyTorch + CUDA 12.6 + cuDNN9 (torch is pinned to 2.6.0 below).
FROM mcr.microsoft.com/azureml/curated/acpt-pytorch-2.8-cuda12.6:2

# System packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        openssh-server \
        openssh-client \
        tmux \
        vim \
        zip \
        unzip \
        curl \
        git \
        build-essential \
        libgl1-mesa-glx \
        libglib2.0-0 \
        cudnn9-cuda-12 \
        dsh \
        pdsh && \
    rm -rf /var/lib/apt/lists/*

# Git LFS (for pulling HuggingFace checkpoints)
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends git-lfs && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

# PyTorch: keep the cu124 build (old C++ ABI) to match vllm 0.8.5.post1 + flash-attn cxx11abiFALSE.
RUN pip install --upgrade pip
RUN pip install --no-cache-dir \
    torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
    --index-url https://download.pytorch.org/whl/cu124

# Python deps: SFT (Stage 1/2) + evaluation + RL (Stage 3, VERL)
RUN pip install --no-cache-dir \
    "transformers[hf_xet]>=4.51.0" \
    accelerate \
    datasets \
    peft \
    tokenizers \
    safetensors \
    hf-transfer \
    "numpy<2.0.0" \
    pandas \
    "pyarrow>=15.0.0" \
    scipy \
    einops \
    sentencepiece \
    tqdm \
    fire \
    wandb \
    bitsandbytes \
    opencv-python \
    packaging \
    pyyaml \
    tensordict==0.6.2 \
    "ray[default]" \
    hydra-core \
    omegaconf \
    codetiming \
    dill \
    pybind11 \
    liger-kernel \
    mathruler \
    pylatexenc \
    qwen-vl-utils \
    "nvidia-ml-py>=12.560.30" \
    "fastapi[standard]>=0.115.0" \
    "optree>=0.13.0" \
    "pydantic>=2.9" \
    "grpcio>=1.62.1" \
    vllm==0.8.5.post1

# CUDA-compiled accelerators (matched to torch 2.6 / cu12, cxx11abi=FALSE)
RUN pip install --no-cache-dir \
    https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

RUN pip install --no-cache-dir \
    https://github.com/flashinfer-ai/flashinfer/releases/download/v0.2.2.post1/flashinfer_python-0.2.2.post1+cu124torch2.6-cp38-abi3-linux_x86_64.whl

# Optional backends (disabled; RL uses vLLM + FSDP):
# RUN pip install --no-cache-dir "sglang[all]==0.4.6.post1" \
#     --find-links https://flashinfer.ai/whl/cu124/torch2.6/flashinfer-python && \
#     pip install --no-cache-dir torch-memory-saver
# RUN NVTE_FRAMEWORK=pytorch pip install --no-deps --no-cache-dir \
#         git+https://github.com/NVIDIA/TransformerEngine.git@v2.2.1 && \
#     pip install --no-deps --no-cache-dir \
#         git+https://github.com/NVIDIA/Megatron-LM.git@core_v0.12.2