import os
from datetime import datetime
from typing import Dict
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from app.schema.product import Product, ProductUpdate
from service.products import (
    add_product,
    change_product,
    get_all_products,
    load_products,
    remove_product,
)
from app.celery_app import celery_app
from app.tasks import process_data
from celery.result import AsyncResult
from slowapi import Limiter, _rate_limit_exceeded_handler
from app.utils.telegram import send_error_alert, send_health_alert
import traceback
from sqlalchemy import text
from app.database import engine
import redis
from contextlib import asynccontextmanager
import asyncio
from app.logger import logger
from slowapi.errors import RateLimitExceeded
import time
from slowapi.util import get_remote_address

def get_caller_key(request: Request):
    """
    Identifies the caller using 'X-API-Token' header, falling back to IP address.
    """
    token = request.headers.get("X-API-Token")
    if token:
        return f"token:{token}"
    return get_remote_address(request)
import time

load_dotenv()

# Initialize Rate Limiter
REDIS_URL = os.getenv("CELERY_RESULT_BACKEND")
if not REDIS_URL:
    raise ValueError("CELERY_RESULT_BACKEND (Redis URL) environment variable is not set")

limiter = Limiter(key_func=get_caller_key, storage_uri=REDIS_URL, headers_enabled=True)

def get_system_health():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check Database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Celery Workers (wait briefly for worker to register if needed)
    try:
        inspector = celery_app.control.inspect()
        active = inspector.active()
        if active:
            health_status["services"]["celery"] = "healthy"
        else:
            health_status["services"]["celery"] = "no active workers found"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["celery"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wait a moment for other containers (like Celery) to fully register
    await asyncio.sleep(2)
    
    health = get_system_health()
    if health["status"] == "healthy":
        await send_health_alert("healthy", "🚀 *Backend Systems Online*\nAll services (API, Postgres, Redis, Celery) are up and running.")
    else:
        await send_health_alert("unhealthy", f"⚠️ *Startup Warning*\nSome services failed to initialize:\n```json\n{health['services']}\n```")
        
    yield

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Processing Time: {process_time:.2f}ms"
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that catches all unhandled exceptions,
    logs them, and sends a notification to Telegram.
    """
    error_details = traceback.format_exc()
    request_info = f"{request.method} {request.url}\nHeaders: {dict(request.headers)}"
    
    # Log the error
    logger.error(f"Unhandled exception: {exc}\n{error_details}")
    
    # Send Telegram alert
    await send_error_alert(
        error_type=type(exc).__name__,
        details=error_details.splitlines()[-1], # Send only the last line of traceback for brevity in preview
        request_info=request_info
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. The administrator has been notified."},
    )


@app.get("/health")
async def health_check():
    """
    Check health of all vital services (DB, Redis, Celery).
    """
    health_status = get_system_health()
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health_status)


# @app.middleware("http")
# async def lifecycle(request: Request, call_next):
#     print("Before request")
#     response = await call_next(request)
#     print("After request")
#     return response


def common_logic():
    return "Hello There"


@app.get("/", response_model=dict)
def root(dep=Depends(common_logic)):
    DB_PATH = os.getenv("BASE_URL")
    # return {"message": "Welcomne to FastAPI.", "dependency": dep, "data_path": DB_PATH}
    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcomne to FastAPI.",
            "dependency": dep,
            "data_path": DB_PATH,
        },
    )


@app.get("/products", response_model=Dict)
def list_products(
    dep=Depends(load_products),
    name: str = Query(
        default=None,
        min_length=1,
        max_length=50,
        description="Search by product name (case insensitive)",
        example="Energy 3Pcs",
    ),
    sort_by_price: bool = Query(default=False, description="Sort products by price"),
    order: str = Query(
        default="asc", description="Sort order when sort_by_price=true (asc,desc)"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of items to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination Offset",
    ),
):

    # products = get_all_products()
    products = dep

    if name:
        needle = name.strip().lower()
        products = [p for p in products if needle in p.get("name", "").lower()]

    if not products:
        raise HTTPException(
            status_code=404, detail=f"No product found matching name={name}"
        )

    if sort_by_price:
        reverse = order == "desc"
        products = sorted(products, key=lambda p: p.get("price", 0), reverse=reverse)

    total = len(products)
    products = products[offset : offset + limit]
    return {"total": total, "limit": limit, "items": products}


@app.get("/products/{product_id}", response_model=Dict)
def get_product_by_id(
    product_id: str = Path(
        ...,
        min_length=36,
        max_length=36,
        description="UUID of the products",
        example="c47ea2457-c4a9-4bfg-9dd5-6464r0ebe343",
    ),
):
    products = get_all_products()
    for product in products:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found!")


@app.post("/products", status_code=201)
def create_product(product: Product):
    product_dict = product.model_dump(mode="json")
    product_dict["id"] = str(uuid4())
    product_dict["created_at"] = datetime.utcnow().isoformat() + "Z"
    try:
        add_product(product_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return product.model_dump(mode="json")


@app.delete("/products/{product_id}")
def delete_product(product_id: UUID = Path(..., description="Product UUID")):
    try:
        res = remove_product(str(product_id))
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/products/{product_id}")
def update_product(
    product_id: UUID = Path(..., description="Product UUID"),
    payload: ProductUpdate = ...,
):
    try:
        update_product = change_product(
            str(product_id), payload.model_dump(mode="json", exclude_unset=True)
        )
        return update_product
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/tasks/process", status_code=202)
@limiter.limit("5/minute")
async def trigger_process(request: Request, data: str = Query(..., description="Data to process")):
    """
    Trigger a background task with rate limiting (5 requests per minute).
    """
    task = process_data.delay(data)
    return {"task_id": task.id, "status": "Task enqueued"}


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Retrieve the status and result of a background task.
    """
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }
@app.get("/rate-limit-status")
@limiter.limit("10/minute")
async def get_rate_limit_status(request: Request):
    """
    Retrieve current rate limit status. Detailed info is in X-RateLimit-* headers.
    """
    return {
        "identity": get_caller_key(request),
        "message": "Rate limit details are provided in the X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset headers."
    }
