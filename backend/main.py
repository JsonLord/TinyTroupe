from fastapi import FastAPI
from contextlib import asynccontextmanager
import gradio as gr
import logging

from backend.routers.api import router
from backend.gradio_app import create_gradio_app
from backend.services.git_sync import git_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up...")
    git_sync.startup_pull()
    yield
    # Shutdown
    logger.info("Application shutting down...")

app = FastAPI(title="UserSync Backend", lifespan=lifespan)

# Mount API routes
app.include_router(router)

# Mount Gradio Application
gradio_app = create_gradio_app()
app = gr.mount_gradio_app(app, gradio_app, path="/gradio")

@app.get("/")
def root():
    return {"message": "Welcome to UserSync API"}
