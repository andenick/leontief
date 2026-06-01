# Deploy Runbook — Wassily (Leontief) I-O Website

**Subdomain:** `leontief.nickanderson.us`
**Stack:** FastAPI + gunicorn/uvicorn · Caddy 2.8 · Cloudflare Tunnel
**Hardware:** Carson mini PC (go-live GATED — box not yet online; see below)
**Sites registry:** `Council/Carson/Technical/sites_registry.json`
**Architecture:** `Council/Carson/Technical/HOSTING_ARCHITECTURE.md`

---

## Why no refresh service?

BEA publishes I-O tables annually (typically April/May for the prior year).
Unlike Gerhard (live FRED/BLS data), Wassily's data is fully static between
BEA vintages. There is no scheduled refresh container. Redeploy (`docker compose
up -d --build`) once per BEA release after re-running the pre-build steps.

---

## 0. Prerequisites on the dev machine

Ensure the Python webapp venv is active:

```powershell
# Windows dev machine (D:\Arcanum\Projects\Leontief\webapp)
.venv\Scripts\Activate
```

---

## 1. PRE-BUILD: generate site_data/ on the dev machine

**Must be done before `docker build`.** The container does NOT have access to
`Technical/data/` (source pkl files); `site_data/` must be fully populated
before the image is built and then copied in.

```bash
cd D:\Arcanum\Projects\Leontief\webapp

# Step 1: vendor front-end assets (plotly, KaTeX, Pygments CSS)
python data_pipeline/vendor.py

# Step 2: build the sector registry (sectors.json)
python data_pipeline/build_sectors.py

# Step 3: build the site manifest and I-O cache (site_manifest.json + cache/)
python data_pipeline/build_cache.py

# Step 4 (OPTIONAL — not yet implemented; skip if run_studies.py does not exist):
# python data_pipeline/run_studies.py
```

After these steps, verify `webapp/site_data/` contains:
- `sectors.json`
- `site_manifest.json`
- `cache/` with parquet/json outputs

---

## 2. Build and start the stack

From the project root (`D:\Arcanum\Projects\Leontief`):

```bash
docker compose -f webapp/deploy/docker-compose.yml up -d --build
```

This builds the image (copies app/, content/, site_data/) and starts:
- `app` — gunicorn on internal port 8080
- `caddy` — reverse proxy on 80/443 with automatic HTTPS

---

## 3. Verify locally

```bash
# Health check
curl http://localhost:8080/healthz
# Expected: {"status":"ok","site":"Wassily","manifest_present":true,...}

# Via Caddy (on the server, before public DNS is live)
curl -H "Host: leontief.nickanderson.us" http://localhost/healthz
```

---

## 4. Cloudflare Tunnel (public exposure — no open router ports)

TLS terminates at the Cloudflare edge. The box never opens an inbound port.

### 4a. Install cloudflared (on the Carson mini PC, Debian/Ubuntu)

```bash
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

### 4b. Authenticate

```bash
cloudflared tunnel login
# Opens a browser — authorize on Cloudflare dashboard
```

### 4c. Create the tunnel

```bash
cloudflared tunnel create leontief
# Records a UUID and writes ~/.cloudflared/<UUID>.json
```

### 4d. Route DNS

```bash
cloudflared tunnel route dns leontief leontief.nickanderson.us
# Creates a CNAME in Cloudflare DNS pointing to the tunnel
```

### 4e. Install and start the cloudflared service

```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

Cloudflare forwards `leontief.nickanderson.us` → tunnel → `localhost:80` (Caddy)
→ `app:8080` (gunicorn). No router port forwarding needed.

---

## 5. Verify external access

```bash
curl -I https://leontief.nickanderson.us
# Expected: HTTP/2 200, server: cloudflare
curl https://leontief.nickanderson.us/healthz
# Expected: {"status":"ok","site":"Wassily",...}
```

---

## 6. GO-LIVE GATE

**Carson mini PC is not yet online (as of 2026-05-31).** This runbook is
complete and ready; execute from step 0 once:

- [ ] Carson hardware purchased and powered on
- [ ] Debian/Ubuntu headless installed; SSH key auth; UFW default-deny
- [ ] Docker + Compose plugin installed; non-root docker group
- [ ] Tailscale joined (admin access over VPN)
- [ ] `nickanderson.us` DNS nameservers moved to Cloudflare
- [ ] cloudflared installed and authenticated

Reference checklist: `Council/Carson/Technical/HOSTING_ARCHITECTURE.md`
(Open setup checklist section).

---

## 7. Data refresh (annual — new BEA vintage)

When BEA publishes a new I-O vintage:

1. Obtain new BEA data files; place in `Technical/data/`
2. Re-run pre-build steps (§1 above)
3. `docker compose -f webapp/deploy/docker-compose.yml up -d --build`
4. Verify `curl https://leontief.nickanderson.us/healthz` shows updated counts

---

## 8. Non-Docker path (systemd)

See `leontief-web.service` for a bare-metal venv deploy. Useful for:
- Troubleshooting without Docker
- Running directly under nginx (see `nginx.conf`)

Install:
```bash
sudo cp webapp/deploy/leontief-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now leontief-web
```

---

## Files in this directory

| File | Role |
|------|------|
| `Dockerfile` | Production image (python:3.12-slim, vendored assets, pre-built site_data) |
| `docker-compose.yml` | app + caddy services; no refresh service (static data) |
| `Caddyfile` | Reverse proxy + automatic HTTPS; `leontief.nickanderson.us` |
| `nginx.conf` | Equivalent nginx alternative (for parity with Gerhard) |
| `leontief-web.service` | systemd unit for non-Docker venv deploy |
| `.env.example` | Environment variable template (no secrets needed) |
| `README.md` | This runbook |
