import os
import re
import uuid
from typing import List, Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr

# Initialize FastAPI app with metadata for docs
openapi_tags = [
    {"name": "health", "description": "Service health and readiness endpoints"},
    {"name": "interpretation", "description": "Prompt interpretation and intent extraction"},
    {"name": "wireframe", "description": "Transform intents into structured wireframe specifications"},
]
app = FastAPI(
    title="AI Agent API Interface",
    version="1.0.0",
    description="RESTful API for interpreting user prompts and generating wireframe specifications.",
    openapi_tags=openapi_tags,
)

# Enable permissive CORS for now (can be restricted later via env/config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Security (optional API key via Authorization: Bearer <key>) ----------
def get_expected_api_key() -> Optional[str]:
    # Read once; FastAPI process is long-lived
    return os.getenv("AI_API_KEY") or None

def require_api_key(authorization: Optional[str] = Header(None, description="Bearer token for AI Agent API")):
    """
    Optional API key validation. If AI_API_KEY is set in env, require requests to include:
    Authorization: Bearer <AI_API_KEY>

    If AI_API_KEY is not set, allow all requests.
    """
    expected = get_expected_api_key()
    if not expected:
        return  # No auth required in this mode
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    provided = authorization.split(" ", 1)[1].strip()
    if provided != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return

# ---------------------- Models ----------------------

class PromptRequest(BaseModel):
    prompt: constr(strip_whitespace=True, min_length=1) = Field(..., description="User input prompt to interpret")

class Intent(BaseModel):
    type: str = Field(..., description="Intent type")
    value: Any = Field(None, description="Value or payload for the intent")
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Optional confidence score between 0 and 1"
    )

class InterpretResponse(BaseModel):
    intents: List[Intent] = Field(default_factory=list, description="List of extracted intents")

class WireframeIntent(BaseModel):
    type: str = Field(..., description="Intent type")
    value: Any = Field(None, description="Optional value for the intent")

class WireframeRequest(BaseModel):
    intents: List[WireframeIntent] = Field(..., description="Intents to transform into a wireframe spec")

class WireframeSpec(BaseModel):
    id: str = Field(..., description="Unique identifier for the generated wireframe")
    layout: Dict[str, Any] = Field(..., description="Layout structure (containers, rows, columns)")
    components: List[Dict[str, Any]] = Field(..., description="Flat list of components with ids/types/props")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class WireframeResponse(BaseModel):
    wireframe_spec: Dict[str, Any] = Field(default_factory=dict, description="Minimal wireframe specification")

# ---------------------- Helpers ----------------------

_KEYWORDS = {
    "login": ["login", "sign in", "signin"],
    "dashboard": ["dashboard", "overview", "home screen"],
    "list": ["list", "listing", "items"],
    "table": ["table", "grid"],
    "form": ["form", "input fields", "fields"],
    "button": ["button", "cta", "submit", "save"],
    "navbar": ["navbar", "navigation", "top bar", "menu"],
}

def _score_match(prompt_lc: str, synonyms: List[str]) -> float:
    """
    Very simple scoring: 1.0 for exact word match, 0.8 for substring presence, else 0.
    """
    for syn in synonyms:
        syn = syn.lower()
        # word boundary check
        if re.search(rf"\b{re.escape(syn)}\b", prompt_lc):
            return 1.0
        if syn in prompt_lc:
            return 0.8
    return 0.0

def _extract_intents_from_prompt(prompt: str) -> List[Intent]:
    prompt_lc = prompt.lower()
    intents: List[Intent] = []
    for intent_type, synonyms in _KEYWORDS.items():
        score = _score_match(prompt_lc, synonyms)
        if score > 0:
            intents.append(Intent(type=intent_type, value=None, confidence=round(score, 2)))
    # If nothing matched, add a generic 'unknown' with low confidence
    if not intents:
        intents.append(Intent(type="unknown", value=None, confidence=0.1))
    return intents

