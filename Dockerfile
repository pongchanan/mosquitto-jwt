# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Stage 1: Compile Mosquitto and the Plugin
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim AS builder

ENV MOSQUITTO_VERSION=2.0.18
ENV RUST_VERSION=1.85

# Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libc-ares-dev \
    uuid-dev \
    libwebsockets-dev \
    libcjson-dev \
    libsystemd-dev \
    wget \
    git \
    curl \
    ca-certificates \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
ENV PATH="/root/.cargo/bin:${PATH}"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain $RUST_VERSION

# Compile Mosquitto
WORKDIR /tmp
RUN wget https://mosquitto.org/files/source/mosquitto-${MOSQUITTO_VERSION}.tar.gz \
    && tar -xzf mosquitto-${MOSQUITTO_VERSION}.tar.gz \
    && cd mosquitto-${MOSQUITTO_VERSION} \
    && make WITH_WEBSOCKETS=yes WITH_SRV=yes WITH_TLS=yes \
    && make install \
    && ldconfig

# Compile the plugin
WORKDIR /tmp
RUN git clone --branch 0.4.0 --depth 1 https://github.com/wiomoc/mosquitto-jwt-auth.git \
    && cd mosquitto-jwt-auth \
    && cargo build --release
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Stage 2: Final Image (only binaries and configs)
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim

ARG JWT_SECRET

RUN apt-get update && apt-get install -y \
    libssl-dev \
    libc-ares2 \
    libwebsockets17 \
    libcjson1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r mosquitto && useradd -r -g mosquitto mosquitto

RUN mkdir -p /mosquitto/config \
    && mkdir -p /mosquitto/data \
    && mkdir -p /mosquitto/log \
    && mkdir -p /mosquitto/plugins \
    && mkdir -p /mosquitto/run

# Copy files from the build stage
COPY --from=builder /usr/local/sbin/mosquitto /usr/local/sbin/mosquitto
COPY --from=builder /usr/local/lib/libmosquitto.so.1 /usr/local/lib/libmosquitto.so.1
COPY --from=builder /tmp/mosquitto-jwt-auth/target/release/libmosquitto_jwt_auth.so /mosquitto/plugins/

# Copy mosquitto.conf
COPY mosquitto.conf /mosquitto/config/mosquitto.conf

COPY entrypoint.sh /entrypoint.sh
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Permissions & Users
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
RUN chown -R mosquitto:mosquitto /mosquitto \
    && chmod 644 /mosquitto/config/* \
    && chmod 755 /mosquitto/plugins/libmosquitto_jwt_auth.so \
    && chmod 755 /mosquitto/run \
    && chmod +x /entrypoint.sh

USER mosquitto
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Ports
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
EXPOSE 1883 9001
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/local/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]
