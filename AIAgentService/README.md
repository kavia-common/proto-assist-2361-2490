# AIAgentService

This service exposes a FastAPI application for interpreting user prompts and generating wireframe specifications.

How to run locally (from this directory):

- Install dependencies:
  pip install -r requirements.txt

- Start the API (from project root or from this folder):
  uvicorn main:app --reload

Entrypoint details:
- The ASGI app is exposed as `main:app` at AIAgentService/main.py.
- main.py ensures the `src` directory is on sys.path and imports `api.main:app`.

Available routes (stubs for now):
- GET / -> {"status": "ok", "service": "ai-agent"}
- POST /interpret -> accepts {"prompt": "..."}, returns {"intents": []}
- POST /specify-wireframe -> accepts {"intents": [...]}, returns {"wireframe_spec": {}}
