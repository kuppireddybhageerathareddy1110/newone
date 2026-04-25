# CardioAI Hybrid

CardioAI Hybrid is a heart-disease risk assessment project built around a Python inference API and multiple frontend clients.

It currently includes:

- a FastAPI backend for prediction, explainability, batch scoring, and model metadata
- a React/Vite web app
- a Flutter client source scaffold for mobile/desktop/web follow-up
- a training pipeline that produces model artifacts and evaluation outputs

## Repository layout

- `api_hybrid.py`: FastAPI inference server
- `train_pipeline.py`: training and artifact generation pipeline
- `heart_disease.csv`: training dataset
- `outputs/`: saved model files, plots, and model comparison metrics
- `react-app/`: React web frontend
- `flutter-app/`: Flutter client source scaffold
- `requirements.txt`: backend Python dependencies

## What the app does

- single-patient heart-disease risk prediction
- stacked hybrid inference using XGBoost + deep learning + logistic meta model
- SHAP waterfall, force, summary, and importance views
- LIME local explanation
- batch scoring through a CSV-style workflow
- prediction history in the web client
- model details and feature glossary

## Prerequisites

### Backend

- Python 3.10+ recommended
- the trained files already present in `outputs/`

### React app

- Node.js 18+ recommended
- npm

### Flutter app

- Flutter SDK installed locally
- Android Studio / VS Code / suitable device tooling depending on your target platform

## Backend setup and run

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install backend dependencies

```powershell
pip install -r requirements.txt
```

### 3. Start the API server

```powershell
uvicorn api_hybrid:app --host 0.0.0.0 --port 8001 --reload
```

Once started, the backend will be available at:

- API root: `http://127.0.0.1:8001`
- Swagger docs: `http://127.0.0.1:8001/docs`

### Optional backend environment variables

- `CARDIOAI_ALLOWED_ORIGINS`
  Example:

```powershell
$env:CARDIOAI_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

Default is `*`.

## React web app setup and run

### 1. Open a second terminal

The backend should already be running on port `8001`.

### 2. Install frontend dependencies

```powershell
cd react-app
npm install
```

### 3. Start the React development server

```powershell
npm run dev
```

Vite will print a local URL, usually:

- `http://localhost:5173`

### Optional React environment variable

The web app defaults to `http://127.0.0.1:8001`.

If needed, create `react-app/.env` and set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8001
```

### React production build

```powershell
cd react-app
npm run build
```

## Flutter app setup and run

The Flutter app source is included, but this environment did not have the Flutter CLI installed, so native platform folders such as `android/`, `ios/`, `web/`, and `windows/` were not generated here.

### 1. Install Flutter locally

Confirm Flutter is available:

```powershell
flutter --version
```

### 2. Generate the missing Flutter project platform folders

```powershell
cd flutter-app
flutter create .
```

Important:

- keep the existing `lib/`, `pubspec.yaml`, and README content from this folder
- if Flutter asks whether to overwrite files, preserve the app source already in this repo

### 3. Fetch Flutter dependencies

```powershell
flutter pub get
```

### 4. Start the Flutter app

```powershell
flutter run
```

### Flutter backend URL

The default base URL is defined in:

- [cardio_api.dart](C:\Users\k bhageeratha reddy\Downloads\newoneheart\flutter-app\lib\services\cardio_api.dart)

Default value:

- Android emulator: `http://10.0.2.2:8001`

If you are using a physical device, iOS simulator, or desktop target, change the URL accordingly.

Examples:

- Android emulator: `http://10.0.2.2:8001`
- Windows desktop target talking to local backend: `http://127.0.0.1:8001`
- physical phone: `http://<your-local-ip>:8001`

## Typical local development workflow

### Web flow

1. Start backend:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn api_hybrid:app --host 0.0.0.0 --port 8001 --reload
```

2. Start React app in a second terminal:

```powershell
cd react-app
npm run dev
```

3. Open the local Vite URL in the browser.

### Flutter flow

1. Start backend:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn api_hybrid:app --host 0.0.0.0 --port 8001 --reload
```

2. Start Flutter app:

```powershell
cd flutter-app
flutter run
```

## API endpoints

Main endpoints currently exposed by the backend:

- `GET /`
- `GET /health`
- `POST /predict`
- `POST /predict/batch`
- `POST /explain/waterfall`
- `POST /explain/force`
- `GET /explain/summary`
- `GET /explain/importance`
- `POST /explain/lime`
- `GET /model/info`

Interactive API docs:

- `http://127.0.0.1:8001/docs`

## Retraining the model

If you want to regenerate model artifacts:

```powershell
.\.venv\Scripts\Activate.ps1
python train_pipeline.py
```

This writes artifacts back into `outputs/`.

## Outputs expected by the backend

The backend expects these files in `outputs/`:

- `xgboost_model.pkl`
- `best_dl_model.keras`
- `meta_model.pkl`
- `scaler.pkl`
- `features.json`

If any of these are missing, the backend will fail on startup.

## Troubleshooting

### Backend imports fail

Reinstall the requirements:

```powershell
pip install -r requirements.txt
```

### `shap` or TensorFlow errors

Those libraries are required by the backend. Use the same virtual environment used for the project.

### React app cannot reach backend

Check:

1. backend is running on port `8001`
2. `VITE_API_BASE_URL` points to the correct host
3. `CARDIOAI_ALLOWED_ORIGINS` is not blocking the frontend

### Flutter app cannot reach backend

Check:

1. the backend is running
2. the base URL in `flutter-app/lib/services/cardio_api.dart` matches your platform
3. for real devices, use your machine’s LAN IP, not `127.0.0.1`

### Flutter commands fail

That means Flutter is not installed correctly or not on PATH. Run:

```powershell
flutter doctor
```

## Notes and limitations

- This project is for research and educational use, not clinical diagnosis.
- Global SHAP and LIME views use synthetic reference samples because the original full training matrix is not persisted for live serving.
- The Flutter app is source-complete enough to continue development, but it still needs platform generation through Flutter CLI before it can run.
