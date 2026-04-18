# Product Search API (ML Project)

A FastAPI-powered backend service for searching and listing products from a JSON-based data store. This project serves as a foundation for product-related machine learning tasks, such as recommendations or classification.

## Project Structure

```text
ml/
├── app/
│   ├── data/
│   │   └── products.json      # Product database (JSON)
│   ├── service/
│   │   ├── __init__.py
│   │   └── products.py       # Data loading and search logic
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   └── requirements.txt      # Project dependencies
├── scratch/                   # Experimental scripts and tests
│   └── test_search.py        # Independent search logic testing
├── scripts/                   # Utility scripts
│   └── safety_hook.py        # Pre-execution safety hooks
└── README.md                  # Project documentation
```

## Features

- **FastAPI Framework**: High-performance asynchronous API.
- **Product Search**: Case-insensitive search by product name.
- **Health Check**: Endpoint to verify service status.
- **RESTful Design**: Clean and structured JSON responses.

## Prerequisites

- Python 3.8+
- Virtual Environment (recommended)

## Installation & Setup

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd ml
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r app/requirements.txt
   ```

## Running the Application

Start the FastAPI server using `uvicorn`:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Once the server is running, you can access the interactive API docs at:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|

| `GET` | `/` | Root endpoint, returns status OK. |
| `GET` | `/health` | Service health check. |
| `GET` | `/products` | List all products or search by name. |

#### Product Search Parameters

- `name` (query string): Optional. Search term for product names (min: 1 char, max: 50 chars).

**Example Request**:

```bash
curl http://127.0.0.1:8000/products?name=xiaomi
```

## Technical Implementation

- **Data Persistence**: Uses a flat-file JSON storage (`app/data/products.json`).
- **Input Validation**: Leverages FastAPI's `Query` parameters for automatic validation and range checking.
- **Search Logic**: Implements a case-insensitive partial match algorithm using native Python list comprehensions.
- **Service Layer**: Decouples API routes from data access logic via `app/service/products.py`.

## Security & Reliability

- **Safety Hooks**: A pre-commit safety script (`scripts/safety_hook.py`) prevents the inclusion of dangerous shell commands in the codebase.
- **Input Sanitization**: Query strings are stripped of whitespace and normalized to prevent simple injection or formatting issues.
- **Error Handling**: Standard HTTP status codes (404 for missing products, 422 for validation errors) are used consistently.

## Development & Testing

You can run experimental search tests without starting the server:

```bash
python scratch/test_search.py
```

## Future Roadmap

- [ ] Implement product categorization using NLP.
- [ ] Add vector-based semantic search.
- [ ] Integrate a proper database (PostgreSQL/MongoDB).
- [ ] Containerization with Docker.
- [ ] Unit testing for service layer components.
