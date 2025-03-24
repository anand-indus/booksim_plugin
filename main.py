from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from booksim_engine import select_config_from_prompt, customize_config, run_simulation

from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import yaml
import os

app = FastAPI()

# === Plugin Routes ===

@app.get("/openapi.yaml", response_class=PlainTextResponse)
def serve_openapi_yaml():
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="OpenAPI schema for Booksim plugin",
        routes=app.routes,
    )
    return yaml.dump(openapi_schema, sort_keys=False)

@app.get("/logo.png")
def get_logo():
    return FileResponse("logo.png")

@app.get("/legal")
def get_legal():
    return {"message": "Use of this plugin is subject to the MIT License."}

# Serve plugin manifest folder
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

# === API Models ===

class ConfigRequest(BaseModel):
    prompt: str

class CustomizationRequest(BaseModel):
    config_path: str
    updates: dict

class SimulationRequest(BaseModel):
    config_path: str

# === Endpoints ===

@app.post("/select-config")
def select_config(req: ConfigRequest):
    try:
        config_path, metadata = select_config_from_prompt(req.prompt)
        return {"config_path": config_path, "metadata": metadata}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/customize-config")
def customize_config_endpoint(req: CustomizationRequest):
    temp_path = customize_config(req.config_path, req.updates)
    return {"temp_config_path": temp_path}

@app.post("/simulate")
def simulate(req: SimulationRequest):
    result = run_simulation(req.config_path)
    return result



