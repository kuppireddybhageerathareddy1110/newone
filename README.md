# CardioAI Hybrid

CardioAI Hybrid is a heart-disease risk assessment project with:

- A FastAPI backend for hybrid inference and explainability
- A React/Vite frontend for single-patient, batch, history, and explainability workflows
- A training pipeline that produces saved model artifacts and evaluation plots

## Project structure

- `api_hybrid.py`: FastAPI inference API
- `train_pipeline.py`: end-to-end training and artifact generation
- `heart_disease.csv`: training dataset
- `outputs/`: trained models, plots, and comparison metrics
- `react-app/`: Vite frontend

## Backend setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api_hybrid:app --host 0.0.0.0 --port 8001 --reload
```

Optional environment variable:

- `CARDIOAI_ALLOWED_ORIGINS`: comma-separated CORS origin list. Default is `*`.

## Frontend setup

```bash
cd react-app
npm install
npm run dev
```

Optional environment variable:

- `VITE_API_BASE_URL`: backend base URL. Default is `http://127.0.0.1:8001`.

## Current frontend capabilities

- Single-patient risk assessment
- SHAP waterfall, force, global summary, and feature importance views
- LIME local explanation
- Personalized follow-up recommendations from the prediction response
- Local browser history for recent assessments
- Batch assessment from pasted CSV
- Dynamic model metadata page backed by the API

## Notes

- The project is positioned as research and educational software, not clinical decision software.
- Explainability endpoints use synthetic reference data for global SHAP/LIME views because the original training matrix is not persisted separately in the repo.
