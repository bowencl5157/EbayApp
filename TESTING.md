# Testing Plan for eBay App

## Overview

This document outlines the comprehensive testing strategy for the eBay Product Research Tool. The testing plan uses pytest as the testing framework and includes unit tests, integration tests, and database tests.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_api_browse.py       # Browse API client tests
├── test_api_finding.py      # Finding API client tests
├── test_services.py         # Service layer tests
├── test_api_endpoints.py    # API endpoint integration tests
├── test_models.py           # Database model tests
└── test_utils.py           # Utility tests (cache, rate limiter)
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Markers**: `@pytest.mark.unit`
- **Files**: `test_api_browse.py`, `test_api_finding.py`, `test_utils.py`
- **Coverage**: API clients, utilities, helper functions

### Integration Tests
- **Purpose**: Test interactions between components
- **Markers**: `@pytest.mark.integration`
- **Files**: `test_api_endpoints.py`, `test_services.py`
- **Coverage**: API endpoints, service layer

### Database Tests
- **Purpose**: Test database models and queries
- **Markers**: `@pytest.mark.database`
- **Files**: `test_models.py`
- **Coverage**: SQLAlchemy models, database operations

### API Tests
- **Purpose**: Test API endpoints
- **Markers**: `@pytest.mark.api`
- **Files**: `test_api_endpoints.py`
- **Coverage**: FastAPI endpoints including:
  - Original endpoints: Search, Trending, Pricing, SEO Keywords
  - New service endpoints: Product Research, Price Monitoring, Seller Analytics, Marketplace Research, Repricing
  - Additional endpoints: Inventory Tracking, Trending Products, Market Competition, Auto-Reprice, Apply Repricing Rules

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
python run_tests.py
```

### Run Specific Test Categories

```bash
# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run only API tests
python run_tests.py --api

# Run only database tests
python run_tests.py --database
```

### Run Tests with Coverage

```bash
python run_tests.py --coverage
```

This generates:
- HTML coverage report: `htmlcov/index.html`
- Terminal coverage summary
- XML coverage report: `coverage.xml`

### Run Tests Directly with Pytest

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api_browse.py -v

# Run specific test class
pytest tests/test_api_browse.py::TestBrowseAPIClient -v

# Run specific test
pytest tests/test_api_browse.py::TestBrowseAPIClient::test_init -v

# Run tests by marker
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m database -v
```

## Test Fixtures

### Database Fixture
```python
@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory SQLite database for each test"""
```

### Test Client Fixture
```python
@pytest.fixture(scope="function")
def client(db_session):
    """Creates a FastAPI test client with database dependency override"""
```

### Mock API Client Fixtures
```python
@pytest.fixture
def mock_browse_client():
    """Mock Browse API client"""
    
@pytest.fixture
def mock_finding_client():
    """Mock Finding API client"""
```

### Sample Data Fixtures
```python
@pytest.fixture
def sample_item_data():
    """Sample item data for testing"""
    
@pytest.fixture
def sample_search_response():
    """Sample search API response"""
```

## Test Coverage

### API Clients
- Browse API client: Initialization, token management, search, trending, item details
- Finding API client: Completed items, category search, advanced search
- Trading API client: Seller operations, inventory management
- Inventory API client: Inventory items, offers, locations
- Account API client: Account status, policies, rate limits

### Services
- Product Research: Multi-API research, price history analysis, comprehensive product analysis
- Price Monitoring: Price tracking, trend analysis, competitor monitoring, historical price data
- Seller Analytics: Dashboard, inventory tracking, performance trends, seller metrics
- Marketplace Research: Category research, trending products, competition analysis, market insights
- Repricing: Competitor analysis, auto-repricing, rule application, price optimization

### Database Models
- ProductSearch, ItemDetails, PriceHistory
- KeywordAnalysis, TrendingItem
- SellerPerformance, MarketTrend
- CompetitorPrice, InventorySnapshot, APIUsage

### Utilities
- Cache Manager: Redis caching, fallback cache, TTL management
- Rate Limiter: API rate limiting, request tracking, limit enforcement

### API Endpoints
- Original Endpoints: Search, Trending, Item Details, Pricing Analysis, SEO Keywords
- New Service Endpoints:
  - Product Research: `/api/product-research`
  - Price Monitoring: `/api/price-monitoring`, `/api/competitor-prices`
  - Seller Analytics: `/api/seller-analytics`, `/api/inventory-tracking`
  - Marketplace Research: `/api/marketplace-research`, `/api/trending-products`, `/api/market-competition`
  - Repricing: `/api/repricing-analysis`, `/api/auto-reprice`, `/api/apply-repricing-rules`

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python run_tests.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

1. **Isolation**: Each test should be independent and not depend on other tests
2. **Mocking**: Use mocks for external API calls to avoid hitting rate limits
3. **Fixtures**: Use fixtures for common setup/teardown logic
4. **Markers**: Use pytest markers to categorize tests
5. **Async Tests**: Use `@pytest.mark.asyncio` for async test functions
6. **Database**: Use in-memory SQLite for fast, isolated database tests
7. **Coverage**: Aim for >80% code coverage
8. **Naming**: Use descriptive test names that explain what is being tested

## Troubleshooting

### Tests Fail Due to Missing Dependencies
```bash
pip install -r requirements.txt
```

### Tests Fail Due to Database Issues
The tests use in-memory SQLite, so no database setup is required. If you see database errors, ensure the test fixtures are working correctly.

### Async Tests Fail
Ensure `pytest-asyncio` is installed and configured correctly in `pytest.ini`.

### Tests Timeout
Increase timeout values in `pytest.ini` if needed:
```ini
[pytest]
timeout = 300
```

## Adding New Tests

1. Create a new test file in `tests/` directory
2. Import necessary fixtures from `conftest.py`
3. Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
4. Write test functions following the pattern: `test_<component>_<action>`
5. Run the tests to verify they pass
6. Update this documentation if needed

## Test Metrics

Track the following metrics:
- Total number of tests
- Test pass rate
- Code coverage percentage
- Test execution time
- Number of flaky tests

## Maintenance

- Review and update tests when code changes
- Remove obsolete tests
- Add tests for new features
- Update fixtures as needed
- Keep test data up to date
