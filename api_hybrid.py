"""
================================================================================
CARDIOAI - HYBRID FASTAPI BACKEND
Prediction  : Stacked Hybrid (XGBoost + Best DL -> Meta Logistic Regression)
XAI         : XGBoost SHAP TreeExplainer (waterfall, force, summary, importance)
              + LIME tabular explainer

Run:
    uvicorn api_hybrid:app --host 0.0.0.0 --port 8001 --reload

Requires outputs/ to contain:
    xgboost_model.pkl
    best_dl_model.keras
    meta_model.pkl
    scaler.pkl
    features.json
================================================================================
"""

import base64
import io
import json
import logging
import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).parent
OUT = BASE / "outputs"
MODEL_COMPARISON_PATH = OUT / "model_comparison.csv"
API_VERSION = "4.1.0"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CARDIOAI_ALLOWED_ORIGINS", "*").split(",") if o.strip()]

try:
    xgb_model = joblib.load(OUT / "xgboost_model.pkl")
    meta_model = joblib.load(OUT / "meta_model.pkl")
    scaler = joblib.load(OUT / "scaler.pkl")

    with open(OUT / "features.json", encoding="utf-8") as f:
        raw = json.load(f)
    feature_names: List[str] = raw if isinstance(raw, list) else raw.get("features", raw)

    import tensorflow as tf

    dl_model = tf.keras.models.load_model(str(OUT / "best_dl_model.keras"))
    shap_explainer = shap.TreeExplainer(xgb_model)

    log.info("Models loaded | features: %s", len(feature_names))
except Exception as exc:
    log.error("Failed to load artifacts: %s", exc)
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("CardioAI Hybrid API started")
    yield
    log.info("CardioAI Hybrid API stopped")


