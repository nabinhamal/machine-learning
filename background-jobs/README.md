# Background Jobs & Infrastructure Project

This project provides a robust, production-ready stack for handling background tasks, centralized logging, and infrastructure management for a FastAPI application.

## Tech Stack

- **FastAPI**: Core Python web framework.
- **Celery**: Distributed task queue for background jobs.
- **RabbitMQ**: Message broker for Celery.
- **Redis**: Result backend for Celery and storage for rate limiting.
- **PostgreSQL**: Relational database with **pgvector** support.
- **Nginx (Active/Standby)**: Dual Nginx fallback system.
- **HAProxy**: High Availability gateway and failover manager.
- **Loki + Promtail + Grafana**: Centralized logging and visualization stack.
- **Flower**: Real-time monitoring for Celery tasks.

## Getting Started

### Prerequisites

- Docker & Docker Compose installed.

### Setup & Run

1. From research root, navigate to this directory:

   ```bash
   cd background-jobs
   ```

2. Start the stack:

   ```bash
   docker-compose up --build -d
   ```

## Infrastructure Access

- **API (FastAPI)**: [http://localhost](http://localhost) (via HAProxy)
- **API Docs (Swagger)**: [http://localhost/docs](http://localhost/docs)
- **Celery Monitoring (Flower)**: [http://localhost/flower/](http://localhost/flower/)
- **HAProxy Stats**: [http://localhost:1936](http://localhost:1936) (User: `admin`, Pass: `admin`)
- **Logging & Dashboards (Grafana)**: [http://localhost:3000](http://localhost:3000) (User: `admin`, Pass: `admin`)
- **RabbitMQ Management**: [http://localhost:15672](http://localhost:15672) (User: `guest`, Pass: `guest`)

## Logging Visualization

1. Open **Grafana** at `http://localhost:3000`.
2. Go to **Explore** (compass icon).
3. Select **Loki** as the datasource.
4. Use the query `{container="ml_api"}` or `{container="ml_worker"}` to see live logs.

## Background Jobs

- Enqueue a task: `POST /tasks/process?data=some_data`
- Check task status: `GET /tasks/{task_id}`

## Rate Limiting

The `/tasks/process` endpoint is rate-limited to **5 requests per minute** per client.

## Database (pgvector)

PostgreSQL is equipped with the `vector` extension. A sample `embeddings` table is defined in `app/database.py`.
