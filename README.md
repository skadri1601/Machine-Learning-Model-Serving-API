# Machine Learning Model Serving API

A scalable, secure RESTful API for serving machine learning models (real-time & batch predictions).

## Features
- 🚀 **Real-time & Batch Predictions** - Single and bulk prediction endpoints
- 📦 **Model Management** - Upload, list, version, and delete ML models
- 🔐 **JWT Authentication** - Secure user registration and login
- 📊 **Usage Metrics** - Track predictions, latency, and model performance
- 🐳 **Docker Ready** - Fully containerized with docker-compose
- 🧪 **Tested** - Comprehensive test suite with pytest

## Tech Stack
- **Framework**: FastAPI (async, high-performance)
- **ML Support**: scikit-learn, joblib (extensible to TensorFlow/PyTorch)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Auth**: JWT tokens with bcrypt password hashing
- **Monitoring**: Prometheus metrics
- **Testing**: pytest with test database
- **Deployment**: Docker & docker-compose

## Project Structure
```
ml-model-api/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/                 # API endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── models.py        # Model management endpoints
│   │   └── predict.py       # Prediction endpoints
│   ├── core/                # Core utilities
│   │   ├── auth.py          # Auth logic (JWT, password hashing)
│   │   └── config.py        # Configuration settings
│   ├── db/                  # Database layer
│   │   ├── database.py      # DB connection
│   │   └── models.py        # SQLAlchemy models
│   └── models/              # ML model logic
│       └── model_loader.py  # Model loading & inference
├── tests/                   # Test suite
│   └── test_api.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Getting Started

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Machine-Learning-Model-Serving-API
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your DATABASE_URL and SECRET_KEY
   ```

5. **Run the API**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Option 2: Docker Deployment

1. **Using docker-compose** (recommended)
   ```bash
   docker-compose up --build
   ```
   This starts both the API and PostgreSQL database.

2. **Using Docker only**
   ```bash
   docker build -t ml-model-api .
   docker run -p 8000:8000 ml-model-api
   ```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Model Management
- `GET /models` - List all available models
- `GET /models/{model_name}` - Get specific model details
- `POST /models/upload` - Upload new model (admin only)
- `DELETE /models/{model_name}` - Delete model (admin only)

### Predictions
- `POST /predict` - Single/real-time prediction
- `POST /batch_predict` - Batch predictions from CSV file
- `GET /metrics` - Usage statistics and metrics

### System
- `GET /health` - Health check
- `GET /` - API info

## Usage Examples

### 1. Register & Login
```bash
# Register
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123"
  }'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -d "username=johndoe&password=securepass123"

# Response: {"access_token": "...", "token_type": "bearer"}
```

### 2. Upload Model (Admin)
```bash
curl -X POST "http://localhost:8000/models/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@model.pkl" \
  -F "name=my_classifier" \
  -F "version=1.0" \
  -F "framework=sklearn" \
  -F "description=My trained model"
```

### 3. Make Predictions
```bash
# Single prediction
curl -X POST "http://localhost:8000/predict?model_name=my_classifier" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [[5.1, 3.5, 1.4, 0.2]]
  }'

# Batch prediction
curl -X POST "http://localhost:8000/batch_predict?model_name=my_classifier" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@data.csv"
```

### 4. Get Metrics
```bash
curl -X GET "http://localhost:8000/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## Configuration

Create a `.env` file (see `.env.example`):

```env
# Application
APP_NAME=ML Model Serving API
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mlapi

# Model Storage
MODEL_STORAGE_PATH=./models
MAX_MODEL_SIZE_MB=500
```

## Database Schema

- **users**: User accounts with auth info
- **ml_models**: Model metadata (name, version, framework, file path)
- **predictions**: Prediction logs with input/output and latency

## Security Features

- JWT token-based authentication
- Bcrypt password hashing
- Role-based access control (admin vs regular user)
- Request timing middleware
- CORS configuration
- Input validation with Pydantic

## Monitoring & Metrics

The `/metrics` endpoint provides:
- Total predictions count
- Active models count
- Average prediction latency
- Predictions per model breakdown

Prometheus metrics available at `/metrics` (if enabled).

## Extending the API

### Adding New ML Frameworks

Edit `app/models/model_loader.py` to support TensorFlow, PyTorch, or ONNX:

```python
elif framework == "tensorflow":
    import tensorflow as tf
    model = tf.keras.models.load_model(full_path)
elif framework == "pytorch":
    import torch
    model = torch.load(full_path)
```

## License
MIT
