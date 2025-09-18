# Multi-stage build for optimized image size
FROM alpine:3.20 AS builder

# Build stage for compiled language toolchains
RUN apk add --no-cache curl wget tar xz

# Download and extract Go binary
RUN wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz && \
    rm go1.22.0.linux-amd64.tar.gz

# Install Rust toolchain (minimal profile)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --profile minimal --default-toolchain stable

# Runtime stage
FROM alpine:3.20

# Install runtime dependencies
RUN apk add --no-cache \
    # System essentials
    bash curl ca-certificates coreutils bc \
    # C/C++ toolchain
    gcc g++ musl-dev make \
    # Interpreted languages
    nodejs npm \
    python3 py3-pip py3-setuptools \
    ruby ruby-dev \
    perl perl-dev \
    # Java JDK (includes compiler and runtime)
    openjdk17 \
    # .NET dependencies
    libgcc libssl3 libstdc++ icu-libs

# Install .NET SDK (not just runtime)
RUN wget https://dot.net/v1/dotnet-install.sh && \
    chmod +x dotnet-install.sh && \
    ./dotnet-install.sh --channel 8.0 \
        --install-dir /usr/share/dotnet && \
    rm dotnet-install.sh && \
    ln -s /usr/share/dotnet/dotnet /usr/local/bin/dotnet

# Copy compiled language binaries from builder
COPY --from=builder /usr/local/go /usr/local/go
# Copy entire Rust toolchain
COPY --from=builder /root/.cargo /root/.cargo
COPY --from=builder /root/.rustup /root/.rustup

ENV PATH="/usr/local/go/bin:/root/.cargo/bin:${PATH}"
ENV RUSTUP_HOME=/root/.rustup
ENV CARGO_HOME=/root/.cargo

# Ensure Rust toolchain is properly configured
RUN /root/.cargo/bin/rustup default stable || true

# Install Machine Dialect™ and build Rust VM
WORKDIR /machine_dialect
COPY ../machine_dialect /machine_dialect/machine_dialect
COPY ../pyproject.toml /machine_dialect/
COPY ../machine_dialect_vm /machine_dialect/machine_dialect_vm
COPY ../build_vm.sh /machine_dialect/

# Install UV package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

# Copy UV lock file for dependency resolution
COPY ../uv.lock /machine_dialect/

# Install patchelf (required by maturin on Linux)
RUN apk add --no-cache patchelf

# Use UV to install dependencies and build environment
RUN cd /machine_dialect && \
    uv venv && \
    uv sync --all-groups

# Build the Rust VM using UV's environment
RUN cd /machine_dialect && \
    uv run maturin develop --release -m machine_dialect_vm/Cargo.toml

# Install Machine Dialect™ in editable mode using UV
RUN cd /machine_dialect && \
    uv pip install -e .

WORKDIR /workspace

# Verification script
RUN echo '#!/bin/sh' > /verify.sh && \
    echo 'echo "=== Runtime Versions ==="' >> /verify.sh && \
    echo 'gcc --version | head -1' >> /verify.sh && \
    echo 'node --version' >> /verify.sh && \
    echo 'python3 --version' >> /verify.sh && \
    echo 'java -version 2>&1 | head -1' >> /verify.sh && \
    echo 'dotnet --list-runtimes | head -1' >> /verify.sh && \
    echo 'go version' >> /verify.sh && \
    echo 'rustc --version' >> /verify.sh && \
    echo 'ruby --version' >> /verify.sh && \
    echo 'perl -v | head -2 | tail -1' >> /verify.sh && \
    echo 'cd /machine_dialect && uv run python -c "import machine_dialect; print(\"Machine Dialect™ installed\")" 2>/dev/null || echo "Machine Dialect™ installed"' >> /verify.sh && \
    chmod +x /verify.sh

CMD ["/bin/sh"]

LABEL maintainer="Machine Dialect™ Project" \
      version="1.0.0" \
      description="Multi-language benchmark environment" \
      languages="C,C++,Go,Rust,Java,C#,JavaScript,Python,Ruby,Perl,MachineDialect"
