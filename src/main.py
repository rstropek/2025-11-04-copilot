from typing import Annotated
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import os
import re
import base64
import tempfile
import shutil
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Get the directory where main.py is located
BASE_DIR = Path(__file__).resolve().parent

# Global variable to store the system prompt
system_prompt: str = ""

# Global variable to store the dataset
df: pd.DataFrame = pd.DataFrame()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load configuration at startup and clean up at shutdown."""
    global system_prompt, df

    # Load system prompt from file
    prompt_path = BASE_DIR / "config" / "system_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = "No system prompt loaded"

    # Load prosthetics data
    data_path = BASE_DIR.parent / "data" / "prosthetics_data.csv"
    try:
        df = pd.read_csv(data_path)
        print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    except FileNotFoundError:
        print(f"Warning: Dataset not found at {data_path}")
        df = pd.DataFrame()

    yield

    # Cleanup (if needed)


# Create FastAPI app with lifespan
app: FastAPI = FastAPI(lifespan=lifespan)

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
    """Process a user prompt using OpenAI Responses API and execute generated Python code."""
    temp_dir: str = ""

    try:
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return HTMLResponse(content='<div class="error">OpenAI API key not configured</div>', status_code=500)

        client = OpenAI(api_key=api_key)

        # Call OpenAI Responses API
        try:
            response = client.responses.create(
                model="gpt-5",
                input=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_output_tokens=8192,
                reasoning={"effort": "minimal"},
                store=False,  # Don't store conversation history
            )

            # Extract the generated Python script
            python_script = response.output_text

        except Exception as e:
            return HTMLResponse(content=f'<div class="error">OpenAI API call failed: {str(e)}</div>', status_code=500)

        # Create temporary directory for script execution
        temp_dir = tempfile.mkdtemp()

        # Execute the Python script in the temporary directory
        original_dir = os.getcwd()
        try:
            # Change to temp directory
            os.chdir(temp_dir)

            # Basic sandboxing: restrict builtins but allow necessary imports
            restricted_globals = {
                "__builtins__": {
                    "open": open,
                    "print": print,
                    "range": range,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sorted": sorted,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "isinstance": isinstance,
                    "type": type,
                    "__import__": __import__,
                },
                "df": df.copy(),  # Provide a copy of the DataFrame to avoid accidental modifications
            }

            # Execute the script
            exec(python_script, restricted_globals)

            # Change back to original directory
            os.chdir(original_dir)

        except Exception as e:
            os.chdir(original_dir)
            return HTMLResponse(content=f'<div class="error">Script execution failed: {str(e)}</div>', status_code=500)

        # Read the generated HTML
        html_path = Path(temp_dir) / "index.html"
        if not html_path.exists():
            return HTMLResponse(content='<div class="error">Generated script did not create index.html</div>', status_code=500)

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Find all image references and embed them as base64
        img_pattern = re.compile(r'<img\s+[^>]*src="([^"]+)"[^>]*>', re.IGNORECASE)

        def replace_image(match: re.Match[str]) -> str:
            img_src = match.group(1)
            img_path = Path(temp_dir) / img_src

            if img_path.exists():
                with open(img_path, "rb") as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                    # Determine MIME type based on extension
                    ext = img_path.suffix.lower()
                    mime_type = "image/png" if ext == ".png" else "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/gif"
                    # Replace src with base64 data URL
                    return match.group(0).replace(f'src="{img_src}"', f'src="data:{mime_type};base64,{img_base64}"')
            return match.group(0)

        # Replace all image sources with base64
        html_content = img_pattern.sub(replace_image, html_content)

        return HTMLResponse(content=html_content)

    finally:
        # Clean up temporary directory
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
