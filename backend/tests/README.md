# Backend Tests

## Running Tests

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_cart.py
pytest tests/test_recommendations.py
pytest tests/test_products_filtering.py
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Files

- `test_cart.py` - Tests for cart functionality including save for later
- `test_recommendations.py` - Tests for recommendation algorithm
- `test_products_filtering.py` - Tests for product filtering and sorting

## Notes

- Tests use async/await for FastAPI endpoints
- Test data is stored in separate test data directory
- Tests clean up after themselves
