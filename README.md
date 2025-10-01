# FastMCP Playground

## Comandos

Instalar fastmcp:

```bash
uv add fastmcp
```

Rodando fastmcp cli ambiente global (`uv tool run` ou `uvx`) ou local (`uv run`):

```bash
uv tool run fastmcp inspect src/server.py
uv tool run fastmcp inspect src/server.py --format mcp
uv tool run fastmcp inspect src/server.py --format fastmcp

uvx fastmcp inspect src/server.py
uvx fastmcp inspect src/server.py --format mcp
uvx fastmcp inspect src/server.py --format fastmcp

uv run fastmcp inspect src/server.py
uv run fastmcp inspect src/server.py --format mcp
uv run fastmcp inspect src/server.py --format fastmcp
```

## Usando FastMCP


Um servidor FastMCP é uma coleção de tools, resources e outros componentes MCP. Para criar um servidor instancie uma classe FastMCP.

```python
from fastmcp import FastMCP

mcp = FastMCP('My FastMCP Server')
```

Para adicionar uma tool ao servidor use o decorador `@mcp.tool`.

```python
@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"
```

Para iniciar o servidor use o método `mcp.run()`.

```python
if __name__ == "__main__":
    mcp.run(host="localhost", port=8000, debug=True, transport="http")
```

Você pode rodar o servidor como um script ou usar o FastMCP CLI. Quando usar o CLI, não importa se existe um mcp.run() no código, o CLI sempre iniciará o servidor.

```bash
uv run server.py
fastmcp run server.py:mcp --transport http --port 8000
```

Uma vez que o servidor estiver rodando, você pode conectar um cliente MCP a ele.

```python
import asyncio
from fastmcp import Client

client = Client("http://localhost:8000")

async def call_tool():
    async with client:
        result = await client.call("hello", name="World")
        print(result)

asyncio.run(call_tool())
```
## Deploy FastMCP
Para fazer o deploy do seu servidor, você precisará de uma conta no GitHub. Depois de criar uma, você pode fazer o deploy do seu servidor quatro passos:

1 - Crie um arquivo my_server.py com o conteúdo do seu servidor FastMCP

2 - Envie o arquivo my_server.py para um repositório no GitHub

3 - Faça login no FastMCP Cloud com sua conta do GitHub

4 - Crie um novo projeto a partir do seu repositório e informe my_server.py:mcp como ponto de entrada do servidor

Pronto! O FastMCP Cloud irá construir e publicar seu servidor, tornando-o disponível em uma URL como https://seu-projeto.fastmcp.app/mcp. Você pode conversar com ele para testar sua funcionalidade ou conectar-se a partir de qualquer cliente LLM que suporte o protocolo MCP.


