from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pydantic import BaseModel
import asyncio
import os
import joblib
import json
from pathlib import Path as pathlib_Path
from rdkit import Chem
from ddt.utility import FeatureGenerator
from tqdm import tqdm
import numpy as np
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


MODELS_DIR = pathlib_Path("models/files")
models = {}
models_info = {}


def load_model(model_name: str):
    return joblib.load(MODELS_DIR / model_name)


def load_single_model(model_name: str):
    model = app.state.model_loading_pool.submit(load_model, model_name)
    models[model_name] = model

    # Check if all the models are loaded
    if len(models) == len(os.listdir(MODELS_DIR)):
        logger.info("All models loaded")


def load_models_background(background_tasks: BackgroundTasks):
    # Read the best models
    with open("best_models.txt", "r") as f:
        best_models = f.read().splitlines()

    for model_name in best_models:
        background_tasks.add_task(load_single_model, model_name)


def load_models_info():
    with open("best_models.txt", "r") as f:
        best_models = f.read().splitlines()
    uniprots = [model_name[:6] for model_name in best_models]
    for uniprot in uniprots:
        with open(f"models/reports/{uniprot}_results.json", "r") as f:
            models_info[uniprot] = json.load(f)

    logger.info("All models info loaded")


@app.on_event("startup")
async def startup_event():
    app.state.model_loading_pool = ProcessPoolExecutor(max_workers=os.cpu_count())
    background_tasks = BackgroundTasks()
    background_tasks.add_task(load_models_background, background_tasks)
    background_tasks.add_task(load_models_info)
    # more tasks can be added

    await background_tasks()


@app.on_event("shutdown")
async def shutdown_event():
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
    results = {}
    cmpd_id, features = await get_features(input, input_type)
    cmpd_id = np.array(cmpd_id)
    for uniprot_id, model in tqdm(
        zip(models_info.keys(), models.values()), total=len(models)
    ):
        # np.float32 is not json serializable, take float64
        pred = model.result().predict_proba(features).astype(np.float64)[:, 1].round(2)
        mask = pred >= confidence_threshold
        for _id, _pred in zip(cmpd_id[mask], pred[mask]):
            # Create a dictionary for compound if not exists
            if _id not in results.keys():
                results[_id] = {}
            # Update the compound result dictionary
            results[_id].update({uniprot_id: _pred})
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
    return {"ping": "pong"}


@app.get("/ligandnet/api/v1/")
async def ligandnet_home():
    return {"message": "Welcome to LigandNet API"}


@app.get("/ligandnet/api/v1/models/{uniprot_id}")
async def ligandnet_model_info(uniprot_id: str = Depends(validate_uniprot_id)):
    return models_info[uniprot_id]


@app.post("/ligandnet/api/v1/predict/{smiles}")
async def ligandnet_predict(smiles: str = Depends(validate_smiles)):
    results = await get_prediction_async(smiles, "smiles")
    return {"predictions": results}


@app.post("/ligandnet/api/v1/predict/{uniprot_id}/{smiles}")
async def ligandnet_predict_by_model(
    uniprot_id: str = Depends(validate_uniprot_id),
    smiles: str = Depends(validate_smiles),
):
    results = await get_prediction_by_model(uniprot_id, smiles, "smiles")
    return {"predictions": results}
