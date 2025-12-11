
import sys
import traceback
from fastapi.openapi.utils import get_openapi
from app.main import app

try:
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    print("OpenAPI schema generated successfully.")
except Exception:
    traceback.print_exc()
