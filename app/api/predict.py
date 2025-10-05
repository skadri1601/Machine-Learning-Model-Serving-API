from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Any, Optional
import time
import json
import numpy as np
import pandas as pd

from app.core.auth import get_current_active_user
from app.db.database import get_db
from app.db.models import MLModel, User, Prediction
from app.models.model_loader import model_loader

router = APIRouter()


class PredictRequest(BaseModel):
    data: List[List[float]]  # 2D array of features


class PredictResponse(BaseModel):
    model_name: str
    predictions: List[Any]
    latency: float


class BatchPredictResponse(BaseModel):
    model_name: str
    total_predictions: int
    predictions: List[Any]
    latency: float


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    model_name: str = Query(..., description="Name of the model to use"),
    version: Optional[str] = Query(None, description="Model version (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Run real-time prediction on input data."""

    # Get model from database
    query = db.query(MLModel).filter(
        MLModel.name == model_name,
        MLModel.is_active == True
    )
    if version:
        query = query.filter(MLModel.version == version)

    db_model = query.first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Convert input to numpy array
    try:
        input_array = np.array(request.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")

    # Run prediction
    start_time = time.time()
    try:
        predictions = model_loader.predict(model_name, input_array)
        predictions_list = predictions.tolist() if hasattr(predictions, 'tolist') else list(predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    latency = time.time() - start_time

    # Log prediction to database
    prediction_record = Prediction(
        model_id=db_model.id,
        user_id=current_user.id,
        input_data=json.dumps(request.data),
        output_data=json.dumps(predictions_list),
        latency=latency
    )
    db.add(prediction_record)
    db.commit()

    return {
        "model_name": model_name,
        "predictions": predictions_list,
        "latency": latency
    }


@router.post("/batch_predict", response_model=BatchPredictResponse)
async def batch_predict(
    file: UploadFile = File(...),
    model_name: str = Query(..., description="Name of the model to use"),
    version: Optional[str] = Query(None, description="Model version (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Run batch predictions from uploaded CSV file."""

    # Get model from database
    query = db.query(MLModel).filter(
        MLModel.name == model_name,
        MLModel.is_active == True
    )
    if version:
        query = query.filter(MLModel.version == version)

    db_model = query.first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Read CSV file
    try:
        content = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

    # Run batch prediction
    start_time = time.time()
    try:
        predictions = model_loader.predict(model_name, df.values)
        predictions_list = predictions.tolist() if hasattr(predictions, 'tolist') else list(predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    latency = time.time() - start_time

    # Log batch prediction
    prediction_record = Prediction(
        model_id=db_model.id,
        user_id=current_user.id,
        input_data=f"Batch file: {file.filename} ({len(df)} rows)",
        output_data=json.dumps(predictions_list),
        latency=latency
    )
    db.add(prediction_record)
    db.commit()

    return {
        "model_name": model_name,
        "total_predictions": len(predictions_list),
        "predictions": predictions_list,
        "latency": latency
    }


@router.get("/metrics")
async def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get usage metrics and statistics."""

    total_predictions = db.query(Prediction).count()
    total_models = db.query(MLModel).filter(MLModel.is_active == True).count()

    # Average latency
    avg_latency = db.query(Prediction).with_entities(
        db.func.avg(Prediction.latency)
    ).scalar() or 0

    # Predictions by model
    predictions_by_model = db.query(
        MLModel.name,
        db.func.count(Prediction.id).label('count')
    ).join(Prediction).group_by(MLModel.name).all()

    return {
        "total_predictions": total_predictions,
        "total_active_models": total_models,
        "average_latency_seconds": round(avg_latency, 4),
        "predictions_by_model": [
            {"model": name, "count": count} for name, count in predictions_by_model
        ]
    }