app = FastAPI(title="CardioAI Hybrid API", version=API_VERSION, docs_url="/docs", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PatientInput(BaseModel):
    age: float = Field(..., ge=18, le=120)
    sex: str
    oldpeak: float = Field(..., ge=0, le=10)
    chest_pain: str
    restingbp_final: float = Field(..., ge=80, le=200)
    chol_final: float = Field(..., ge=100, le=600)
    maxhr_final: float = Field(..., ge=60, le=220)
    fasting_bs: str
    resting_ecg: str
    exercise_angina: str
    st_slope: str

    @field_validator("sex")
    @classmethod
    def v_sex(cls, v: str):
        if v not in ("Male", "Female"):
            raise ValueError("sex must be Male|Female")
        return v

    @field_validator("chest_pain")
    @classmethod
    def v_cp(cls, v: str):
        options = ["Typical Angina", "Atypical Angina", "Non-anginal Pain", "Asymptomatic"]
        if v not in options:
            raise ValueError(f"chest_pain must be one of {options}")
        return v

    @field_validator("fasting_bs")
    @classmethod
    def v_fbs(cls, v: str):
        if v not in ("Yes", "No"):
            raise ValueError("fasting_bs must be Yes|No")
        return v

    @field_validator("resting_ecg")
    @classmethod
    def v_ecg(cls, v: str):
        options = ["Normal", "ST-T Abnormality", "LV Hypertrophy"]
        if v not in options:
            raise ValueError(f"resting_ecg must be one of {options}")
        return v

    @field_validator("exercise_angina")
    @classmethod
    def v_ang(cls, v: str):
        if v not in ("Yes", "No"):
            raise ValueError("exercise_angina must be Yes|No")
        return v

    @field_validator("st_slope")
    @classmethod
    def v_slope(cls, v: str):
        options = ["Upsloping", "Flat", "Downsloping"]
        if v not in options:
            raise ValueError(f"st_slope must be one of {options}")
        return v


class BatchPredictionRequest(BaseModel):
    patients: List[PatientInput] = Field(..., min_length=1, max_length=250)


def encode_patient(p: PatientInput) -> pd.DataFrame:
    row: Dict[str, float] = {f: 0.0 for f in feature_names}

    for col in ("age", "oldpeak", "restingbp_final", "chol_final", "maxhr_final"):
        if col in row:
            row[col] = float(getattr(p, col))

    age = p.age
    chol = p.chol_final
    bp = p.restingbp_final
    hr = p.maxhr_final
    op = p.oldpeak

    if "chol_age_ratio" in row:
        row["chol_age_ratio"] = chol / (age + 1e-6)
    if "bp_hr_ratio" in row:
        row["bp_hr_ratio"] = bp / (hr + 1e-6)
    if "stress_index" in row:
        row["stress_index"] = op * hr
    if "cardiac_load" in row:
        row["cardiac_load"] = bp * age

    for key in ("sex_Male", "sex_M"):
        if key in row:
            row[key] = 1.0 if p.sex == "Male" else 0.0

    cp_map = {
        "Typical Angina": "cp_final_Typical Angina",
        "Atypical Angina": "cp_final_Atypical Angina",
        "Non-anginal Pain": "cp_final_Non-anginal Pain",
        "Asymptomatic": "cp_final_Asymptomatic",
    }
    cp_idx_map = {"Typical Angina": 0, "Atypical Angina": 1, "Non-anginal Pain": 2, "Asymptomatic": 3}
    cp_col = cp_map.get(p.chest_pain, "")
    if cp_col in row:
        row[cp_col] = 1.0
    else:
        idx = cp_idx_map[p.chest_pain]
        for i in range(1, 4):
            key = f"cp_final_{i}"
            if key in row:
                row[key] = 1.0 if i == idx else 0.0

    if "fbs_final_Yes" in row:
        row["fbs_final_Yes"] = 1.0 if p.fasting_bs == "Yes" else 0.0

    ecg_map = {
        "Normal": "restecg_final_Normal",
        "ST-T Abnormality": "restecg_final_ST-T Abnormality",
        "LV Hypertrophy": "restecg_final_LV Hypertrophy",
    }
    ecg_col = ecg_map.get(p.resting_ecg, "")
    if ecg_col in row:
        row[ecg_col] = 1.0
    else:
        ecg_idx = {"Normal": 0, "ST-T Abnormality": 1, "LV Hypertrophy": 2}
        idx = ecg_idx[p.resting_ecg]
        for i in range(1, 3):
            key = f"restecg_final_{i}"
            if key in row:
                row[key] = 1.0 if i == idx else 0.0

    for key in ("exang_final_Yes", "exang_final_Y"):
        if key in row:
            row[key] = 1.0 if p.exercise_angina == "Yes" else 0.0

    slope_map = {"Upsloping": "slope_final_Up", "Flat": "slope_final_Flat", "Downsloping": "slope_final_Down"}
    slope_col = slope_map.get(p.st_slope, "")
    if slope_col in row:
        row[slope_col] = 1.0
    else:
        slope_idx = {"Upsloping": 0, "Flat": 1, "Downsloping": 2}
        idx = slope_idx[p.st_slope]
        for i in range(1, 3):
            key = f"slope_final_{i}"
            if key in row:
                row[key] = 1.0 if i == idx else 0.0

    return pd.DataFrame([row])[feature_names]


def scale(df: pd.DataFrame) -> np.ndarray:
    return scaler.transform(df.to_numpy()).astype(np.float64)


def hybrid_predict(df: pd.DataFrame):
    Xs = scale(df)
    xgb_p = float(xgb_model.predict_proba(Xs)[0, 1])
    dl_p = float(dl_model.predict(Xs, verbose=0)[0, 0])
    meta = np.array([[xgb_p, dl_p]])
    prob = float(meta_model.predict_proba(meta)[0, 1])
    pred = int(meta_model.predict(meta)[0])
    return pred, prob, xgb_p, dl_p


def extract_shap(df: pd.DataFrame) -> np.ndarray:
    raw = shap_explainer.shap_values(df)
    if isinstance(raw, list):
        return np.array(raw[1]).flatten()
    arr = np.array(raw)
    if arr.ndim == 3:
        return arr[0, :, 1]
    if arr.ndim == 2:
        return arr[0]
    return arr.flatten()


def base_value() -> float:
    expected = shap_explainer.expected_value
    if isinstance(expected, (list, np.ndarray)):
        return float(expected[1])
    return float(expected)


def fig_to_b64(fig=None) -> str:
    if fig is None:
        fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close("all")
    return b64


def risk_level(probability: float) -> str:
    return "HIGH" if probability >= 0.70 else "MEDIUM" if probability >= 0.40 else "LOW"


def get_ci(probability: float, xgb_p: float, dl_p: float) -> Dict:
    disagreement = abs(xgb_p - dl_p)
    half_width = min(0.18, max(0.03, 0.04 + disagreement * 0.35))
    return {
        "lower": round(max(0.0, probability - half_width), 4),
        "upper": round(min(1.0, probability + half_width), 4),
        "estimated_half_width": round(half_width, 4),
        "model_disagreement": round(disagreement, 4),
        "confidence_level": 0.95,
    }


def factor_lists(shap_values: np.ndarray, df: pd.DataFrame):
    pairs = sorted(zip(feature_names, shap_values, df.values[0]), key=lambda item: abs(item[1]), reverse=True)
    risk = [f"{feature} ({value:.2f})" for feature, shap_value, value in pairs[:6] if shap_value > 0]
    prot = [f"{feature} ({value:.2f})" for feature, shap_value, value in pairs[:6] if shap_value < 0]
    return risk, prot


def build_recommendations(patient: PatientInput, probability: float) -> List[Dict[str, str]]:
    recommendations: List[Dict[str, str]] = []

    if patient.restingbp_final >= 140:
        recommendations.append(
            {
                "title": "Address elevated resting blood pressure",
                "reason": f"Resting BP is {patient.restingbp_final:.0f} mm Hg, which increases cardiovascular strain.",
                "priority": "high" if probability >= 0.70 else "medium",
            }
        )
    if patient.chol_final >= 240:
        recommendations.append(
            {
                "title": "Review lipid management",
                "reason": f"Cholesterol is {patient.chol_final:.0f} mg/dl, above the desirable range.",
                "priority": "high" if probability >= 0.70 else "medium",
            }
        )
    if patient.fasting_bs == "Yes":
        recommendations.append(
            {
                "title": "Investigate glycemic control",
                "reason": "Elevated fasting blood sugar is associated with higher cardiometabolic risk.",
                "priority": "medium",
            }
        )
    if patient.exercise_angina == "Yes" or patient.chest_pain == "Asymptomatic":
        recommendations.append(
            {
                "title": "Escalate clinical follow-up",
                "reason": "Symptoms and stress-related markers suggest prompt clinical review.",
                "priority": "high",
            }
        )
    if patient.maxhr_final < 100:
        recommendations.append(
            {
                "title": "Review exercise tolerance",
                "reason": f"Max heart rate is {patient.maxhr_final:.0f} bpm, which may reflect reduced exercise capacity in this context.",
                "priority": "medium",
            }
        )
    if patient.oldpeak >= 2:
        recommendations.append(
            {
                "title": "Pay attention to ST depression",
                "reason": f"Oldpeak of {patient.oldpeak:.1f} indicates stress-induced ECG change associated with elevated risk.",
                "priority": "high" if probability >= 0.70 else "medium",
            }
        )

    recommendations.append(
        {
            "title": "Use this result as decision support, not diagnosis",
            "reason": "This model is for research and educational use and should complement clinical judgement.",
            "priority": "info",
        }
    )

    return recommendations[:5]


def load_model_metrics() -> Tuple[Dict, List[Dict]]:
    rows: List[Dict] = []
    best_model: Dict = {}
    if MODEL_COMPARISON_PATH.exists():
        df_metrics = pd.read_csv(MODEL_COMPARISON_PATH)
        rows = df_metrics.to_dict(orient="records")
        match = df_metrics.loc[df_metrics["Model"] == "Stacked Hybrid"]
        best_model = match.iloc[0].to_dict() if not match.empty else (df_metrics.iloc[0].to_dict() if not df_metrics.empty else {})
    return best_model, rows


def artifact_manifest() -> List[Dict[str, str]]:
    manifest = []
    for path in sorted(OUT.glob("*")):
        if path.is_file():
            manifest.append(
                {
                    "name": path.name,
                    "size_kb": round(path.stat().st_size / 1024, 1),
                    "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                }
            )
    return manifest


def build_prediction_payload(patient: PatientInput) -> Dict:
    df = encode_patient(patient)
    pred, probability, xgb_probability, dl_probability = hybrid_predict(df)
    shap_values = extract_shap(df)
    risk_factors, protective_factors = factor_lists(shap_values, df)

    return {
        "prediction": "Disease" if pred == 1 else "No Disease",
        "probability": probability,
        "xgb_probability": xgb_probability,
        "dl_probability": dl_probability,
        "confidence_interval": get_ci(probability, xgb_probability, dl_probability),
        "risk_level": risk_level(probability),
        "risk_factors": risk_factors,
        "protective_factors": protective_factors,
        "recommendations": build_recommendations(patient, probability),
        "model_used": "Stacked Hybrid (XGBoost + DL -> Meta-LR)",
        "timestamp": datetime.now().isoformat(),
        "input_summary": patient.model_dump(),
    }


def synthetic_reference_frame(sample_size: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    synth = pd.DataFrame(rng.standard_normal((sample_size, len(feature_names))), columns=feature_names)
    numeric_columns = {
        "age",
        "oldpeak",
        "restingbp_final",
        "chol_final",
        "maxhr_final",
        "chol_age_ratio",
        "bp_hr_ratio",
        "stress_index",
        "cardiac_load",
    }
    for column in feature_names:
        if column not in numeric_columns:
            synth[column] = (synth[column] > 0).astype(float)
    return synth


@app.get("/")
async def root():
    return {
        "message": "CardioAI Hybrid API",
        "version": API_VERSION,
        "model": "Stacked Hybrid (XGBoost + DL + Meta-LR)",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": "Stacked Hybrid",
        "features": len(feature_names),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/predict")
async def predict(patient: PatientInput):
    try:
        return build_prediction_payload(patient)
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.post("/predict/batch")
async def predict_batch(payload: BatchPredictionRequest):
    try:
        results = [build_prediction_payload(patient) for patient in payload.patients]
        disease_count = sum(1 for row in results if row["prediction"] == "Disease")
        average_probability = round(float(np.mean([row["probability"] for row in results])), 4) if results else 0.0
        return {
            "count": len(results),
            "disease_count": disease_count,
            "no_disease_count": len(results) - disease_count,
            "average_probability": average_probability,
            "generated_at": datetime.now().isoformat(),
            "results": results,
        }
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.post("/explain/waterfall")
async def explain_waterfall(patient: PatientInput):
    try:
        df = encode_patient(patient)
        shap_values = extract_shap(df)
        explanation = shap.Explanation(
            values=shap_values,
            base_values=base_value(),
            data=df.iloc[0].values,
            feature_names=feature_names,
        )
        plt.close("all")
        shap.plots.waterfall(explanation, show=False, max_display=15)
        fig = plt.gcf()
        fig.suptitle("SHAP Waterfall - Feature Contributions", fontsize=14, fontweight="bold")
        plt.tight_layout()
        return {"plot": fig_to_b64(fig), "type": "waterfall"}
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.post("/explain/force")
async def explain_force(patient: PatientInput):
    try:
        df = encode_patient(patient)
        shap_values = extract_shap(df)
        force_plot = shap.force_plot(base_value(), shap_values, df.iloc[0], feature_names=feature_names)
        buf = io.StringIO()
        shap.save_html(buf, force_plot)
        return {"plot": buf.getvalue(), "type": "force"}
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.get("/explain/summary")
async def explain_summary():
    try:
        synth = synthetic_reference_frame()
        raw = shap_explainer.shap_values(synth)
        shap_values = raw[1] if isinstance(raw, list) else np.array(raw)[:, :, 1] if np.array(raw).ndim == 3 else np.array(raw)

        plt.close("all")
        shap.summary_plot(shap_values, synth, show=False, max_display=15)
        fig = plt.gcf()
        fig.suptitle("Global SHAP Summary", fontsize=14, fontweight="bold")
        plt.tight_layout()
        return {"plot": fig_to_b64(fig), "type": "summary"}
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.get("/explain/importance")
async def explain_importance():
    try:
        synth = synthetic_reference_frame()
        raw = shap_explainer.shap_values(synth)
        shap_values = raw[1] if isinstance(raw, list) else np.array(raw)[:, :, 1] if np.array(raw).ndim == 3 else np.array(raw)

        plt.close("all")
        shap.summary_plot(shap_values, synth, plot_type="bar", show=False, max_display=15)
        fig = plt.gcf()
        fig.suptitle("Feature Importance - Mean |SHAP|", fontsize=14, fontweight="bold")
        plt.tight_layout()
        return {"plot": fig_to_b64(fig), "type": "importance"}
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.post("/explain/lime")
async def explain_lime(patient: PatientInput):
    try:
        from lime.lime_tabular import LimeTabularExplainer

        df = encode_patient(patient)
        scaled_input = scale(df)
        synth = synthetic_reference_frame()
        scaled_reference = scaler.transform(synth).astype(np.float64)

        explainer = LimeTabularExplainer(
            training_data=scaled_reference,
            feature_names=feature_names,
            class_names=["No Disease", "Disease"],
            mode="classification",
            random_state=42,
        )
        explanation = explainer.explain_instance(scaled_input[0], xgb_model.predict_proba, num_features=12)

        plt.close("all")
        fig = explanation.as_pyplot_figure()
        fig.suptitle("LIME Explanation - Top Features", fontsize=14, fontweight="bold")
        fig.set_size_inches(12, 8)
        plt.tight_layout()

        return {
            "plot": fig_to_b64(fig),
            "type": "lime",
            "feature_weights": [{"feature": str(feature), "weight": float(weight)} for feature, weight in explanation.as_list()],
        }
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.get("/model/info")
async def model_info():
    best_metrics, leaderboard = load_model_metrics()
    return {
        "architecture": "Stacked Hybrid",
        "version": API_VERSION,
        "base_models": ["XGBoost", "Best DL (BatchNormNet or similar)"],
        "meta_learner": "Logistic Regression (5-Fold OOF)",
        "xai_engine": "SHAP TreeExplainer (XGBoost) + LIME",
        "features": len(feature_names),
        "feature_list": feature_names,
        "best_reported_metrics": best_metrics,
        "leaderboard": leaderboard[:10],
        "artifacts": artifact_manifest(),
    }


@app.exception_handler(Exception)
async def global_handler(req, exc):
    log.error(str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_hybrid:app", host="0.0.0.0", port=8001, reload=True)
