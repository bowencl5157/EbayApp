# eBay Product Research Tool

A FastAPI + Tailwind CSS application for eBay product research, pricing analysis, and trending item discovery.

## Features

- **Product Search**: Search for products on eBay with various sorting options
- **Trending Items**: Discover best-selling and trending products
- **Pricing Analysis**: Analyze pricing data for product categories with statistics

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Open your browser to `http://localhost:8000`

## Current Status

The application is configured to use **real eBay Browse API data only**. There is no demo mode and no fake fallback data.

The Browse API search endpoint used by the app is:

```text
GET https://api.ebay.com/buy/browse/v1/item_summary/search
```

The app requires one of these authentication options in `.env`:

```env
EBAY_ACCESS_TOKEN=your_oauth_access_token
```

or:

```env
EBAY_CLIENT_ID=your_client_id
EBAY_CLIENT_SECRET=your_client_secret
```

If neither is present, API endpoints intentionally fail with a clear error. The old `appToken.txt` value is not treated as valid Browse API OAuth credentials.

## API Endpoints

- `GET /` - Frontend interface
- `GET /api/search` - Search for products using the Browse API
- `GET /api/trending` - Search for trending-style products using the Browse API
- `GET /api/item/{item_id}` - Get item details
- `GET /api/pricing/{query}` - Get pricing analysis

## eBay API Integration

The application uses:
- **Browse API** - `GET /buy/browse/v1/item_summary/search`
- **Browse API** - `GET /buy/browse/v1/item/{item_id}`
