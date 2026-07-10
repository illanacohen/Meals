# Meals — Proyecto Nutrición

API REST para el seguimiento alimenticio y la gestión de metas nutricionales. Este repositorio es la base técnica de una aplicación orientada a ayudar a las personas a alcanzar sus objetivos alimenticios de forma sostenible.

## Objetivo

La app busca **ayudar al usuario a conseguir su objetivo alimenticio** mediante un acompañamiento integral — tipo coach — basado en conocimientos científicos, tanto fisiológicos como de disciplina y hábitos.

Muchas personas no logran sus metas por factores como:

- Falta de autoconocimiento
- Exceso de carga sobre la fuerza de voluntad
- Negociación constante sobre calorías y vicios
- Autoengaño en el registro y seguimiento de lo que comen

Este proyecto apunta a reducir esos obstáculos con un enfoque práctico:

- **Organización de comidas** — planificar con anticipación en lugar de decidir en el momento
- **Permitidos no a mano** — definir de antemano qué está permitido para evitar decisiones impulsivas
- **Objetivos claros** — visualización concreta de metas para mantener el rumbo
- **Registro de emociones** — positivas y negativas, para entender el vínculo entre estado anímico y alimentación
- **Registro de contexto de vida** — capturar circunstancias que influyen en las decisiones alimenticias

En conjunto, estas herramientas buscan **reducir la dependencia de la fuerza de voluntad** y **disminuir el autoengaño**, haciendo el proceso más consciente y sostenible.

## Estado actual

Por ahora la API implementa las **utilidades básicas de gestión de comidas**:

- Carga, actualización, eliminación y visualización de comidas con sus macronutrientes (calorías, proteína, grasa y carbohidratos)

La gestión de metas, el registro emocional, el contexto de vida y el módulo de coach están planificados como próximas etapas del proyecto.

## Stack

- **FastAPI** — framework web
- **SQLAlchemy** — ORM
- **SQLite** — base de datos local (`nutrition.db`)
- **Alembic** — migraciones
- **Pydantic** — validación de datos
- **Uvicorn** — servidor ASGI

## Estructura del proyecto

```
Meals/
├── nutrition-app/
│   ├── app/
│   │   ├── api/          # Router principal
│   │   ├── database/     # Conexión y sesión de BD
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── routes/       # Endpoints
│   │   ├── schemas/      # Schemas Pydantic
│   │   ├── services/     # Lógica de negocio (ej. macro_engine)
│   │   └── main.py       # Punto de entrada de la app
│   ├── alembic/          # Migraciones
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
└── README.md
```

## Requisitos

- Python 3.11+
- pip

## Instalación y ejecución local

```bash
cd nutrition-app

# Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
alembic upgrade head

# Levantar el servidor
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.

- Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

| Método   | Ruta              | Descripción              |
|----------|-------------------|--------------------------|
| `GET`    | `/`               | Health check             |
| `GET`    | `/meals/`         | Listar todas las comidas |
| `POST`   | `/meals/`         | Crear una comida         |
| `GET`    | `/meals/{meal_id}`| Obtener una comida       |
| `PUT`    | `/meals/{meal_id}`| Actualizar una comida    |
| `DELETE` | `/meals/{meal_id}`| Eliminar una comida      |

### Ejemplo: crear una comida

**Request**

```http
POST /meals/
Content-Type: application/json

{
  "name": "Pollo con arroz",
  "calories": 520,
  "protein": 45,
  "fat": 12,
  "carbs": 55
}
```

**Response** `201 Created`

```json
{
  "id": 1,
  "name": "Pollo con arroz",
  "calories": 520,
  "protein": 45,
  "fat": 12,
  "carbs": 55
}
```

### Errores

Si se consulta, actualiza o elimina un `meal_id` que no existe, la API responde con `404`:

```json
{
  "detail": "Meal not found"
}
```

## Modelo de datos

Cada comida (`Meal`) tiene:

| Campo      | Tipo    | Descripción        |
|------------|---------|--------------------|
| `id`       | int     | Identificador      |
| `name`     | string  | Nombre de la comida|
| `calories` | float   | Calorías           |
| `protein`  | float   | Proteína (g)       |
| `fat`      | float   | Grasa (g)          |
| `carbs`    | float   | Carbohidratos (g)  |

## Base de datos

Por defecto la app usa SQLite con el archivo `nutrition.db` en `nutrition-app/`. Ese archivo está ignorado por Git (no debe commitearse).

Para crear o actualizar el esquema:

```bash
cd nutrition-app
alembic upgrade head
```

## Docker

El proyecto incluye `Dockerfile` y `docker-compose.yml`. Para levantar los servicios:

```bash
cd nutrition-app
docker compose up --build
```

> **Nota:** la configuración actual de la app apunta a SQLite. El servicio Postgres en `docker-compose.yml` está preparado para una futura migración a PostgreSQL.

## Desarrollo

```bash
# Crear una nueva migración tras cambiar modelos
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```
