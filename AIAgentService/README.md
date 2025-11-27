# AIAgentService

This service exposes a FastAPI application for interpreting user prompts and generating wireframe specifications.

How to run locally (from this directory):

- Install dependencies:
  pip install -r requirements.txt

- Start the API (from project root or from this folder):
  uvicorn main:app --reload

Environment:
- Copy .env.example to .env and set variables as needed.
- AI_API_KEY: If set, requests must include Authorization: Bearer <AI_API_KEY>.
- AI_PORT: Optional port variable for your process manager; uvicorn command still controls actual port unless integrated.

Entrypoint details:
- The ASGI app is exposed as `main:app` at AIAgentService/main.py.
- main.py ensures the `src` directory is on sys.path and imports `api.main:app`.

Authentication:
- Optional API key authentication via Authorization header.
  - If environment variable AI_API_KEY is set, all write endpoints require:
    Authorization: Bearer <AI_API_KEY>
  - If AI_API_KEY is not set, endpoints are open for local/dev use.

Available routes:
- GET / -> Health check
- POST /interpret -> accepts {"prompt": "..."}, returns {"intents": [...]}
- POST /specify-wireframe -> accepts {"intents": [...]}, returns {"wireframe_spec": {...}}

OpenAPI docs:
- Visit /docs for Swagger UI and /openapi.json for schema.
- Tags:
  - health
  - interpretation
  - wireframe

Request/Response Models:
- PromptRequest { prompt: string }
- Intent { type: string, value?: any, confidence?: number(0..1) }
- InterpretResponse { intents: Intent[] }
- WireframeIntent { type: string, value?: any }
- WireframeRequest { intents: WireframeIntent[] }
- WireframeSpec { id: string, layout: object, components: object[], metadata: object }
- WireframeResponse { wireframe_spec: object }

Keyword-based interpretation:
- The /interpret endpoint uses simple rule-based parsing to detect:
  - login, dashboard, list, table, form, button, navbar
- Confidence scoring:
  - Exact word match: 1.0
  - Substring match: 0.8
  - No match: returns 'unknown' intent with 0.1

Wireframe specification:
- The /specify-wireframe endpoint maps detected intents to a deterministic JSON structure:
  - layout: container -> rows -> columns -> component ids
  - components: array of { id, type, props }
  - metadata: generator info

Examples:

1) Interpret
curl -s -X POST http://localhost:8000/interpret \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Create a dashboard with a navbar and a table of items"}'

With API key:
curl -s -X POST http://localhost:8000/interpret \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AI_API_KEY" \
  -d '{"prompt":"Create a dashboard with a navbar and a table of items"}'

2) Specify wireframe
curl -s -X POST http://localhost:8000/specify-wireframe \
  -H "Content-Type: application/json" \
  -d '{"intents":[{"type":"dashboard"},{"type":"navbar"},{"type":"table"}]}'

With API key:
curl -s -X POST http://localhost:8000/specify-wireframe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AI_API_KEY" \
  -d '{"intents":[{"type":"dashboard"},{"type":"navbar"},{"type":"table"}]}'
