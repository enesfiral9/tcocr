import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import APP_NAME, BASE_DIR
from app.ocr.paddle_service import PaddleOCRService
from app.api import health, scan, export, cleanup


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.scan_lock = asyncio.Lock()
    app.state.ocr = PaddleOCRService()
    await asyncio.to_thread(app.state.ocr.initialize)
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)


@app.middleware("http")
async def disable_frontend_cache(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


for module in (health, scan, export, cleanup):
    app.include_router(module.router)
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(BASE_DIR / "frontend" / "index.html")


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT)
