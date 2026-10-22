# TravelIntel AI

**Automated eSIM Data Engineering & Recommendation Platform**

TravelIntel AI is a Python-based platform that automates the ingestion, validation, storage, and recommendation of travel eSIM offers.

Built as a portfolio project, it demonstrates **data engineering, backend development, workflow automation, and containerization** using FastAPI, PostgreSQL, n8n, and Docker.

## Key Features

- **Data ingestion:** Process supplier offers from CSV files and JSON APIs.
- **Data validation:** Validate prices, data allowances, validity periods, and required fields.
- **PostgreSQL storage:** Persist validated offers with upsert operations.
- **REST API:** Retrieve, filter, and import offers using FastAPI.
- **Recommendation engine:** Match offers to destination, budget, data needs, and trip duration using business rules.
- **Workflow automation:** Schedule supplier imports with n8n.
- **Error monitoring:** Record workflow failures in PostgreSQL.
- **Automated testing:** 37 passing tests using pytest.
- **Docker:** Run the FastAPI backend in a container using Docker Compose.

## Tech Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Backend | FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy |
| Automation | n8n |
| Containerization | Docker, Docker Compose |
| Testing | pytest |
| Version Control | Git, GitHub |

## Architecture

```text
Supplier CSV / JSON
         |
         v
  n8n Automation
         |
         v
 FastAPI Ingestion
         |
         v
 Validation Pipeline
         |
         v
    PostgreSQL
         |
         v
 Recommendation API
```

n8n also provides automated error monitoring with PostgreSQL logging. Local CSV ingestion is supported independently of n8n.

## Getting Started

### Requirements

- Python 3.13
- PostgreSQL
- Docker Desktop (for containerized execution)
- n8n (for workflow automation)

### 1. Clone the repository

```bash
git clone  https://github.com/FendiFiras/TravelIntel-AI.git
cd TravelIntel-AI
```

### 2. Configure environment variables

Create a `.env` file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=travelintel
DB_USER=your_username
DB_PASSWORD=your_password
API_KEY=your_private_api_key
```

An existing PostgreSQL database with the required tables is needed. The `.env` file must not be committed to Git.

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the API

Locally:

```bash
python -m uvicorn src.api:app --reload
```

Or with Docker:

```bash
docker compose up -d --build
```

Swagger UI:

- Local: http://localhost:8000/docs
- Docker: http://localhost:8001/docs

The current Docker configuration connects to PostgreSQL running on the host machine.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/offers` | Retrieve offers |
| GET | `/offers/{offer_id}` | Get an offer by ID |
| GET | `/offers/recommend` | Recommend matching offers |
| POST | `/offers/import` | Import JSON offers |
| POST | `/imports/supplier` | Import supplier CSV |

Import endpoints require an `x-api-key` header.

**Recommendation example:**

```http
GET /offers/recommend?country=Japan&min_data_gb=10&trip_days=10&max_budget=25
```

The recommendation engine is currently rule-based, not a trained machine learning model.

## Testing

Run the automated test suite:

```bash
python -m pytest -v
```

**Latest verified result: 37 tests passed.**

## Future Improvements

- Additional supplier integrations
- AI-assisted offer analysis
- CI/CD and cloud deployment
- Frontend dashboard and advanced monitoring

## Author

**Firas Abidhiaf**

Software Engineering | Data Engineering for AI

*Sample supplier data is fictional and used for development and testing.*