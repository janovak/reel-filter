# Reel Filter — Oracle VM Deployment Guide

Complete step-by-step guide to deploy Reel Filter on an Oracle Cloud VM with
Cloudflare Tunnel for DNS/SSL. No firewall rules, no nginx, no certs.

Handles all four URL combos:
- `http://reelfilter.com` → `https://www.reelfilter.com`
- `https://reelfilter.com` → `https://www.reelfilter.com`
- `http://www.reelfilter.com` → `https://www.reelfilter.com`
- `https://www.reelfilter.com` ✅ (canonical)

---

## Part 1: VM Base Setup

### 1.1 SSH Into Your VM

```bash
ssh -i <your-key> ubuntu@<vm-public-ip>
```

### 1.2 System Update & Essential Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git curl
```

### 1.3 Docker Permissions

```bash
sudo usermod -aG docker $USER
# IMPORTANT: logout and SSH back in for group change to take effect
exit
```

```bash
ssh -i <your-key> ubuntu@<vm-public-ip>
# Verify docker works without sudo
docker ps
```

---

## Part 2: Clone & Configure the App

### 2.1 Clone Repository

```bash
cd ~
git clone <your-repo-url> reel-filter
cd reel-filter
```

### 2.2 Create Environment File

```bash
cp backend/.env.example .env
nano .env
```

Set these values:

```env
# Database
DB_PASSWORD=<generate-a-strong-password>

# OMDb API (get key at https://www.omdbapi.com/apikey.aspx)
OMDB_API_KEY=<your-omdb-api-key>

# CORS — must match your domain
CORS_ORIGINS=https://www.reelfilter.com

# Frontend API URL — tells the React app where the backend lives
VITE_API_BASE_URL=https://www.reelfilter.com/api

# Environment
ENVIRONMENT=production
```

Generate a strong DB password:
```bash
openssl rand -base64 24
```

---

## Part 3: Start the Application

### 3.1 Build and Start All Containers

```bash
cd ~/reel-filter
docker compose up -d --build
```

This starts:
- **PostgreSQL 15** on port 5432 (internal only)
- **Redis 7** on port 6379 (internal only)
- **FastAPI backend** on port 8000
- **React frontend** on port 3000
- **Celery worker** (background task processing)
- **Celery beat** (weekly refresh scheduler)

### 3.2 Verify Containers Are Running

```bash
docker compose ps
```

All containers should show `Up`. DB and Redis should show `(healthy)`.

### 3.3 Quick Smoke Test

```bash
curl http://localhost:8000/api/health
curl -s http://localhost:3000 | head -5
```

---

## Part 4: Cloudflare DNS Setup

### 4.1 Add Domain to Cloudflare

1. Sign up / log in at [dash.cloudflare.com](https://dash.cloudflare.com)
2. Click **Add a Site** → enter `reelfilter.com` → select **Free** plan
3. Cloudflare will scan existing DNS records

### 4.2 Update Nameservers at Your Registrar

1. Cloudflare gives you two nameservers (e.g., `ada.ns.cloudflare.com`,
   `bob.ns.cloudflare.com`)
2. Go to your domain registrar (GoDaddy, Namecheap, etc.) and replace the
   existing nameservers with Cloudflare's
3. Wait for propagation (can take up to 24 hours, usually ~30 minutes)

### 4.3 Cloudflare SSL Settings

Go to **SSL/TLS** in the Cloudflare dashboard:

1. **SSL mode** → set to **Flexible**
   (Cloudflare handles all SSL; your server only speaks HTTP internally)
2. **Edge Certificates → Always Use HTTPS** → **ON**
3. **Edge Certificates → Automatic HTTPS Rewrites** → **ON**

### 4.4 Redirect Bare Domain to www

Go to **Rules → Redirect Rules** → Create rule:

- **Rule name:** `Bare domain to www`
- **When:** Hostname equals `reelfilter.com`
- **Then:** Dynamic redirect to `concat("https://www.reelfilter.com", http.request.uri.path)`
- **Status code:** 301
- **Preserve query string:** ON

---

## Part 5: Cloudflare Tunnel

This is the key piece — `cloudflared` creates an encrypted outbound tunnel
from your VM to Cloudflare. No ports to open, no firewall rules, no SSL certs
to manage on your server.

### 5.1 Install cloudflared

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
sudo mv cloudflared /usr/local/bin/
sudo chmod +x /usr/local/bin/cloudflared
cloudflared --version
```

