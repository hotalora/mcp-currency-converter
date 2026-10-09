# Currency Conversion Stack

El repositorio incluye tres servicios desplegables con Docker Compose:

- `auth-provider`: registro, login y validacion de JWT.
- `currency_management_smcp`: servidor MCP con la tool `convert_currency`.
- `currency_management_aiagent`: agente LangGraph que consume la tool MCP.

El agente valida el token de usuario con `auth-provider` y reenvia ese mismo
token al MCP. El MCP valida nuevamente el token con `auth-provider`. La tool
obtiene la tasa mas reciente del API publico de Frankfurter; no requiere API
key ni tiene endpoint propio de conversion.

## Levantar los servicios

Requiere Docker Desktop y Docker Compose. Copia `.env.example` a `.env` y,
cuando quieras habilitar consultas al modelo, agrega tu clave en
`OPENAI_API_KEY`. La clave se puede configurar despues: el stack arranca sin
ella, pero el endpoint del agente no podra completar peticiones al LLM.

```powershell
Copy-Item .env.example .env

bash

cp .env.example .env

# Edita .env y configura OPENAI_API_KEY cuando la tengas.

docker compose down --remove-orphans

docker compose up -d --force-recreate currency-agent
```

Servicios:

| Servicio | URL local |
| --- | --- |
| Auth | `http://localhost:8000` |
| MCP Streamable HTTP | `http://localhost:8001/api/mcp` |
| Agente | `http://localhost:8003` |

El agente ofrece `GET /health` y `POST /chat`. Registra e inicia sesion contra
el auth-provider para obtener un access token, y envia el mensaje al agente:

```powershell
$tokens = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"usuario@example.com","password":"UnaClaveSegura123"}'

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8003/chat `
  -Headers @{ Authorization = "Bearer $($tokens.access_token)" } `
  -ContentType "application/json" `
  -Body '{"message":"Convierte 25 USD a EUR","conversation_id":"demo"}'
```

`POST /chat` documenta su formato de salida en OpenAPI. El agente siempre
responde con un mensaje de texto en lenguaje natural. La tool MCP conserva
su resultado estructurado internamente para que el agente pueda preparar una
respuesta clara y amable, sin devolver JSON ni tablas al cliente.

Ejemplo de respuesta:

```json
{
  "conversation_id": "demo",
  "messages": [
    {
      "type": "text",
      "content": "¡Claro! 25 USD equivalen a 22.3125 EUR. La tasa utilizada fue 0.8925 y corresponde al 9 de octubre de 2026. ¡Avísame si necesitas otra conversión!"
    }
  ]
}
```

Si no existe el usuario, primero usa `POST /auth/register` con `email` y
`password` (minimo 8 caracteres). Para probar el MCP directamente, usa un
cliente compatible con MCP en `http://localhost:8001/api/mcp` y pasa el mismo
header `Authorization: Bearer <access_token>`. La tool es
`convert_currency(amount, from_currency, to_currency)`.

`docker compose down` detiene los contenedores sin borrar los volumenes de
SQLite y Redis. Cambia `AUTH_SECRET_KEY` antes de usar el stack fuera de
desarrollo local.

## Pruebas

Ejecuta `uv run pytest` desde cada proyecto Python para lanzar su suite.