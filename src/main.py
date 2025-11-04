from typing import Annotated
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Get the directory where main.py is located
BASE_DIR = Path(__file__).resolve().parent

# Create FastAPI app
app: FastAPI = FastAPI()

# Configure Jinja2 templates
templates: Jinja2Templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Serve static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)  # type: ignore[misc]
async def get_index(request: Request) -> HTMLResponse:
    """Render the main page template."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask", response_class=HTMLResponse)  # type: ignore[misc]
async def post_ask(request: Request, prompt: Annotated[str, Form()]) -> HTMLResponse:
    """Process a user prompt. Currently returns placeholder Lorem Ipsum content."""
    # For now, return static Lorem Ipsum content
    lorem_ipsum = """
    <div class="ai-response">
        <h3>Response</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt 
        ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco 
        laboris nisi ut aliquip ex ea commodo consequat.</p>
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat 
        nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia 
        deserunt mollit anim id est laborum.</p>
    </div>
    """
    return HTMLResponse(content=lorem_ipsum)
