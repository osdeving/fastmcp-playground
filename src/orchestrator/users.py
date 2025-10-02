from fastmcp import FastMCP

users = FastMCP(name="Users", instructions="User operations")


@users.tool(tags={"users"})
def get_user(user_id: int) -> dict:
    """Get user profile."""
    return {"id": user_id, "name": "Alice", "email": "alice@example.com"}


@users.tool(tags={"users"})
def update_email(user_id: int, email: str) -> dict:
    """Update user email."""
    return {"id": user_id, "email": email, "updated": True}


@users.tool(tags={"users"})
def list_dependents(user_id: int) -> list[dict]:
    """List user dependents."""
    return [{"id": 10, "name": "Bob"}, {"id": 11, "name": "Carol"}]


if __name__ == "__main__":
    users.run(transport="http", host="127.0.0.1", port=9103)
