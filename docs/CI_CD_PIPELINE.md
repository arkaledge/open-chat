# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and testing. The pipeline automatically runs on every push and pull request to ensure code quality and functionality.

## Pipeline Configuration

The main testing pipeline is defined in `.github/workflows/test.yml`.

## Pipeline Jobs

### 1. Backend Tests (`backend-tests`)

Tests the Python/FastAPI backend with the following steps:

**Services:**
- PostgreSQL 15 (for database tests)
- Redis 7 (for caching tests)

**Steps:**
1. **Linting**: Checks code formatting with `black` and import sorting with `isort`
2. **Type Checking**: Runs `mypy` for static type analysis
3. **Unit Tests**: Executes pytest with coverage reporting

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Test secret key
- `ENVIRONMENT`: Set to `test`

### 2. Frontend Tests (`frontend-tests`)

Tests the Next.js/TypeScript frontend:

**Steps:**
1. **Linting**: Runs ESLint checks
2. **Type Checking**: Validates TypeScript types
3. **Build**: Ensures the application builds successfully

### 3. Docker Build (`docker-build`)

Validates that Docker images can be built:

**Steps:**
1. Builds backend Docker image
2. Builds frontend Docker image
3. Uses GitHub Actions cache for faster builds

### 4. Status Check (`status-check`)

Final job that ensures all tests passed before marking the pipeline as successful.

## Running Tests Locally

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run linting
black --check app/
isort --check-only app/

# Run type checking
mypy app/

# Run tests
pytest tests/ -v --cov=app
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run linting
npm run lint

# Run type checking
npm run type-check

# Build
npm run build
```

### Docker

```bash
# Build backend
docker build -t openchat-backend ./backend

# Build frontend
docker build -t openchat-frontend ./frontend

# Or use docker-compose
docker-compose build
```

## Adding Tests

### Backend Tests

Add test files in `backend/tests/` following the pattern `test_*.py`:

```python
import pytest

def test_example():
    assert True

@pytest.mark.asyncio
async def test_async_example():
    # Your async test here
    pass
```

### Frontend Tests

Currently, the pipeline focuses on linting, type-checking, and build verification. To add unit tests:

1. Install a testing framework (e.g., Jest, Vitest)
2. Add test scripts to `package.json`
3. Update the workflow to run tests

## Pipeline Triggers

The pipeline runs on:
- **All branches**: Every push to any branch
- **Pull requests**: When PRs are opened or updated

## Caching

The pipeline uses caching to speed up builds:
- **Python**: pip packages cached by `setup-python` action
- **Node.js**: npm packages cached by `setup-node` action
- **Docker**: Build cache using GitHub Actions cache

## Troubleshooting

### Pipeline Failing on Linting

Run the formatters locally:
```bash
# Backend
cd backend
black app/
isort app/

# Frontend
cd frontend
npm run lint -- --fix
```

### Pipeline Failing on Type Checks

Fix type errors locally:
```bash
# Backend
cd backend
mypy app/

# Frontend
cd frontend
npm run type-check
```

### Docker Build Failures

Test Docker builds locally:
```bash
docker-compose build
```

## Future Enhancements

Potential improvements to the pipeline:

- [ ] Add frontend unit tests with Jest/Vitest
- [ ] Add E2E tests with Playwright/Cypress
- [ ] Add security scanning (Snyk, Trivy)
- [ ] Add deployment steps for staging/production
- [ ] Add performance testing
- [ ] Add code coverage requirements
- [ ] Add automatic dependency updates (Dependabot)
