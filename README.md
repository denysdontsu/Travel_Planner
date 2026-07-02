# Travel Planner API

This is a CRUD API for travel planning. Users can create travel projects and add places to visit. Places are checked with the [Art Institute of Chicago API](https://api.artic.edu/docs/#collections) before they are saved.

## Tech Stack

- FastAPI
- SQLAlchemy (async) + SQLite (aiosqlite)
- httpx (for calling the external API)
- Poetry (dependency management)

## How to Run the App

### Option 1: Docker

```bash
docker-compose up --build
```

### Option 2: Local (with Poetry)

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

The app will run at: `http://localhost:8000`

Interactive API docs (Swagger UI): `http://localhost:8000/docs`

## Environment Variables

| Variable | Default value | What it does |
|---|---|---|
| DATABASE_URL | sqlite+aiosqlite:///./travel.db | Connection string for the database |
| ARTIC_API_URL | https://api.artic.edu/api/v1 | Base URL of the Art Institute API |

You can set these in a `.env` file in the project root, or use the default values.

## Business Rules

- A project can have between 1 and 10 places.
- Every place must be checked and found in the Art Institute API before it is saved.
- The same place (same external ID) cannot be added twice to one project.
- A project cannot be deleted if one or more of its places are already marked as `visited`.
- When all places in a project are `visited`, the project becomes `completed` automatically.

## API Endpoints

### Projects

| Method | Path | Description |
|---|---|---|
| POST | /projects/ | Create a new project (places are optional) |
| GET | /projects/ | Get a list of all projects |
| GET | /projects/{project_id} | Get one project by ID |
| PUT | /projects/{project_id} | Update project name, description, or start date |
| DELETE | /projects/{project_id} | Delete a project |

### Places

| Method | Path | Description |
|---|---|---|
| POST | /projects/{project_id}/places | Add a place to a project |
| GET | /projects/{project_id}/places | Get all places in a project |
| GET | /projects/{project_id}/places/{place_id} | Get one place |
| PATCH | /projects/{project_id}/places/{place_id} | Update notes or mark a place as visited |

Full interactive documentation is here: `/docs` (Swagger UI) or `/redoc`.

## Example Requests

**Create a project with places:**

```bash
curl -X POST http://localhost:8000/projects/ \
  -H "Content-Type: application/json" \
  -d '{
  "name": "Chicago Trip",
  "description": "My first art trip",
  "places": [
    { "external_place_id": "27992" },
    { "external_place_id": "27993" },
    { "external_place_id": "27994" },
    { "external_place_id": "27995" },
    { "external_place_id": "27997" },
    { "external_place_id": "27998" },
    { "external_place_id": "27999" },
    { "external_place_id": "28000" },
    { "external_place_id": "28002" },
    { "external_place_id": "28004" }
  ]
}'
```

**Add a place to an existing project:**

```bash
curl -X POST http://localhost:8000/projects/1/places \
  -H "Content-Type: application/json" \
  -d '{ "external_place_id": "27998" }'
```

**Mark a place as visited:**

```bash
curl -X PATCH http://localhost:8000/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{ "is_visited": true }'
```

**Delete a project:**

```bash
curl -X DELETE http://localhost:8000/projects/1
```

## Known Limitations

- A project can be created with 0 places. The task says a project should have 1 to 10 places, but this app allows creating an empty project first and adding places later, one by one.
- The cache for place validation is stored in memory. It resets every time the app restarts.
- There is no authentication in this version.

## Possible Improvements

- Add basic authentication
- Add pagination and filters for the places list
- Add tests
- Move the in-memory cache to Redis for a production setup