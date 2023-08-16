from celery_task_app.worker import app
import time
from pathlib import Path
from celery.signals import celeryd_init
import joblib
import os
import logging
import json
from ddt.utility import FeatureGenerator
import numpy as np
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger(__name__)


MODELS_DIR = Path(os.environ["MODELS_DIR"])
models = {}
models_info = {}


def load_model(model_name: str):
    models[model_name[:6]] = joblib.load(MODELS_DIR / model_name)


def load_models_info(uniprots: list):
    for uniprot in uniprots:
        with open(f"models/reports/{uniprot}_results.json", "r") as f:
            models_info[uniprot] = json.load(f)


@celeryd_init.connect
def load_models(sender, conf, **kwargs):
    with open("best_models.txt", "r") as f:
        best_models = f.read().splitlines()
    uniprots = [model_name[:6] for model_name in best_models]

    for model_name in best_models:
        load_model(model_name)

    load_models_info(uniprots)
    logger.info("All models loaded")


def get_features(input, input_type):
    ft = FeatureGenerator()
    if input_type == "smiles":
        ft.load_smiles(input)
    else:
        ft.load_sdf(input)
    cmpd_id, features = ft.extract_tpatf()
    return cmpd_id, features.reshape(-1, 2692)


@app.task(name="ligandnet_predict_celery")
def ligandnet_predict_celery(input, input_type, confidence_threshold=0.5):
    results = {}
    cmpd_id, features = get_features(input, input_type)
    cmpd_id = np.array(cmpd_id)
    for uniprot_id, model in tqdm(
        zip(models_info.keys(), models.values()), total=len(models)
    ):
        # np.float32 is not json serializable, take float64
        pred = model.predict_proba(features).astype(np.float64)[:, 1].round(2)
        mask = pred >= confidence_threshold
        for _id, _pred in zip(cmpd_id[mask], pred[mask]):
            # Create a dictionary for compound if not exists
            if _id not in results.keys():
                results[_id] = {}
            # Update the compound result dictionary
            results[_id].update({uniprot_id: _pred})
    return results


@app.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True
