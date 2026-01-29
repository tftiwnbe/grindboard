from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings

static_root = get_settings().app.static_root
index_file = static_root / "index.html"

router = APIRouter()

router.mount(
    "/_app",
    StaticFiles(directory=static_root, check_dir=False),
    name="web-assets",
)


@router.get("/manifest.webmanifest", include_in_schema=False)
async def serve_manifest() -> Response:
    """Serve PWA manifest with correct MIME type."""
    manifest_file = static_root / "manifest.webmanifest"
    if manifest_file.exists():
        return FileResponse(
            manifest_file,
            media_type="application/manifest+json",
        )
    raise HTTPException(status_code=404, detail="Manifest not found")


@router.get("/", include_in_schema=False, response_model=None)
async def serve_index() -> Response:
    """Serve the web single-page application entry point."""
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "GrindboardWeb"})


@router.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str) -> Response:
    """Serve static assets or fall back to the SPA entry point for client-side routing."""
    candidate = (static_root / full_path).resolve()

    # Security check: ensure path is within static_root
    try:
        candidate.relative_to(static_root)
    except ValueError:
        candidate = None

    # Serve the file if it exists
    if candidate and candidate.is_file():
        # Special handling for .webmanifest files
        if candidate.suffix == ".webmanifest":
            return FileResponse(candidate, media_type="application/manifest+json")
        return FileResponse(candidate)

    # Fall back to index.html for SPA routing
    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Not found")
