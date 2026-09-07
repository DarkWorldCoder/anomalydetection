# Production deploy

Docker-based deploy for:

- `capstone.eterosoft.com` — frontend (static Vite/React build, served by Nginx)
- `api-capstone.eterosoft.com` — backend (FastAPI, proxied by Nginx)

Stack: `postgres` + `api` (FastAPI) + `frontend` (one-shot build that populates a
shared volume) + `nginx` (TLS termination, reverse proxy, static file serving) +
`certbot` (Let's Encrypt issuance/renewal).

## Prerequisites

- DNS: `capstone.eterosoft.com` and `api-capstone.eterosoft.com` A/AAAA records
  point at this server's public IP.
- Ports 80 and 443 open/forwarded to this host.
- Docker + Docker Compose v2 installed.

## First-time setup

```bash
cd infra
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD, SECRET_KEY, CERTBOT_EMAIL

docker compose -f docker-compose.prod.yml build

./certbot/init-letsencrypt.sh
```

The init script issues real Let's Encrypt certificates for both domains (it
starts nginx with temporary self-signed certs first, since nginx won't boot
with `ssl` server blocks pointing at files that don't exist yet, then swaps
them for real ones via the HTTP-01 webroot challenge).

## Subsequent deploys

```bash
cd infra
docker compose -f docker-compose.prod.yml up -d --build
```

The `frontend` service rebuilds the SPA and copies it into the shared
`frontend_dist` volume, then exits; `nginx` serves that volume read-only. The
`certbot` service keeps renewing certs automatically every 12h in the
background.

## Layout

```
infra/
  docker-compose.prod.yml   # postgres, api, frontend (build), nginx, certbot
  frontend.Dockerfile       # multi-stage: npm build -> copies dist into a volume
  nginx/
    api.conf                # api-capstone.eterosoft.com -> proxy_pass to api:8000
    frontend.conf           # capstone.eterosoft.com -> static SPA + fallback
  certbot/
    init-letsencrypt.sh     # one-time bootstrap for both domains
  certbot-data/             # created at runtime: certs + ACME webroot (gitignored)
  .env.example
```

## Notes

- Backend CORS is locked to `https://capstone.eterosoft.com` in
  `docker-compose.prod.yml` (`BACKEND_CORS_ORIGINS`).
- `certbot-data/` holds live certificates and must not be committed; it's in
  `.gitignore`.
- Run backend DB migrations (`alembic upgrade head`) inside the `api`
  container after first deploy:
  `docker compose -f docker-compose.prod.yml exec api alembic upgrade head`
