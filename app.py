import sys
import os
import certifi

from dotenv import load_dotenv
load_dotenv()

mongo_db_url = os.getenv("MONGODB_URL_KEY")

import pymongo
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from fastapi.templating import Jinja2Templates

ca = certifi.where()
client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="./templates")

@app.get("/")
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train_route():
    return {"message": "Training disabled in production"}

@app.post("/predict")
async def predict_route(request: Request, file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)

        preprocesor = load_object("final_model/preprocessor.pkl")
        model = load_object("final_model/model.pkl")

        network_model = NetworkModel(preprocessor=preprocesor, model=model)

        y_pred = network_model.predict(df)

        df['predicted_column'] = y_pred
        df.to_csv('prediction_output/output.csv')

        table_html = df.to_html(classes='table table-striped')

        return templates.TemplateResponse(
            "table.html",
            {"request": request, "table": table_html}
        )

    except Exception as e:
        raise NetworkSecurityException(e, sys)

if __name__ == "__main__":
    app_run(app, host="0.0.0.0", port=8080)