from fastapi import FastAPI, HTTPException, Path, Query

from app.service.products import get_all_products

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


# @app.get("/products/{product_id}")
# def get_product(product_id: int):
#     products = [{"id": 1, "name": "Product 1"}, {"id": 2, "name": "Product 2"}, {"id": 3, "name": "Product 3"}]
#     for product in products:
#         if product["id"] == product_id:
#             return product
#     raise HTTPException(status_code=404, detail="Product not found")

# @app.get("/products")
# def get_products()      :
#     return get_all_products()


@app.get("/products")
def list_products(
    name: str = Query(
        default=None,
        min_length=1,
        max_length=50,
        description="Search by product  name (case insensitive)",
    ),
    sort_by_price: bool = Query(
        default=False,
        description="Sort products by price",
    ),
    order: str = Query(
        default="asc",
        description="Sort order",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Limit the number of products",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination of products",
    ),
):

    products = get_all_products()
    if name:
        needle = name.strip().lower()
        products = [p for p in products if needle in p.get("name", "").lower()]

        if not products:
            raise HTTPException(
                status_code=404, detail=f"Product not found for the given name={name}"
            )
    if sort_by_price:
        reverse = order == "desc"
        products = sorted(products, key=lambda p: p.get("price", 0), reverse=reverse)

    total = len(products)
    products = products[offset : offset + limit]
    return {
        "total": total,
        "items": products,
    }


@app.get("/products/{product_id}")
def get_product_by_id(
    product_id: str = Path(
        ...,
        description="Product ID",
        min_length=1,
        max_length=50,
        example="0005a4ea-ce3f-4dd7-bee0-f4ccc70fea6a",
    ),
):
    products = get_all_products()
    product = [p for p in products if p["id"] == product_id][0]
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
