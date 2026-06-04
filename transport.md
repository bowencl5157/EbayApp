# eBay App Transport Guide

This guide explains how to transport this FastAPI eBay seller analytics app to another computer and set it up using Docker.

## What This App Does

This is a FastAPI web application that:
- Connects to eBay via OAuth for seller account access
- Fetches orders, financial transactions, and seller data from eBay Sell API
- Displays sales data with reconciliation fields (fees, taxes, refunds, net income)
- Exports data to CSV
- Uses PostgreSQL for data persistence and Redis for caching

## Prerequisites on Target Computer

1. Docker Desktop installed and running
2. Git (optional but recommended)
3. eBay Developer account with app credentials
4. Walmart Developer account with API credentials (optional)

## Quick Setup (For LLM/AI Assistant)

**PROMPT FOR LLM:**

```
I need to set up an eBay seller analytics FastAPI app on this computer. 

The project files are located at: [PATH_TO_EXTRACTED_PROJECT]

Here are the required steps:

1. Navigate to the project directory
2. Copy env.example to .env and fill in real credentials:
   - EBAY_CLIENT_ID (from eBay Developer Portal)
   - EBAY_CLIENT_SECRET (from eBay Developer Portal)
   - EBAY_REDIRECT_URI (must match eBay app settings, use https for production)
   - EBAY_MARKETPLACE_ID (e.g., EBAY_US)
   - WALMART_CLIENT_ID (optional, from Walmart Developer Portal)
   - WALMART_CLIENT_SECRET (optional)
   - DB_USER, DB_PASSWORD, DB_NAME (can use defaults for local dev)
   - DATABASE_URL (postgresql://DB_USER:DB_PASSWORD@postgres:5432/DB_NAME)
   - REDIS_URL (redis://redis:6379/0)

3. Start the services:
   docker compose up --build

4. Wait for all services to be healthy (check docker compose logs)

5. Access the app at http://localhost:8000

6. For eBay OAuth to work:
   - Update eBay Developer Portal redirect URI to match your setup
   - If using locally: http://localhost:8000/oauth/callback
   - If using tunnel: https://your-tunnel.trycloudflare.com/oauth/callback
   - The app will show a "Connect eBay Account" button

7. Database tables will be auto-created on first run (check init.sql or app startup)

8. Test the app:
   - Go to http://localhost:8000
   - Click "Connect eBay Account" to authorize
   - Go to "Account" tab and fetch data for a date range
   - Verify CSV download works

If there are database connection errors, verify:
- DATABASE_URL uses "postgres" as hostname (not localhost)
- PostgreSQL service is healthy in docker compose

If eBay OAuth fails:
- Verify EBAY_REDIRECT_URI in .env matches eBay Developer Portal
- Verify the redirect URI is accessible from the internet (use Cloudflare tunnel if needed)
```

## Manual Step-by-Step Setup

### 1. Extract Project Files

Copy the project folder to the new computer:
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `requirements.txt`
- `main.py`
- `api/` folder
- `templates/` folder
- `init.sql` (if exists)
- `env.example`

**DO NOT copy:**
- `.env` file (contains secrets - recreate manually)
- `__pycache__/` folders
- `postgres_data/` folder (database will be fresh)
- Any `.db` or `.sqlite3` files

### 2. Create Environment File

```bash
cp env.example .env
```

Edit `.env` and fill in your real credentials:

```env
# Required: eBay API
EBAY_CLIENT_ID=your_real_ebay_client_id
EBAY_CLIENT_SECRET=your_real_ebay_client_secret
EBAY_REDIRECT_URI=http://localhost:8000/oauth/callback  # or your tunnel URL

# Optional: Walmart API
WALMART_CLIENT_ID=your_walmart_client_id
WALMART_CLIENT_SECRET=your_walmart_client_secret
```

### 3. Start Services

```bash
docker compose up --build
```

This will:
- Build the FastAPI app image
- Start PostgreSQL container
- Start Redis container
- Start the app container
- Connect all services

Wait for health checks to pass:
```bash
docker compose ps
```

