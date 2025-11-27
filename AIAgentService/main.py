import sys
import pathlib

# Ensure the ./src directory is on the Python path so 'api.main' can be imported
CURRENT_DIR = pathlib.Path(__file__).parent
SRC_DIR = CURRENT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

# Re-export app for uvicorn entrypoint: uvicorn main:app
from api.main import app as app  # noqa: F401
