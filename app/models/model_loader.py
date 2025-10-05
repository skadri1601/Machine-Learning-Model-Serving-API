import os
import pickle
import joblib
from typing import Any, Dict
from pathlib import Path

from app.core.config import settings


class ModelLoader:
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_storage_path = Path(settings.MODEL_STORAGE_PATH)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)

    def load_model(self, model_name: str, file_path: str, framework: str) -> Any:
        """Load a model from file based on framework."""
        full_path = self.model_storage_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"Model file not found: {full_path}")

        try:
            if framework == "sklearn":
                model = joblib.load(full_path)
            elif framework == "pickle":
                with open(full_path, "rb") as f:
                    model = pickle.load(f)
            # Add more frameworks as needed
            # elif framework == "tensorflow":
            #     import tensorflow as tf
            #     model = tf.keras.models.load_model(full_path)
            # elif framework == "pytorch":
            #     import torch
            #     model = torch.load(full_path)
            else:
                raise ValueError(f"Unsupported framework: {framework}")

            # Cache the model
            self.models[model_name] = model
            return model

        except Exception as e:
            raise Exception(f"Error loading model: {str(e)}")

    def get_model(self, model_name: str) -> Any:
        """Get a cached model or raise exception if not loaded."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not loaded. Please load it first.")
        return self.models[model_name]

    def unload_model(self, model_name: str):
        """Remove model from cache."""
        if model_name in self.models:
            del self.models[model_name]

    def predict(self, model_name: str, input_data: Any) -> Any:
        """Run prediction using cached model."""
        model = self.get_model(model_name)
        try:
            prediction = model.predict(input_data)
            return prediction
        except Exception as e:
            raise Exception(f"Prediction error: {str(e)}")

    def save_uploaded_model(self, file_content: bytes, filename: str) -> str:
        """Save uploaded model file to storage."""
        file_path = self.model_storage_path / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return filename

    def delete_model_file(self, file_path: str):
        """Delete model file from storage."""
        full_path = self.model_storage_path / file_path
        if full_path.exists():
            os.remove(full_path)


# Global model loader instance
model_loader = ModelLoader()
