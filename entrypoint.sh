#!/bin/sh
set -e
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Secret
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
if [ -z "${JWT_SECRET}" ]; then
  echo "ERRO: JWT_SECRET not defined."
  exit 1
fi
echo -n "${JWT_SECRET}" > /mosquitto/config/jwt_secret.key

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Configuration Injection
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Defaults
: ${MAX_CONNECTIONS:=65536}
: ${MAX_INFLIGHT_MESSAGES:=20}
: ${MAX_QUEUED_MESSAGES:=1024}

echo "Configuring Mosquitto with:"
echo "MAX_CONNECTIONS=${MAX_CONNECTIONS}"
echo "MAX_INFLIGHT_MESSAGES=${MAX_INFLIGHT_MESSAGES}"
echo "MAX_QUEUED_MESSAGES=${MAX_QUEUED_MESSAGES}"

sed -i "s/^max_connections .*/max_connections $MAX_CONNECTIONS/" /mosquitto/config/mosquitto.conf
sed -i "s/^max_inflight_messages .*/max_inflight_messages $MAX_INFLIGHT_MESSAGES/" /mosquitto/config/mosquitto.conf
sed -i "s/^max_queued_messages .*/max_queued_messages $MAX_QUEUED_MESSAGES/" /mosquitto/config/mosquitto.conf

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Permissions
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
chown mosquitto:mosquitto /mosquitto/config/jwt_secret.key
chmod 600 /mosquitto/config/jwt_secret.key
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
exec "$@"
