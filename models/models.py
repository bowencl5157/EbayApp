from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class ProductSearch(Base):
    """Cache for product search results"""
    __tablename__ = "product_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    category_id = Column(String, nullable=True, index=True)
    results = Column(JSON)
    result_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)


class ItemDetails(Base):
    """Cache for item details"""
    __tablename__ = "item_details"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, unique=True, index=True)
    title = Column(String)
    price = Column(Float)
    condition = Column(String)
    seller_username = Column(String)
    seller_feedback_score = Column(Integer)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PriceHistory(Base):
    """Historical pricing data for items"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, index=True)
    title = Column(String)
    price = Column(Float)
    currency = Column(String, default="USD")
    condition = Column(String)
    seller_username = Column(String)
    listing_type = Column(String)  # auction, fixed_price
    is_completed = Column(Boolean, default=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_price_history_item_date', 'item_id', 'recorded_at'),
    )


class KeywordAnalysis(Base):
    """SEO keyword analysis results"""
    __tablename__ = "keyword_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    category_id = Column(String, nullable=True, index=True)
    short_tail_keywords = Column(JSON)
    long_tail_keywords = Column(JSON)
    total_listings_analyzed = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TrendingItem(Base):
    """Trending items tracking"""
    __tablename__ = "trending_items"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, unique=True, index=True)
    title = Column(String)
    price = Column(Float)
    category_id = Column(String, index=True)
    trend_score = Column(Float, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class SellerPerformance(Base):
    """Seller performance metrics over time"""
    __tablename__ = "seller_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_username = Column(String, index=True)
    feedback_score = Column(Integer)
    feedback_percentage = Column(Float)
    positive_feedback_count = Column(Integer)
    neutral_feedback_count = Column(Integer)
    negative_feedback_count = Column(Integer)
    active_listings_count = Column(Integer, nullable=True)
    total_listings_count = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_seller_performance_username_date', 'seller_username', 'recorded_at'),
    )


class MarketTrend(Base):
    """Market trend data from Marketplace Insights API"""
    __tablename__ = "market_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(String, index=True)
    category_name = Column(String)
    trend_data = Column(JSON)
    price_distribution = Column(JSON)
    seller_performance_benchmarks = Column(JSON)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class CompetitorPrice(Base):
    """Competitor pricing for repricing tool"""
    __tablename__ = "competitor_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, index=True)
    competitor_item_id = Column(String, index=True)
    competitor_seller = Column(String, index=True)
    competitor_price = Column(Float)
    our_price = Column(Float, nullable=True)
    price_difference = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_competitor_price_item_date', 'item_id', 'recorded_at'),
    )


class InventorySnapshot(Base):
    """Inventory snapshots for sellers"""
    __tablename__ = "inventory_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_username = Column(String, index=True)
    sku = Column(String, index=True)
    title = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    location = Column(String, nullable=True)
    snapshot_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_inventory_snapshot_seller_date', 'seller_username', 'snapshot_date'),
    )


class APIUsage(Base):
    """Track API usage for rate limiting"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String, index=True)
    endpoint = Column(String, index=True)
    call_count = Column(Integer, default=1)
    last_called = Column(DateTime, default=datetime.utcnow)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_api_usage_endpoint_date', 'endpoint', 'date'),
    )
