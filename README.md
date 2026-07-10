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

La API implementa:

- CRUD de comidas con macronutrientes (calorías, proteína, grasa, carbohidratos y fibra)
- **Ingredientes por comida** (`items`: quantity + unit → grams vía catálogo local)
- **Planes de alimentación diarios** con 4 slots fijos (Desayuno, Almuerzo, Merienda, Cena)
- **Metas diarias** de macros, con resumen del plan vs objetivo

El registro emocional, el contexto de vida y el módulo de coach están planificados como próximas etapas.

## Future features

- **Perfil corporal y actividad** — ingreso de peso, edad, altura e intensidad de ejercicio diario para calcular necesidades energéticas de forma personalizada.
- **Objetivo nutricional** — elegir entre déficit (con distintas intensidades), mantenimiento o volumen limpio, y generar metas de macros alineadas a ese objetivo.
- **Distribución inteligente de macros** — estrategia basada en el horario de entrenamiento y/o la rutina diaria de la persona, para repartir calorías y macros entre las comidas del día de modo que se reduzca el hambre y se optimice la energía (por ejemplo, más carbohidratos alrededor del entrenamiento).

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
python -m uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.

- Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### Meals

| Método   | Ruta              | Descripción              |
|----------|-------------------|--------------------------|
| `GET`    | `/`               | Health check             |
| `GET`    | `/meals/`         | Listar todas las comidas |
| `POST`   | `/meals/`         | Crear una comida         |
| `GET`    | `/meals/{meal_id}`| Obtener una comida       |
| `PUT`    | `/meals/{meal_id}`| Actualizar una comida    |
| `DELETE` | `/meals/{meal_id}`| Eliminar una comida      |

### Meal Plans

| Método   | Ruta | Descripción |
|----------|------|-------------|
| `POST`   | `/plans/` | Crear plan del día (crea 4 slots) |
| `GET`    | `/plans/` | Listar planes |
| `GET`    | `/plans/by-date/{date}` | Obtener plan por fecha |
| `GET`    | `/plans/{plan_id}` | Obtener plan con slots y comidas |
| `GET`    | `/plans/{plan_id}/summary` | Totales del plan vs meta del día |
| `GET`    | `/plans/{plan_id}/validate` | Validar plan contra la meta (± tolerancia) |
| `POST`   | `/plans/{plan_id}/slots/{position}/meals` | Agregar comida a un slot (1–4) |
| `DELETE` | `/plans/{plan_id}` | Eliminar plan |

### Daily Goals

| Método   | Ruta | Descripción |
|----------|------|-------------|
| `POST`   | `/goals/` | Crear meta diaria |
| `GET`    | `/goals/` | Listar metas |
| `GET`    | `/goals/by-date/{date}` | Obtener meta por fecha |
| `GET`    | `/goals/{goal_id}` | Obtener meta |
| `PUT`    | `/goals/{goal_id}` | Actualizar meta |
| `DELETE` | `/goals/{goal_id}` | Eliminar meta |

### Ejemplo: crear una comida

**Request**

```http
POST /meals/
Content-Type: application/json

{
  "name": "Pollo con verduras",
  "calories": 420,
  "protein": 45,
  "fat": 12,
  "carbs": 20,
  "fiber": 6,
  "items": [
    { "name": "pollo", "quantity": 150, "unit": "g" },
    { "name": "zanahoria", "quantity": 80, "unit": "g" },
    { "name": "zapallito", "quantity": 100, "unit": "g" },
    { "name": "cebolla", "quantity": 40, "unit": "g" },
    { "name": "huevo", "quantity": 2, "unit": "unit" }
  ]
}
```

**Response** `201 Created`

```json
{
  "id": 1,
  "name": "Pollo con verduras",
  "calories": 420,
  "protein": 45,
  "fat": 12,
  "carbs": 20,
  "fiber": 6,
  "slot_id": null,
  "items": [
    { "id": 1, "name": "pollo", "quantity": 150, "unit": "g", "grams": 150 },
    { "id": 2, "name": "zanahoria", "quantity": 80, "unit": "g", "grams": 80 },
    { "id": 3, "name": "zapallito", "quantity": 100, "unit": "g", "grams": 100 },
    { "id": 4, "name": "cebolla", "quantity": 40, "unit": "g", "grams": 40 },
    { "id": 5, "name": "huevo", "quantity": 2, "unit": "unit", "grams": 100 }
  ]
}
```

> **Unidades:** `g`, `unit` (piezas) o `ml`. Para `unit`/`ml`, un catálogo local convierte a gramos (ej. huevo = 50 g). Si el alimento no está en el catálogo, pasá `grams_per_unit` en el item.
### Errores

Si se consulta, actualiza o elimina un `meal_id` que no existe, la API responde con `404`:

```json
{
  "detail": "Meal not found"
}
```

## Modelo de datos

### Meal

| Campo      | Tipo    | Descripción              |
|------------|---------|--------------------------|
| `id`       | int     | Identificador            |
| `name`     | string  | Nombre de la comida      |
| `calories` | float   | Calorías                 |
| `protein`  | float   | Proteína (g)             |
| `fat`      | float   | Grasa (g)                |
| `carbs`    | float   | Carbohidratos (g)        |
| `fiber`    | float   | Fibra (g)                |
| `slot_id`  | int?    | Slot del plan (opcional) |
| `items`    | list    | Ingredientes (nombre + g)|

### MealItem

Cada elemento de una comida:

| Campo            | Tipo   | Descripción                                      |
|------------------|--------|--------------------------------------------------|
| `id`             | int    | Identificador                                    |
| `name`           | string | Ingrediente                                      |
| `quantity`       | float  | Cantidad                                         |
| `unit`           | string | `g`, `unit` o `ml`                               |
| `grams`          | float  | Equivalente en gramos (calculado)                |
| `grams_per_unit` | float? | Solo en create: override si no está en catálogo  |

Ejemplo con unidades: `{ "name": "huevo", "quantity": 2, "unit": "unit" }` → `grams: 100`.

Al actualizar una comida, si enviás `items`, se reemplaza la lista completa.

### MealPlan

Un plan por fecha. Al crearlo se generan 4 slots: Desayuno (1), Almuerzo (2), Merienda (3), Cena (4).

### DailyGoal

Una meta de macros por fecha (`calories`, `protein`, `fat`, `carbs`, `fiber`). El endpoint `/plans/{id}/summary` compara los totales del plan con la meta del mismo día.

### Validar plan vs meta

`GET /plans/{plan_id}/validate?tolerance_percent=5`

Compara los macros del plan con la meta del mismo día. Un macro está `ok` si la diferencia está dentro del porcentaje de tolerancia (default 5%). Responde `is_valid: true/false` y el detalle por nutriente (`ok` / `under` / `over`). Si no hay meta para esa fecha, responde `404`.

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
