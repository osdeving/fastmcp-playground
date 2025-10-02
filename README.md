# FastMCP Playground

Este projeto demonstra um sistema de orquestração FastMCP com múltiplos servidores de domínio e seleção baseada em sessão.

## Arquitetura

### Orchestrator (Gateway)

-   **Porta:** 9100
-   **Função:** Gateway principal que roteia para servidores de domínio específicos
-   **Recursos:** Seleção de domínio por sessão, middleware de filtro de ferramentas

### Servidores de Domínio

1. **Invoicing Server** (porta 9101) - Operações de faturamento
2. **Products Server** (porta 9102) - Gerenciamento de produtos
3. **Users Server** (porta 9103) - Gerenciamento de usuários

## Funcionalidades do Orchestrator

### Ferramentas Principais (Sempre Disponíveis)

-   `list_domains` - Lista domínios disponíveis
-   `select_domain` - Seleciona domínio ativo para a sessão
-   `get_session_status` - Verifica status da sessão atual

### Recursos

-   Ferramentas do orchestrator sempre disponíveis para gerenciamento de sessão

### Middleware de Escopo de Domínio

-   Filtra ferramentas baseado na seleção de domínio da sessão
-   Garante que apenas ferramentas relevantes sejam expostas
-   Mantém ferramentas do orchestrator sempre disponíveis

## Como Usar

### Opção 1: Teste Automático (Recomendado)

O script de teste automatizado inicia todos os servidores e executa os testes:

```bash
# Um único comando para testar tudo
uv run test_orchestrator.py
```

Este comando:

1. 🚀 Inicia automaticamente todos os servidores (invoicing, products, users, orchestrator)
2. ⏳ Aguarda todos os servidores estarem prontos
3. 🧪 Executa testes completos de todas as funcionalidades
4. 🛑 Para automaticamente todos os servidores ao final

### Opção 2: Inicialização Manual

### 1. Iniciar Servidores de Domínio

```bash
# Terminal 1 - Invoicing
uv run src/invoicing.py

# Terminal 2 - Products
uv run src/products.py

# Terminal 3 - Users
uv run src/users.py
```

### 2. Iniciar Orchestrator

```bash
# Terminal 4 - Orchestrator
uv run src/orchestrator.py
```

### 3. Conectar Cliente

```python
import asyncio
from fastmcp import Client

async def demo():
    async with Client("http://127.0.0.1:9100/mcp") as client:
        # Listar domínios disponíveis
        domains = await client.call_tool("list_domains")
        print("Domínios:", domains)

        # Selecionar domínio
        await client.call_tool("select_domain", {"domain": "invoicing"})

        # Agora ferramentas de faturamento estão disponíveis
        invoice = await client.call_tool("invoicing_create_invoice", {
            "customer_id": 123,
            "amount": 100.0
        })
        print("Fatura:", invoice)

asyncio.run(demo())
```

## Melhorias Implementadas

### 1. **Documentação e Estrutura**

-   Documentação completa em docstrings
-   Código organizado em seções lógicas
-   Logging estruturado para debug

### 2. **Middleware Aprimorado**

-   Implementação robusta do `DomainScopeMiddleware`
-   Melhor tratamento de erros
-   Validação de acesso por sessão

### 3. **Ferramentas Adicionais**

-   `get_session_status` para verificar estado da sessão
-   Recurso `session://status` para informações detalhadas
-   Mensagens de erro mais descritivas

### 4. **Gerenciamento de Sessão**

-   Identificação robusta de sessão
-   Mapeamento persistente de domínios por sessão
-   Notificações automáticas de mudanças

### 5. **Setup Assíncrono**

-   Configuração adequada de proxies HTTP
-   Tratamento de falhas de conexão
-   Logging de status de montagem

## Comandos CLI

### Teste Automatizado Completo

```bash
# Inicia todos os servidores e executa testes
uv run test_orchestrator.py
```

### Comandos Individuais (para desenvolvimento)

```bash
# Instalar fastmcp
uv add fastmcp

# Rodar servidores individuais
uv run src/invoicing.py    # porta 9101
uv run src/products.py     # porta 9102
uv run src/users.py        # porta 9103
uv run src/orchestrator.py # porta 9100

# Inspeção de servidores
uv run fastmcp inspect src/orchestrator.py:main --format fastmcp
uv run fastmcp inspect src/invoicing.py --format mcp
```

### FastMCP CLI Global

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
