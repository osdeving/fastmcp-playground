from fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool(
    # se não fornecido usa o nome da função
    name='find_products',

    # descrição da tool, se fornecido aqui não usará docstring para esse fim.
    description='Search the product catalog with optional category filtering.',

    # conjunto de tags da tool, pode ser usado pelo server e alguns casos pelo client também
    tags={'catalog', 'search'},

    # informações sobre a tool. Esses dados são passados para o MCP no schema via o campo _meta e pode ser usado pelo client
    meta={'version': '1.2', 'author': 'product-team'}
)
def search_products(query: str, category: str | None = None) -> list[dict]:
    """Internal description (ignored if description is provided above)."""
    print(f'Searching for "${query}" in "${category}"')
    return [{"id": 2, "name": "Wireless Keyboard"}]


if __name__ == '__main__':
    mcp.run()


