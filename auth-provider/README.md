# FastAPI Authentication Service

Servicio de autenticacion HTTP con FastAPI, JWT, SQLite y una arquitectura por
capas inspirada en DDD. Requiere Python 3.12 y UV.

## Arquitectura

```text
src/auth_service/
  domain/          Entidades, errores y contratos de repositorio
  application/     Casos de uso de registro, inicio, validacion y refresh
  infrastructure/ Adaptadores SQLAlchemy, SQLite y seguridad JWT/Argon2
  presentation/   Endpoints HTTP y esquemas Pydantic
```

La capa de aplicacion depende de contratos de dominio y de adaptadores de
seguridad; la API conecta los casos de uso con las implementaciones SQLite.

## Instalacion y ejecucion

```powershell
uv sync --dev
```

Configure `AUTH_SECRET_KEY` con un secreto aleatorio de al menos 32 caracteres
antes de ejecutar el servicio en un entorno real. `.env` se ignora en Git.
`.env.example` documenta las variables, pero PowerShell no carga `.env`
automaticamente; exporte las variables en la terminal o en su entorno:

```powershell
$env:AUTH_SECRET_KEY = "use-a-random-secret-of-at-least-32-characters"
$env:DATABASE_URL = "sqlite:///./auth.db"
uv run uvicorn auth_service.main:app --app-dir src --reload
```

SQLite crea `auth.db` y sus tablas durante el inicio. Las contrasenas se
almacenan con hash Argon2. Access y refresh tokens son JWT HS256, se persisten
por identificador y expiran en una hora. Cada refresh valida y revoca el
refresh anterior antes de emitir un nuevo par. Los access tokens emitidos
anteriormente permanecen validos hasta su expiracion.

## API

| Metodo | Ruta | Descripcion |
| --- | --- | --- |
| `POST` | `/auth/register` | Crear usuario |
| `POST` | `/auth/login` | Validar credenciales y emitir tokens |
| `GET` | `/auth/validate` | Validar access token; requiere `Authorization: Bearer <token>` |
| `POST` | `/auth/refresh` | Rotar tokens con `{"refresh_token": "<token>"}` |

Registro y login reciben `email` y `password`. La contrasena debe tener entre
8 y 128 caracteres. Registro duplicado responde `409`, credenciales invalidas
responden `401` y las solicitudes invalidas responden `422`.

La documentacion interactiva esta disponible en `/docs`.

## Ejecutar con Docker

Con Docker Desktop instalado y abierto, desde la raiz del proyecto ejecuta en
PowerShell:

```powershell
$bytes = [byte[]]::new(32)
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$env:AUTH_SECRET_KEY = [Convert]::ToBase64String($bytes)
docker compose up --build
```

El servicio queda disponible en `http://localhost:8000` y la interfaz de
pruebas en `http://localhost:8000/docs`. La base SQLite se guarda en el volumen
persistente `auth_data`, por lo que se conserva al recrear el contenedor.
La imagen se ejecuta como usuario sin privilegios y su filesystem es de solo
lectura excepto por el volumen de datos y `/tmp`.

Para detener el servicio, presiona `Ctrl+C`. Para iniciarlo en segundo plano,
usa `docker compose up --build -d`; los logs se consultan con
`docker compose logs -f`, y se detiene con `docker compose down`. No agregues
`--volumes` a `down` si quieres conservar la base de datos.

## Pruebas

```powershell
uv run pytest
```