### 5.2 Authenticate

```bash
cloudflared tunnel login
```

This prints a URL. Open it in your browser, select `reelfilter.com`, and
authorize. A certificate file is saved to `~/.cloudflared/`.

### 5.3 Create the Tunnel

```bash
cloudflared tunnel create reel-filter
```

Note the **Tunnel ID** printed (a UUID like `a1b2c3d4-...`). You'll need it
next.

### 5.4 Configure Routing

```bash
nano ~/.cloudflared/config.yml
```

Paste this (replace `<TUNNEL_ID>` with your actual tunnel ID):

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/ubuntu/.cloudflared/<TUNNEL_ID>.json

ingress:
  # API requests → backend on port 8000
  - hostname: www.reelfilter.com
    path: /api/*
    service: http://localhost:8000

  # Swagger docs → backend
  - hostname: www.reelfilter.com
    path: /docs*
    service: http://localhost:8000

  - hostname: www.reelfilter.com
    path: /redoc*
    service: http://localhost:8000

  - hostname: www.reelfilter.com
    path: /openapi.json
    service: http://localhost:8000

  # Everything else → frontend on port 3000
  - hostname: www.reelfilter.com
    service: http://localhost:3000

  # Catch-all (required by cloudflared)
  - service: http_status:404
```

### 5.5 Add DNS Routes

```bash
cloudflared tunnel route dns reel-filter www.reelfilter.com
```

This creates a CNAME record in Cloudflare DNS pointing `www.reelfilter.com`
to your tunnel. You should see it appear in the Cloudflare DNS dashboard.

> **Note:** If you already created A records in Part 4, delete them now.
> The tunnel CNAME replaces them.

### 5.6 Test the Tunnel Manually

```bash
cloudflared tunnel run reel-filter
```

This runs in the foreground. Open `https://www.reelfilter.com` in your
browser — you should see the app. Press Ctrl+C to stop when confirmed.

### 5.7 Install as System Service

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Verify it's running:
```bash
sudo systemctl status cloudflared
```

The tunnel now starts automatically on boot and restarts if it crashes.

### 5.8 Verify All Four URL Combos

From your local machine:

```bash
curl -I http://reelfilter.com          # → 301 to https://www.reelfilter.com
curl -I https://reelfilter.com         # → 301 to https://www.reelfilter.com
curl -I http://www.reelfilter.com      # → 301 to https://www.reelfilter.com
curl -I https://www.reelfilter.com     # → 200 OK
curl https://www.reelfilter.com/api/health  # → {"status":"healthy"}
```

---

## Part 6: Populate the Database

### 6.1 Seed Sample Data (Quick Test)

```bash
cd ~/reel-filter
docker compose exec backend python scripts/manual_refresh.py --seed
```

Inserts 10 test movies so you can verify the UI works. No network needed.

### 6.2 Scrape Kids-in-Mind Content Scores

```bash
docker compose exec backend python scripts/manual_refresh.py --kim
```

- Crawls 26 A-Z index pages from kids-in-mind.com
- Scores are embedded in the index page text (no detail pages needed)
- Respects 60-second crawl delay (takes ~26 minutes)
- Creates stub movie records with content scores (~5,000 movies)
- Idempotent — safe to re-run, updates existing scores

### 6.3 Enrich Movies with OMDb Metadata

```bash
docker compose exec backend python scripts/manual_refresh.py --omdb
```

- Looks up each KIM movie in OMDb by title+year to get full metadata
  (ratings, cast, plot, poster, awards)
- **Quota-aware:** automatically stops when OMDb returns a rate limit error
- **Resumable:** skips already-enriched movies, picks up where it left off
- **Free tier (1,000/day):** run once per day for ~5 days
- **Paid tier ($1/mo, 100K/day):** completes in one run

To limit requests per run (e.g., stay safely under the free daily quota):
```bash
docker compose exec backend python scripts/manual_refresh.py --omdb --limit 900
```

Progress is logged every 50 movies. Example output:
```
Found 5000 movies needing OMDb data. Processing 900 this run.
  Progress: 50/900 fetched, 48 matched, 2 not found, ~4950 remaining total
  Progress: 100/900 fetched, 96 matched, 4 not found, ~4900 remaining total
  ...
OMDb enrichment summary:
  Fetched:    900
  Matched:    871
  Not found:  29
  Remaining:  4100
  Run again with --omdb to process more.
```

### 6.4 Check Match Quality

```bash
docker compose exec backend python -c "
from src.database.session import SessionLocal
from src.models.movie import Movie
from src.models.content_score import ContentScore
db = SessionLocal()
total = db.query(ContentScore).count()
matched = db.query(ContentScore).filter(ContentScore.match_confidence >= 88).count()
review = db.query(ContentScore).filter(ContentScore.match_confidence.between(75, 88)).count()
print(f'Total: {total}, Auto-matched: {matched}, Needs review: {review}')
db.close()
"
```

### 6.5 Review Fuzzy Matches (75-88% Confidence)

```bash
docker compose exec backend python -c "
from src.database.session import SessionLocal
from src.models.movie import Movie
from src.models.content_score import ContentScore
db = SessionLocal()
rows = db.query(Movie.title, Movie.year, ContentScore.match_confidence) \
    .join(ContentScore) \
    .filter(ContentScore.match_confidence.between(75, 88)) \
    .filter(ContentScore.manually_reviewed == False) \
    .all()
for title, year, conf in rows:
    print(f'{conf:.1f}%  {title} ({year})')
db.close()
"
```

To approve a match:
```bash
docker compose exec db psql -U reel_filter_user -d reel_filter \
  -c "UPDATE content_scores SET manually_reviewed = TRUE WHERE id = '<score-id>';"
```

---

## Part 7: Ongoing Operations

### 7.1 Weekly Auto-Refresh

Celery beat is already configured to run weekly refreshes:
- **Sunday 2:00 AM** — OMDb metadata refresh
- **Sunday 3:00 AM** — Kids-in-Mind score refresh

Verify the scheduler is running:
```bash
docker compose logs celery_beat --tail 10
```

### 7.2 View Logs

```bash
# All services
docker compose logs -f --tail 50

# Specific service
docker compose logs backend --tail 50
docker compose logs celery_worker --tail 20
```

### 7.3 Update the App

```bash
cd ~/reel-filter
git pull
docker compose up -d --build
```

### 7.4 Database Backup

```bash
# Backup
docker compose exec db pg_dump -U reel_filter_user reel_filter > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260217.sql | docker compose exec -T db psql -U reel_filter_user reel_filter
```

### 7.5 Monitor Disk Space

```bash
# Docker can eat disk space with old images
docker system prune -f
```

---

## Troubleshooting

### App not loading?
```bash
docker compose ps                        # Are all containers up?
docker compose logs backend --tail 30    # Backend errors?
curl http://localhost:8000/api/health    # Backend responding?
curl http://localhost:3000               # Frontend responding?
sudo systemctl status cloudflared        # Tunnel running?
```

### 502 Bad Gateway from Cloudflare?
The tunnel is up but the app isn't responding:
```bash
docker compose restart backend
docker compose logs backend --tail 30
```

### Tunnel not connecting?
```bash
sudo systemctl restart cloudflared
journalctl -u cloudflared --tail 30
```

### Cloudflare showing old content?
Purge cache: Cloudflare dashboard → **Caching → Configuration → Purge Everything**
