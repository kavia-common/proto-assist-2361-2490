from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Any, Dict

# Initialize FastAPI app with metadata for docs
app = FastAPI(
    title="AI Agent API Interface",
    version="1.0.0",
    description="RESTful API for interpreting user prompts and generating wireframe specifications."
)

# Enable permissive CORS for now (can be restricted later via env/config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models kept minimal for stub behavior

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="User input prompt to interpret")

class Intent(BaseModel):
    type: str = Field(..., description="Intent type")
    value: Any = Field(None, description="Value or payload for the intent")
    confidence: float | None = Field(None, description="Optional confidence score between 0 and 1")

class InterpretResponse(BaseModel):
    intents: List[Intent] = Field(default_factory=list, description="List of extracted intents")

class WireframeIntent(BaseModel):
    type: str = Field(..., description="Intent type")
    value: Any = Field(None, description="Optional value for the intent")

class WireframeRequest(BaseModel):
    intents: List[WireframeIntent] = Field(..., description="Intents to transform into a wireframe spec")

class WireframeResponse(BaseModel):
    wireframe_spec: Dict[str, Any] = Field(default_factory=dict, description="Minimal wireframe specification")


# PUBLIC_INTERFACE
@app.get("/", summary="Health Check", tags=["health"])
def health_check():
    """
    Health check endpoint.
    Returns a minimal status payload indicating the service is up.
    """
    return {"status": "ok", "service": "ai-agent"}

# PUBLIC_INTERFACE
@app.post(
    "/interpret",
    response_model=InterpretResponse,
    summary="Interpret user prompt and extract intents",
    tags=["interpretation"]
)
def interpret_prompt(payload: PromptRequest) -> InterpretResponse:
    """
    Interpret a user prompt and return a minimal intents list.
    Currently returns an empty list as stub to ensure 200 response.
    """
    # Stub implementation: returns empty intents to avoid import/runtime errors
    return InterpretResponse(intents=[])

# PUBLIC_INTERFACE
@app.post(
    "/specify-wireframe",
    response_model=WireframeResponse,
    summary="Generate wireframe specification from intents",
    tags=["wireframe"]
)
def specify_wireframe(payload: WireframeRequest) -> WireframeResponse:
    """
    Convert intents into a wireframe specification.
    Currently returns an empty spec as stub to ensure 200 response.
    """
    # Stub implementation: returns an empty dict spec
    return WireframeResponse(wireframe_spec={})
