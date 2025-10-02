# 🚀 FastMCP Orchestrator - Teste Automatizado

## Uso Simples

Execute um único comando para testar todo o sistema:

```bash
uv run test_orchestrator.py
```

## O que o script faz automaticamente:

### 1. 🏗️ **Inicialização Automática**

-   Inicia servidor de **invoicing** na porta 9101
-   Inicia servidor de **products** na porta 9102
-   Inicia servidor de **users** na porta 9103
-   Inicia **orchestrator** na porta 9100

### 2. ⏳ **Verificação de Saúde**

-   Aguarda todos os servidores ficarem prontos
-   Verifica se o orchestrator consegue se conectar aos domínios
-   Usa retry logic para garantir conexões estáveis

### 3. 🧪 **Testes Abrangentes**

-   Testa listagem de domínios disponíveis
-   Testa seleção de cada domínio (invoicing, products, users)
-   Verifica filtro de ferramentas por sessão
-   Executa ferramentas específicas de cada domínio
-   Valida status de sessão

### 4. 🛑 **Limpeza Automática**

-   Para todos os servidores graciosamente
-   Limpa processos em caso de interrupção (Ctrl+C)

## Exemplo de Saída

```
FastMCP Orchestrator Test Suite with Auto Server Management
============================================================
🚀 Starting all FastMCP servers...
✅ invoicing server started (PID: 12345)
✅ products server started (PID: 12346)
✅ users server started (PID: 12347)
✅ orchestrator server started (PID: 12348)

⏳ Waiting for orchestrator to be fully ready...
✅ Orchestrator is ready after 3 attempts

🚀 Testing FastMCP Orchestrator
==================================================
📡 Connecting to orchestrator at http://127.0.0.1:9100...
✅ Connected successfully!

🔧 Testing INVOICING domain functionality...
💰 Testing invoice creation...
Invoice result: {'invoice_id': 123, 'customer_id': 123, 'amount': 99.99, 'status': 'open'}
✅ Invoicing domain test completed

🔧 Testing PRODUCTS domain functionality...
📦 Testing product search...
Products result: [{'id': 1, 'name': 'Widget', 'q': 'test'}, {'id': 2, 'name': 'Gadget', 'q': 'test'}]
✅ Products domain test completed

🔧 Testing USERS domain functionality...
👤 Testing user lookup...
User result: {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}
✅ Users domain test completed

✅ All domain tests completed successfully!

🛑 Stopping all servers...
✅ All servers stopped gracefully
```

## Troubleshooting

### Se o teste falhar:

1. **Verificar portas disponíveis**

    ```bash
    # Verificar se as portas estão em uso
    netstat -tulpn | grep -E ':(9100|9101|9102|9103)'
    ```

2. **Executar manualmente**

    ```bash
    # Terminal 1
    uv run src/invoicing.py

    # Terminal 2
    uv run src/products.py

    # Terminal 3
    uv run src/users.py

    # Terminal 4
    uv run src/orchestrator.py

    # Terminal 5 - Teste manual
    uv run python -c "
    import asyncio
    from fastmcp import Client

    async def test():
        async with Client('http://127.0.0.1:9100') as client:
            print(await client.call_tool('list_domains'))

    asyncio.run(test())
    "
    ```

3. **Debug individual**

    ```bash
    # Inspecionar orchestrator
    uv run fastmcp inspect src/orchestrator.py:main

    # Inspecionar domínio específico
    uv run fastmcp inspect src/invoicing.py
    ```

## Vantagens do Teste Automatizado

✅ **Simplicidade**: Um comando faz tudo
✅ **Confiabilidade**: Retry logic para conexões
✅ **Limpeza**: Para servidores automaticamente
✅ **Completo**: Testa todos os domínios
✅ **Informativo**: Logs detalhados de cada etapa

---

💡 **Dica**: Use `Ctrl+C` para interromper o teste a qualquer momento. Os servidores serão parados automaticamente!
