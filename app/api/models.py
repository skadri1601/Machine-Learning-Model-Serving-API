from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.auth import require_admin, get_current_active_user
from app.db.database import get_db
from app.db.models import MLModel, User
from app.models.model_loader import model_loader
from app.core.config import settings

router = APIRouter()


class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    framework: str
    description: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    models: List[ModelResponse]
    total: int


@router.get("", response_model=ModelListResponse)
async def list_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all available models."""
    models = db.query(MLModel).filter(MLModel.is_active == True).offset(skip).limit(limit).all()
    total = db.query(MLModel).filter(MLModel.is_active == True).count()

    return {"models": models, "total": total}


@router.get("/{model_name}", response_model=ModelResponse)
async def get_model(
    model_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get details of a specific model."""
    model = db.query(MLModel).filter(
        MLModel.name == model_name,
        MLModel.is_active == True
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return model


@router.post("/upload", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
    framework: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Upload a new model (admin only)."""

    # Check if model with same name already exists
    existing_model = db.query(MLModel).filter(MLModel.name == name).first()
    if existing_model:
        raise HTTPException(status_code=400, detail="Model with this name already exists")

    # Validate framework
    supported_frameworks = ["sklearn", "pickle"]
    if framework not in supported_frameworks:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported framework. Supported: {', '.join(supported_frameworks)}"
        )

    # Check file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.MAX_MODEL_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_MODEL_SIZE_MB}MB"
        )

    # Save file
    filename = f"{name}_v{version}_{file.filename}"
    try:
        file_path = model_loader.save_uploaded_model(content, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Create database record
    new_model = MLModel(
        name=name,
        version=version,
        framework=framework,
        file_path=file_path,
        description=description,
        uploaded_by=current_user.id
    )

    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    # Load model into memory
    try:
        model_loader.load_model(name, file_path, framework)
    except Exception as e:
        # Rollback database if model loading fails
        db.delete(new_model)
        db.commit()
        model_loader.delete_model_file(file_path)
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")

    return new_model


@router.delete("/{model_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a model (admin only)."""
    model = db.query(MLModel).filter(MLModel.name == model_name).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Soft delete (mark as inactive)
    model.is_active = False
    db.commit()

    # Unload from memory
    try:
        model_loader.unload_model(model_name)
    except:
        pass  # Model might not be loaded

    return None
