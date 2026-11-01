from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from backend.app.config import settings
from .registry import Predictor
from .synthetic import FEATURES


class Inference(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    rows: list[dict[str, float]] = Field(min_length=2, max_length=2)


@asynccontextmanager
async def lifespan(app):
    try:
        app.state.predictor = Predictor(settings().model_dir)
    except (OSError, ValueError, KeyError):
        app.state.predictor = None
    yield


app = FastAPI(title="SGT-CDMX IA interna", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"loaded": app.state.predictor is not None}


@app.post("/predict")
def predict(body: Inference):
    if app.state.predictor is None:
        raise HTTPException(503, "No hay modelo promovido y verificado")
    if any(set(row) != set(FEATURES) for row in body.rows):
        raise HTTPException(422, "Atributos incompatibles")
    return {"flow_vpm": app.state.predictor.predict(body.rows),
            "metadata": app.state.predictor.metadata}
