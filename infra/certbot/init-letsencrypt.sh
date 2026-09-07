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

if [ ! -e "$DATA_PATH/conf/options-ssl-nginx.conf" ]; then
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
    -o "$DATA_PATH/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
    -o "$DATA_PATH/conf/ssl-dhparams.pem"
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
