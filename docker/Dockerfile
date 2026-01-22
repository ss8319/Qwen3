ARG CUDA_VERSION=12.4.1
ARG PYTHON_VERSION=3.10
ARG UBUNTU_VERSION=22.04
# Use a standard, widely available devel image
ARG from=nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}

FROM ${from} as base

# Install system dependencies
# For Ubuntu 22.04, use python3 packages (Python 3.10 is default)
RUN apt update -y && \
    apt upgrade -y && \
    apt install -y --no-install-recommends \
        git \
        git-lfs \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        wget \
        vim \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast and robust dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set up Python symlinks
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    python3 --version

# Initialize git lfs
RUN git lfs install

FROM base as dev

WORKDIR /workspace

# Set environment variables for uv
ENV UV_SYSTEM_PYTHON=1
ENV UV_LINK_MODE=copy

# Install PyTorch with CUDA 12.4 support
# Using 2.6.0 which is the latest stable available for cu124
RUN uv pip install --no-cache \
    torch==2.6.0 \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu124

# Copy requirements and install remaining dependencies
# We use --override to ignore the torch==2.9.1 in requirements.txt if it exists
COPY requirements.txt /workspace/requirements.txt
RUN uv pip install --no-cache -r /workspace/requirements.txt

FROM dev as vllm

# Install vLLM (compatible with CUDA 12.4)
# vLLM 0.9.0+ supports Qwen3 models
# Note: vLLM will automatically detect CUDA 12.4 compatibility
RUN uv pip install --no-cache "vllm>=0.9.0"

FROM dev as final-base

# Copy project files
COPY . /workspace/

WORKDIR /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000 30000

CMD ["/bin/bash"]

FROM vllm as final

# Copy project files
COPY . /workspace/

WORKDIR /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000 30000

CMD ["/bin/bash"]

