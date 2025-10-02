from fastmcp import FastMCP

invoicing = FastMCP(name="Invoicing", instructions="Invoice operations")


@invoicing.tool(tags={"invoicing"})
def create_invoice(customer_id: int, amount: float) -> dict:
    """Create a new invoice."""
    return {
        "invoice_id": 123,
        "customer_id": customer_id,
        "amount": amount,
        "status": "open",
    }


@invoicing.tool(tags={"invoicing"})
def get_invoice(invoice_id: int) -> dict:
    """Get invoice by ID."""
    return {"invoice_id": invoice_id, "amount": 100.0, "status": "open"}


@invoicing.tool(tags={"invoicing"})
def pay_invoice(invoice_id: int) -> dict:
    """Mark invoice as paid."""
    return {"invoice_id": invoice_id, "status": "paid"}


if __name__ == "__main__":
    # HTTP (Streamable) em 9101
    invoicing.run(transport="http", host="127.0.0.1", port=9101)
