#!/usr/bin/env bash
# Bootstraps Let's Encrypt certs for both domains the first time this stack
# is deployed. Run once from the infra/ directory:
#   ./certbot/init-letsencrypt.sh
set -euo pipefail

cd "$(dirname "$0")/.."

DOMAINS=("api-capstone.eterosoft.com" "capstone.eterosoft.com")
EMAIL="${CERTBOT_EMAIL:-admin@eterosoft.com}"
COMPOSE="docker compose -f docker-compose.prod.yml"

DATA_PATH="./certbot-data"
mkdir -p "$DATA_PATH/conf" "$DATA_PATH/www"

if [ ! -s "$DATA_PATH/conf/options-ssl-nginx.conf" ]; then
  cat > "$DATA_PATH/conf/options-ssl-nginx.conf" <<'EOF'
ssl_session_cache shared:le_nissl:10m;
ssl_session_timeout 1440m;
ssl_session_tickets off;

ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;

ssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384";
EOF
fi

if [ ! -s "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
  docker run --rm -v "$(pwd)/$DATA_PATH/conf:/out" alpine/openssl \
    dhparam -out /out/ssl-dhparams.pem 2048
fi

# Temporary self-signed certs so nginx can start with its ssl server blocks
# before real certs exist.
for domain in "${DOMAINS[@]}"; do
  mkdir -p "$DATA_PATH/conf/live/$domain"
  if [ ! -e "$DATA_PATH/conf/live/$domain/fullchain.pem" ]; then
    docker run --rm -v "$(pwd)/$DATA_PATH/conf:/etc/letsencrypt" \
      alpine/openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
      -keyout "/etc/letsencrypt/live/$domain/privkey.pem" \
      -out "/etc/letsencrypt/live/$domain/fullchain.pem" \
      -subj "/CN=$domain"
  fi
done

$COMPOSE up -d nginx

for domain in "${DOMAINS[@]}"; do
  rm -rf "$DATA_PATH/conf/live/$domain" "$DATA_PATH/conf/archive/$domain" "$DATA_PATH/conf/renewal/$domain.conf"
  $COMPOSE run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$domain" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email
done

$COMPOSE restart nginx

echo "Done. Certs issued for: ${DOMAINS[*]}"