def _component_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def _spec_from_intents(intents: List[WireframeIntent]) -> Dict[str, Any]:
    """
    Deterministic wireframe spec based on intents.
    Layout:
      - Root container with rows/columns keyed off found intents.
    Components:
      - For each recognized intent, add a canonical component with type and minimal props.
    """
    recognized = {i.type for i in intents}
    wid = f"wf-{uuid.uuid4().hex[:8]}"

    layout = {
        "type": "container",
        "id": wid,
        "direction": "column",
        "children": [],
    }

    components: List[Dict[str, Any]] = []

    # Navbar row
    if "navbar" in recognized or "dashboard" in recognized:
        row_id = _component_id("row")
        layout["children"].append({
            "type": "row",
            "id": row_id,
            "children": [
                {"type": "column", "id": _component_id("col"), "span": 12, "children": ["navbar-1"]},
            ],
        })
        components.append({
            "id": "navbar-1",
            "type": "Navbar",
            "props": {"title": "App", "links": ["Home", "About", "Contact"]},
        })

    # Login form
    if "login" in recognized:
        row_id = _component_id("row")
        form_id = "form-1"
        btn_id = "button-1"
        layout["children"].append({
            "type": "row",
            "id": row_id,
            "children": [
                {"type": "column", "id": _component_id("col"), "span": 12, "children": [form_id, btn_id]},
            ],
        })
        components.append({
            "id": form_id,
            "type": "Form",
            "props": {
                "fields": [
                    {"id": "email", "label": "Email", "type": "email"},
                    {"id": "password", "label": "Password", "type": "password"},
                ]
            },
        })
        components.append({
            "id": btn_id,
            "type": "Button",
            "props": {"text": "Sign In", "variant": "primary"},
        })

    # List/table section
    if "table" in recognized or "list" in recognized or "dashboard" in recognized:
        row_id = _component_id("row")
        table_or_list_id = "table-1" if "table" in recognized or "dashboard" in recognized else "list-1"
        layout["children"].append({
            "type": "row",
            "id": row_id,
            "children": [
                {"type": "column", "id": _component_id("col"), "span": 12, "children": [table_or_list_id]},
            ],
        })
        if table_or_list_id.startswith("table"):
            components.append({
                "id": table_or_list_id,
                "type": "Table",
                "props": {
                    "columns": ["Name", "Status", "Updated"],
                    "rows": [],
                },
            })
        else:
            components.append({
                "id": table_or_list_id,
                "type": "List",
                "props": {
                    "items": [],
                    "itemProps": {"primaryKey": "title"},
                },
            })

    # Generic form if requested
    if "form" in recognized and "login" not in recognized:
        row_id = _component_id("row")
        form_id = "form-2"
        layout["children"].append({
            "type": "row",
            "id": row_id,
            "children": [
                {"type": "column", "id": _component_id("col"), "span": 12, "children": [form_id]},
            ],
        })
        components.append({
            "id": form_id,
            "type": "Form",
            "props": {
                "fields": [
                    {"id": "name", "label": "Name", "type": "text"},
                    {"id": "description", "label": "Description", "type": "textarea"},
                ]
            },
        })

    # Standalone button
    if "button" in recognized and "login" not in recognized:
        row_id = _component_id("row")
        btn_id = "button-2"
        layout["children"].append({
            "type": "row",
            "id": row_id,
            "children": [
                {"type": "column", "id": _component_id("col"), "span": 12, "children": [btn_id]},
            ],
        })
        components.append({
            "id": btn_id,
            "type": "Button",
            "props": {"text": "Submit", "variant": "secondary"},
        })

    # If nothing recognized, create an empty canvas
    if not layout["children"]:
        layout["children"].append({
            "type": "row",
            "id": _component_id("row"),
            "children": [{"type": "column", "id": _component_id("col"), "span": 12, "children": []}],
        })

    spec = {
        "id": wid,
        "layout": layout,
        "components": components,
        "metadata": {"generator": "rule-based", "version": "1.0.0"},
    }
    return spec

# ---------------------- Routes ----------------------

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
    description="Interpret a user prompt and return intents derived by keyword matching. "
                "Keywords: login, dashboard, list, table, form, button, navbar.",
    tags=["interpretation"]
)
def interpret_prompt(payload: PromptRequest, _: None = Depends(require_api_key)) -> InterpretResponse:
    """
    Interpret a user prompt and return intents with simple rule-based confidence scores.
    - Exact word match: 1.0
    - Substring match: 0.8
    - If no matches: an 'unknown' intent with 0.1 confidence is returned.

    Parameters:
    - payload: PromptRequest containing the 'prompt' string

    Returns:
    - InterpretResponse with a list of Intent items
    """
    intents = _extract_intents_from_prompt(payload.prompt)
    return InterpretResponse(intents=intents)

# PUBLIC_INTERFACE
@app.post(
    "/specify-wireframe",
    response_model=WireframeResponse,
    summary="Generate wireframe specification from intents",
    description="Convert intents into a deterministic WireframeSpec layout with containers, rows/columns, and components.",
    tags=["wireframe"]
)
def specify_wireframe(payload: WireframeRequest, _: None = Depends(require_api_key)) -> WireframeResponse:
    """
    Convert intents into a wireframe specification.

    Parameters:
    - payload: WireframeRequest containing a list of intents (type/value)

    Returns:
    - WireframeResponse containing 'wireframe_spec' JSON object. The object includes:
        - id: unique wireframe id
        - layout: nested container/row/column structure with child component ids
        - components: flat list of components with ids/types/props
        - metadata: generator and version info
    """
    spec = _spec_from_intents(payload.intents)
    return WireframeResponse(wireframe_spec=spec)
