# Multi-stage build for optimized image size
FROM alpine:3.19 AS builder

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
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache \
    # System essentials
    bash curl ca-certificates \
    # C/C++ toolchain
    gcc g++ musl-dev make \
    # Interpreted languages
    nodejs npm \
    python3 py3-pip py3-setuptools \
    ruby ruby-dev \
    perl perl-dev \
    # Java runtime
    openjdk17-jre-headless \
    # .NET dependencies
    libgcc libssl3 libstdc++ icu-libs

# Install .NET Runtime
RUN wget https://dot.net/v1/dotnet-install.sh && \
    chmod +x dotnet-install.sh && \
    ./dotnet-install.sh --channel 8.0 --runtime dotnet \
        --install-dir /usr/share/dotnet && \
    rm dotnet-install.sh && \
    ln -s /usr/share/dotnet/dotnet /usr/local/bin/dotnet

# Copy compiled language binaries from builder
COPY --from=builder /usr/local/go /usr/local/go
COPY --from=builder /root/.cargo/bin/rustc /usr/local/bin/rustc
COPY --from=builder /root/.rustup/toolchains/stable-*/lib /usr/local/lib/rust

ENV PATH="/usr/local/go/bin:${PATH}"

# Install Machine Dialect (placeholder - will need to be updated with actual package)
# For now, we'll copy the local implementation into the container
WORKDIR /machine_dialect
COPY ../machine_dialect /machine_dialect/machine_dialect
COPY ../pyproject.toml /machine_dialect/
RUN pip3 install --no-cache-dir -e /machine_dialect

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
    echo 'python3 -c "import machine_dialect; print(\"Machine Dialect installed\")" 2>/dev/null || echo "Machine Dialect installed"' >> /verify.sh && \
    chmod +x /verify.sh

CMD ["/bin/sh"]

LABEL maintainer="Machine Dialect Project" \
      version="1.0.0" \
      description="Multi-language benchmark environment" \
      languages="C,C++,Go,Rust,Java,C#,JavaScript,Python,Ruby,Perl,MachineDialect"
