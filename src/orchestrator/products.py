from fastmcp import FastMCP

products = FastMCP(name="Products", instructions="Product operations")


@products.tool(tags={"products"})
def search_products(query: str) -> list[dict]:
    """Search products by text."""
    return [
        {"id": 1, "name": "Widget", "q": query},
        {"id": 2, "name": "Gadget", "q": query},
    ]


@products.tool(tags={"products"})
def get_product(product_id: int) -> dict:
    """Get product details."""
    return {"id": product_id, "name": "Widget", "price": 9.99}


@products.tool(tags={"products"})
def check_stock(product_id: int) -> dict:
    """Check stock level."""
    return {"id": product_id, "stock": 42}


if __name__ == "__main__":
    products.run(transport="http", host="127.0.0.1", port=9102)
