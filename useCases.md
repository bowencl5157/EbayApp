# eBay API Capabilities and Use Cases

This document provides a comprehensive list of what is possible to extract with the eBay API, organized by API category and use cases.

---

## Table of Contents

1. [Browse API (Buy APIs)](#browse-api-buy-apis)
2. [Trading API (Sell APIs)](#trading-api-sell-apis)
3. [Inventory API (Sell APIs)](#inventory-api-sell-apis)
4. [Finding API (Legacy)](#finding-api-legacy)
5. [Shopping API (Legacy)](#shopping-api-legacy)
6. [Marketplace Insights API](#marketplace-insights-api)
7. [Account API](#account-api)
8. [Feed API](#feed-api)

---

## Browse API (Buy APIs)

The Browse API is designed for browsing and searching eBay listings. It's part of the Buy APIs and is primarily used by buyers and researchers.

### Available Resources

#### Item Summary

**Endpoint:** `GET /buy/browse/v1/item_summary/search`

**What you can extract:**
- Search for items by keyword, GTIN, category, charity, product, compatible products, or item aspects
- Filter results by price, condition, shipping, seller feedback, item location
- Get item summaries including: title, price, image URL, item web URL, seller information
- Sort results by price (ascending/descending), best match, distance
- Get aspect histograms for filtering (e.g., brand, color, size)
- Retrieve watch count (requires special permission)
- Get item group information for items with variations

**Use Cases:**
- Product research and market analysis
- Price comparison across listings
- SEO keyword extraction from titles
- Finding best-selling items in a category
- Analyzing seller performance and feedback
- Identifying trending products
- Building product recommendation engines
- Creating price monitoring tools
- Market research for e-commerce

#### Item Details

**Endpoint:** `GET /buy/browse/v1/item/{item_id}`

**What you can extract:**
- Full item details including description, specifications
- All available images for the item
- Item condition and warranty information
- Shipping options and costs
- Return policy details
- Seller information and feedback score
- Item location and handling time
- Quantity available
- Item attributes and aspects
- Compatibility information (for parts/accessories)
- Legacy item ID conversion

**Use Cases:**
- Detailed product analysis
- Product comparison tools
- Building product detail pages
- Inventory management integration
- Price monitoring for specific items
- Analyzing product descriptions for SEO

#### Search by Image

**Endpoint:** `POST /buy/browse/v1/search_by_image`

**What you can extract:**
- Find items that match or are similar to an uploaded image
- Get visually similar products
- Find exact product matches using image recognition

**Use Cases:**
- Visual product search
- Reverse image lookup
- Finding alternatives to a product
- Price comparison using product images
- Catalog management for sellers

#### Item Compatibility

**Endpoint:** `GET /buy/browse/v1/item/{item_id}/compatible_products`

**What you can extract:**
- Find products compatible with a specific item (e.g., car parts for a specific vehicle)
- Get compatibility information for accessories and parts
- Retrieve fitment data

**Use Cases:**
- Automotive parts lookup
- Electronics accessory compatibility
- Building parts databases
- Fitment verification tools

---

## Trading API (Sell APIs)

The Trading API is for sellers to manage their eBay business operations.

### Available Capabilities

**What you can extract:**
- Get seller's active listings
- Retrieve sold item history
- Get item details and descriptions
- Access seller's feedback profile
- Get account information and status
- Retrieve transaction history
- Get order details and buyer information
- Access shipping tracking information
- Get fee information and invoice data
- Retrieve dispute and case information
- Get best offer details

**Use Cases:**
- Seller dashboard and analytics
- Inventory management
- Order processing automation
- Fee calculation and reporting
- Performance tracking
- Dispute management
- Financial reporting
- Multi-channel integration
- Repricing tools
- Listing optimization

---

## Inventory API (Sell APIs)

The Inventory API helps sellers manage their inventory across eBay and other marketplaces.

### Available Resources

#### Inventory Location

**Endpoint:** Various endpoints for inventory locations

**What you can extract:**
- Get all inventory locations (warehouses, stores)
- Retrieve location-specific inventory levels
- Get location details and addresses
- Access merchant location keys

**Use Cases:**
- Multi-warehouse management
- Location-based inventory tracking
- Fulfillment optimization
- Shipping cost calculation

#### Inventory Item

**Endpoint:** Various endpoints for inventory items

**What you can extract:**
- Get all inventory items
- Retrieve item details and SKUs
- Get product descriptions and attributes
- Access item images and EAN/UPC/GTIN data
- Retrieve pricing information
- Get quantity and availability data
- Access product taxonomy and category information

**Use Cases:**
- Catalog management
- Product information management
- Multi-channel synchronization
- Bulk inventory updates
- Product enrichment

#### Offer

**Endpoint:** Various endpoints for offers

**What you can extract:**
- Get all offers (published listings)
- Retrieve offer details and pricing
- Get offer status and availability
- Access offer-specific inventory levels
- Retrieve promotion and discount information
- Get MAP (Minimum Advertised Price) data

**Use Cases:**
- Listing management
- Price monitoring
- Offer optimization
- Promotion tracking
- Multi-marketplace listing

---

## Finding API (Legacy)

The Finding API is for searching and finding items on eBay. It's being replaced by the Browse API but still has some unique capabilities.

### Available Capabilities

**What you can extract:**
- Search for items by keyword, category, product
- Get popular items and trending searches
- Find items by specific attributes (e.g., color, size)
- Retrieve category information and hierarchy
- Get seller information and feedback
- Search for items by seller
- Find items by location
- Get completed item listings (sold items)
- Retrieve item specifics and aspects
- Get eBay store inventory

**Use Cases:**
- Market research
- Price analysis
- Trending product identification
- Category analysis
- Seller research
- Completed item analysis (for pricing research)
- Store inventory monitoring

---

## Shopping API (Legacy)

The Shopping API provides detailed information about items, sellers, and user profiles.

### Available Capabilities

**What you can extract:**
- Get detailed item information
- Retrieve seller profiles and feedback
- Get user profile information
- Find items by category
- Retrieve product details and reviews
- Get shipping cost estimates
- Access item recommendations
- Get multiple item details in batch
- Retrieve user information

**Use Cases:**
- Product research
- Seller vetting
- User profile analysis
- Product recommendation
- Shipping cost calculation
- Feedback analysis
- Trust and reputation building

---

## Marketplace Insights API

The Marketplace Insights API provides aggregated market data and trends.

### Available Capabilities

**What you can extract:**
- Market trend data
- Category performance metrics
- Price distribution analysis
- Seller performance benchmarks
- Buyer behavior insights
- Marketplace health indicators
- Competitive intelligence data
- Seasonal trends

**Use Cases:**
- Market research
- Competitive analysis
- Pricing strategy
- Category selection for sellers
- Trend prediction
- Business intelligence
- Strategic planning

---

## Account API

The Account API provides seller account information and settings.

### Available Capabilities

**What you can extract:**
- Account status and verification
- Seller performance metrics
- Feedback profile and scores
- Account privileges and limits
- Subscription information
- Payment method details
- Shipping address information
- Tax settings

**Use Cases:**
- Account management
- Performance monitoring
- Compliance tracking
- Limit management
- Payment reconciliation

---

## Feed API

The Feed API provides bulk access to eBay data through file-based feeds.

### Available Capabilities

**What you can extract:**
- Daily inventory feeds
- Order fulfillment feeds
- Active listing feeds
- Sold item feeds
- Pricing and promotion feeds
- Bulk item data exports

**Use Cases:**
- Bulk data processing
- Data warehousing
- Business intelligence
- Large-scale analytics
- Backup and archival
- Third-party integrations

---

## Data Fields Commonly Available

### Product Data
- Title and subtitle
- Item description (HTML)
- Item condition
- Brand and manufacturer
- Product identifiers (UPC, EAN, ISBN, GTIN)
- Product specifications and attributes
- Images (multiple URLs)
- Category and subcategory
- Item specifics and aspects

### Pricing Data
- Current price
- Original price (for discounted items)
- Price history (via completed items)
- Shipping costs
- Tax information
- Currency
- Discount percentages
- Best offer acceptance price

### Seller Data
- Seller username
- Seller feedback score
- Seller feedback percentage
- Seller ratings (item description, communication, shipping time)
- Seller location
- Seller store information
- Seller business type (individual/business)

### Listing Data
- Listing start time
- Listing end time
- Listing type (auction, fixed price)
- Quantity available
- Quantity sold
- View count
- Watch count (with permission)
- Bid count (for auctions)
- Current bid (for auctions)
- Buy It Now price (for auctions)

### Shipping Data
- Shipping methods available
- Shipping costs
- Shipping locations (domestic/international)
- Handling time
- Free shipping eligibility
- Expedited shipping options
- Shipping carrier information

### Buyer Data (with proper permissions)
- Buyer feedback
- Purchase history (own account only)
- Watch list (own account only)
- Saved searches (own account only)

---

## Authentication Requirements

### Application Access Token
- Used for public data access (Browse API, Finding API)
- OAuth 2.0 client credentials flow
- No user consent required
- Limited to public information

### User Access Token
- Used for user-specific data (Trading API, Account API)
- OAuth 2.0 authorization code flow
- Requires user consent
- Access to private account data

---

## Rate Limits and Quotas

- Browse API: ~5,000 calls per day for production
- Finding API: ~5,000 calls per day
- Trading API: Varies by application tier
- Inventory API: Varies by application tier
- Marketplace Insights API: Limited access, requires approval

---

## Common Use Case Combinations

### Product Research Tool
- Browse API search for products
- Browse API item details for specifications
- Finding API for completed items (price history)
- Marketplace Insights for trend data

### Price Monitoring Tool
- Browse API for current prices
- Finding API for historical pricing
- Inventory API for seller inventory
- Trading API for seller performance

### SEO Keyword Analysis
- Browse API search for category items
- Extract titles and descriptions
- Analyze keyword frequency
- Identify long-tail keywords

### Seller Analytics Dashboard
- Trading API for active listings
- Trading API for sold items
- Account API for performance metrics
- Inventory API for inventory levels

### Marketplace Research
- Browse API for category browsing
- Marketplace Insights for market trends
- Finding API for popular items
- Shopping API for seller profiles

### Repricing Tool
- Browse API for competitor prices
- Inventory API for own inventory
- Trading API for listing updates
- Account API for performance metrics

---

## Integration Examples

### E-commerce Platform Integration
- Inventory API for product sync
- Trading API for order management
- Account API for seller dashboard
- Feed API for bulk operations

### Price Comparison Website
- Browse API for product search
- Browse API for price data
- Finding API for historical prices
- Marketplace Insights for trend data

### Dropshipping Platform
- Browse API for product sourcing
- Inventory API for inventory management
- Trading API for listing automation
- Account API for performance tracking

### Market Research Tool
- Browse API for market scanning
- Marketplace Insights for trend analysis
- Finding API for completed item data
- Shopping API for seller analysis

---

## Notes and Limitations

1. **Production Access**: Some APIs require special approval for production use
2. **Data Restrictions**: Some fields (like watch count) require additional permissions
3. **Rate Limits**: All APIs have rate limits that must be respected
4. **Legacy APIs**: Finding and Shopping APIs are legacy and may be deprecated
5. **Geographic Restrictions**: Some features are marketplace-specific
6. **Data Freshness**: Real-time data may have slight delays
7. **User Privacy**: Buyer data is heavily restricted
8. **Commercial Use**: Commercial use may require additional agreements

---

## Getting Started

1. **Create eBay Developer Account**: Register at developer.ebay.com
2. **Generate API Keys**: Create application keys in the Developer Portal
3. **Choose Your API**: Select the appropriate API for your use case
4. **Get Authentication**: Set up OAuth tokens
5. **Test in Sandbox**: Use the eBay Sandbox environment for testing
6. **Apply for Production**: Request production access when ready
7. **Monitor Usage**: Track API usage and stay within limits

---

## Resources

- eBay Developer Portal: https://developer.ebay.com
- API Documentation: https://developer.ebay.com/api-docs
- API Explorer: Test API calls interactively
- Sandbox Environment: https://developer.ebay.com/sandbox
- Community Forums: https://developer.ebay.com/forums
