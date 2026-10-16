
# TravelIntel AI

An AI automation and data engineering portfolio project for
processing and validating travel eSIM offers.

## Current features

- Import supplier offers from CSV files
- Validate required fields and numeric values
- Detect duplicate commercial offers
- Export valid records and rejected records with error messages

## Requirements

- Python 3.11 or newer

## Run locally

```bash
python src/pipeline.py
```

## Project structure

- `data/`: sample supplier data
- `src/`: data processing code
- `tests/`: automated tests
- `output/`: generated pipeline results

## Data

The included supplier data is fictional and intended for development
and testing only.

## Roadmap

- Automated tests
- PostgreSQL integration
- FastAPI backend
- n8n automation workflows
- AI-assisted SEO content generation
- React dashboard
- Docker and CI/CD
