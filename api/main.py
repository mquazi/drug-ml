from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Path
from concurrent.futures import ProcessPoolExecutor
from fastapi.responses import JSONResponse
from fastapi.param_functions import Body
from celery.result import AsyncResult
from celery_task_app.tasks import create_task, ligandnet_predict_celery
import os
import joblib
import json
from pathlib import Path as pathlib_Path
from rdkit import Chem
from ddt.utility import FeatureGenerator
from tqdm import tqdm
import numpy as np
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5000",
    "http://localhost:8000",
    "http://api:8000",
    "http://web:5000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger(__name__)


MODELS_DIR = pathlib_Path("models/files")
models = {}
models_info = {}
best_models_dict = {}
model_dict = {
    "xgb": "XGBoost",
    "rf": "Random Forest",
    "svc": "Support Vector Machine",
    "ann": "Artificial Neural Network",
}


def load_model(model_name: str):
    models[model_name[:6]] = joblib.load(MODELS_DIR / model_name)


def load_single_model(model_name: str):
    task = app.state.model_loading_pool.submit(load_model, model_name)
    models[model_name] = task.result()

    # Check if all the models are loaded
    if len(models) == len(os.listdir(MODELS_DIR)):
        logger.info("All models loaded")


def load_models_info(uniprots: list):
    def round_float_values(d):
        rounded_dict = {}
        for k, v in d.items():
            if isinstance(v, float):
                rounded_dict[k] = f"{v:.3f}"
            elif isinstance(v, dict):
                rounded_dict[k] = round_float_values(v)
            else:
                rounded_dict[k] = v
        return rounded_dict

    for uniprot in uniprots:
        with open(f"models/reports/{uniprot}_results.json", "r") as f:
            info = json.load(f)
        info = info[best_models_dict[uniprot]]
        info["model_type"] = "classification"
        info["model"] = model_dict[best_models_dict[uniprot]]
        model_info = {**info, **info["data_info"]}
        del model_info["data_info"]
        models_info[uniprot] = round_float_values(model_info)

    logger.info("All models info loaded")


@app.on_event("startup")
async def startup_event():
    app.state.model_loading_pool = ProcessPoolExecutor(max_workers=os.cpu_count())
    background_tasks = BackgroundTasks()

    # Read the best models
    with open("best_models.txt", "r") as f:
        best_models = f.read().splitlines()
    uniprots = []

    for model_name in best_models:
        uniprot, model_type = model_name.split(".")
        uniprots.append(uniprot)
        best_models_dict[uniprot] = model_type
        background_tasks.add_task(load_model, model_name)

    background_tasks.add_task(load_models_info, uniprots)
    # more tasks can be added
    await background_tasks()
    app.state.model_loading_pool.shutdown()


def validate_uniprot_id(uniprot_id: str = Path(..., title="Uniprot ID")):
    if uniprot_id not in models_info.keys():
        raise HTTPException(status_code=404, detail="Uniprot ID not found")
    return uniprot_id


def validate_smiles(smiles: str):
    try:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise ValueError("Invalid SMILES string")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    return smiles


async def get_features(input, input_type):
    ft = FeatureGenerator()
    if input_type == "smiles":
        ft.load_smiles(input)
    else:
        ft.load_sdf(input)
    cmpd_id, features = ft.extract_tpatf()
    return cmpd_id, features.reshape(-1, 2692)


async def get_prediction_async(input, input_type, confidence_threshold=0.5):
    results = []
    cmpd_id, features = await get_features(input, input_type)
    cmpd_id = np.array(cmpd_id)
    for uniprot_id, model in tqdm(
        zip(models_info.keys(), models.values()), total=len(models)
    ):
        # np.float32 is not json serializable, take float64
        pred = model.predict_proba(features).astype(np.float64)[:, 1].round(2)
        mask = pred >= confidence_threshold
        for _id, _pred in zip(cmpd_id[mask], pred[mask]):
            results.append({"uniprod_id": uniprot_id, "conf_score": _pred})
    return results


async def get_prediction_by_model(
    uniprot_id, input, input_type, confidence_threshold=0.5
):
    results = {}
    cmpd_id, features = await get_features(input, input_type)
    cmpd_id = np.array(cmpd_id)
    # find the matching key in models
    matched_key = [key for key in models.keys() if uniprot_id in key]
    if len(matched_key) == 0:
        raise HTTPException(status_code=404, detail="Requested model not found")
    model = models[matched_key[0]].result()
    pred = model.predict_proba(features).astype(np.float64)[:, 1].round(2)
    mask = pred >= confidence_threshold
    for _id, _pred in zip(cmpd_id[mask], pred[mask]):
        # Create a dictionary for compound if not exists
        if _id not in results.keys():
            results[_id] = {}
        # Update the compound result dictionary
        results[_id].update({uniprot_id: _pred})
    return results


@app.get("/")
async def root():
    return JSONResponse({"ping": "pong"})


@app.get("/ligandnet/api/v1/")
async def ligandnet_home():
    return JSONResponse({"message": "Welcome to LigandNet API"})


@app.get("/ligandnet/api/v1/models")
async def ligandnet_models():
    return JSONResponse(list(models_info.values()))


@app.get("/ligandnet/api/v1/models/{uniprot_id}")
async def ligandnet_model_info(uniprot_id: str = Depends(validate_uniprot_id)):
    return JSONResponse(models_info[uniprot_id])


@app.post("/ligandnet/api/v1/predict")
async def ligandnet_predict(smiles: str = Depends(validate_smiles)):
    results = await get_prediction_async(smiles, "smiles")
    return JSONResponse(results)


@app.post("/ligandnet/api/v1/predict/{uniprot_id}")
async def ligandnet_predict_by_model(
    uniprot_id: str = Depends(validate_uniprot_id),
    smiles: str = Depends(validate_smiles),
):
    results = await get_prediction_by_model(uniprot_id, smiles, "smiles")
    return JSONResponse(results)


@app.post("/tasks", status_code=201)
async def run_task(payload=Body(...)):
    task_type = payload["type"]
    task = create_task.delay(int(task_type))
    return JSONResponse({"task_id": task.id})


@app.get("/tasks/{task_id}")
async def get_status(task_id: str):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
    }
    return JSONResponse(result)


@app.get("/ligandnet/api/v1/tasks/predict/{smiles}")
async def run_prediction_task(smiles: str = Depends(validate_smiles)):
    task = ligandnet_predict_celery.delay(smiles, "smiles")
    return JSONResponse({"task_id": task.id})