### 4. Access the App

Open browser to: http://localhost:8000

### 5. Configure eBay OAuth

1. Go to eBay Developer Portal
2. Find your app
3. Update "Your auth accepted URL" to match EBAY_REDIRECT_URI in your .env
4. Save changes

### 6. Connect eBay Account

In the app:
1. Click "Connect eBay Account"
2. Log in to eBay and authorize
3. You'll be redirected back to the app

### 7. Test Account Data

1. Go to "Account" tab
2. Select date range
3. Click "Get Account Data"
4. Verify data loads correctly
5. Test "Download CSV" button

## Troubleshooting

### Database Connection Errors

**Problem:** `connection refused` or `name resolution failed`

**Solution:**
- In `.env`, use `postgres` (service name) not `localhost`:
  ```
  DATABASE_URL=postgresql://ebayuser:ebaypass@postgres:5432/ebayapp
  ```
- Check PostgreSQL is healthy:
  ```bash
  docker compose logs postgres
  ```

### eBay OAuth Errors

**Problem:** `invalid redirect_uri` or OAuth fails

**Solution:**
- Verify EBAY_REDIRECT_URI in .env exactly matches eBay Developer Portal
- If using locally, must be `http://localhost:8000/oauth/callback`
- If using tunnel, must be `https://your-tunnel.trycloudflare.com/oauth/callback`
- The redirect URI must be accessible from the internet for eBay to call back

### Port Already in Use

**Problem:** `bind: address already in use`

**Solution:**
- Change port in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Use 8001 on host
  ```
- Or stop other services using port 8000

### Missing Dependencies

**Problem:** `ModuleNotFoundError` in app logs

**Solution:**
```bash
docker compose down
docker compose build --no-cache
docker compose up
```

## Moving Database Data (Optional)

If you need to transfer existing database data:

### Export from old computer:

```bash
docker exec ebayapp_postgres pg_dump -U ebayuser ebayapp > backup.sql
```

### Import on new computer:

```bash
# After docker compose up, copy SQL file
docker cp backup.sql ebayapp_postgres:/tmp/
docker exec ebayapp_postgres psql -U ebayuser -d ebayapp -f /tmp/backup.sql
```

## Production Deployment Notes

For production use:

1. Use strong passwords in `.env`
2. Enable HTTPS (use reverse proxy like nginx or traefik)
3. Use Cloudflare tunnel or similar for external access
4. Update EBAY_REDIRECT_URI to production domain
5. Consider using Docker secrets instead of env vars for sensitive data
6. Set up automated database backups

## File Structure After Setup

```
EbayApp/
├── .env                 # Created manually (not in git)
├── .dockerignore        # Excludes .env, cache files
├── docker-compose.yml   # Defines postgres, redis, ebay-app services
├── Dockerfile           # Python 3.11 + FastAPI setup
├── env.example          # Template for .env
├── init.sql             # Database initialization (if exists)
├── main.py              # FastAPI app
├── requirements.txt     # Python dependencies
├── api/                 # API client modules
│   ├── sell.py
│   ├── browse.py
│   └── ...
├── templates/           # HTML templates
│   └── index.html
└── transport.md         # This file
```

## Commands Reference

```bash
# Start all services
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f ebay-app

# Stop all services
docker compose down

# Stop and remove volumes (deletes database!)
docker compose down -v

# Rebuild after code changes
docker compose up --build

# Enter app container for debugging
docker exec -it ebayapp bash

# Enter database container
docker exec -it ebayapp_postgres psql -U ebayuser -d ebayapp
```

## Security Notes

- Never commit `.env` to git
- Use different credentials for dev vs production
- Rotate API keys periodically
- Use HTTPS in production
- Consider OAuth token encryption at rest

## Need Help?

Check the app logs for detailed error messages:
```bash
docker compose logs ebay-app
```

For eBay API issues, check:
- eBay Developer Portal: https://developer.ebay.com/
- API Explorer for testing endpoints

---

**Transport Ready:** Yes  
**Last Updated:** 2024
