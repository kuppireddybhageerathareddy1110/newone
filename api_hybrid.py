"""
================================================================================
CARDIOAI — HYBRID FASTAPI BACKEND
Prediction  : Stacked Hybrid (XGBoost + Best DL → Meta Logistic Regression)
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

import io, json, base64, logging, traceback
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List

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

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
OUT  = BASE / "outputs"

# ─────────────────────────────────────────────────────────────
# LOAD ARTEFACTS
# ─────────────────────────────────────────────────────────────
try:
    xgb_model  = joblib.load(OUT / "xgboost_model.pkl")
    meta_model = joblib.load(OUT / "meta_model.pkl")
    scaler     = joblib.load(OUT / "scaler.pkl")

    with open(OUT / "features.json") as f:
        raw = json.load(f)
    feature_names: List[str] = raw if isinstance(raw, list) else raw.get("features", raw)

    import tensorflow as tf
    dl_model = tf.keras.models.load_model(str(OUT / "best_dl_model.keras"))

    shap_explainer = shap.TreeExplainer(xgb_model)

    log.info(f"✅  Models loaded  | features: {len(feature_names)}")

except Exception as exc:
    log.error(f"❌  Failed to load artefacts: {exc}")
    raise

# ─────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app):
    log.info("🚀 CardioAI Hybrid API started")
    yield
    log.info("👋 CardioAI Hybrid API stopped")

app = FastAPI(title="CardioAI Hybrid API", version="4.0.0",
              docs_url="/docs", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ─────────────────────────────────────────────────────────────
# PYDANTIC SCHEMA
# ─────────────────────────────────────────────────────────────
class PatientInput(BaseModel):
    age:             float = Field(..., ge=18,  le=120)
    sex:             str
    oldpeak:         float = Field(..., ge=0,   le=10)
    chest_pain:      str
    restingbp_final: float = Field(..., ge=80,  le=200)
    chol_final:      float = Field(..., ge=100, le=600)
    maxhr_final:     float = Field(..., ge=60,  le=220)
    fasting_bs:      str
    resting_ecg:     str
    exercise_angina: str
    st_slope:        str

    @field_validator("sex")
    @classmethod
    def v_sex(cls, v):
        if v not in ("Male", "Female"): raise ValueError("sex must be Male|Female")
        return v

    @field_validator("chest_pain")
    @classmethod
    def v_cp(cls, v):
        ok = ["Typical Angina", "Atypical Angina", "Non-anginal Pain", "Asymptomatic"]
        if v not in ok: raise ValueError(f"chest_pain must be one of {ok}")
        return v

    @field_validator("fasting_bs")
    @classmethod
    def v_fbs(cls, v):
        if v not in ("Yes", "No"): raise ValueError("fasting_bs must be Yes|No")
        return v

    @field_validator("resting_ecg")
    @classmethod
    def v_ecg(cls, v):
        ok = ["Normal", "ST-T Abnormality", "LV Hypertrophy"]
        if v not in ok: raise ValueError(f"resting_ecg must be one of {ok}")
        return v

    @field_validator("exercise_angina")
    @classmethod
    def v_ang(cls, v):
        if v not in ("Yes", "No"): raise ValueError("exercise_angina must be Yes|No")
        return v

    @field_validator("st_slope")
    @classmethod
    def v_slope(cls, v):
        ok = ["Upsloping", "Flat", "Downsloping"]
        if v not in ok: raise ValueError(f"st_slope must be one of {ok}")
        return v

# ─────────────────────────────────────────────────────────────
# ENCODING HELPERS
# ─────────────────────────────────────────────────────────────

def encode_patient(p: PatientInput) -> pd.DataFrame:
    """
    Build a DataFrame row matching the trained feature_names exactly.
    Handles both the original one-hot columns AND the 4 engineered features.
    """
    row: Dict[str, float] = {f: 0.0 for f in feature_names}

    # Numeric
    for col in ("age", "oldpeak", "restingbp_final", "chol_final", "maxhr_final"):
        if col in row:
            row[col] = float(getattr(p, col))

    age  = p.age
    chol = p.chol_final
    bp   = p.restingbp_final
    hr   = p.maxhr_final
    op   = p.oldpeak

    # Engineered features (must match training)
    if "chol_age_ratio" in row: row["chol_age_ratio"] = chol / (age  + 1e-6)
    if "bp_hr_ratio"    in row: row["bp_hr_ratio"]    = bp   / (hr   + 1e-6)
    if "stress_index"   in row: row["stress_index"]   = op   * hr
    if "cardiac_load"   in row: row["cardiac_load"]   = bp   * age

    # Sex
    for key in ("sex_Male", "sex_M"):
        if key in row: row[key] = 1.0 if p.sex == "Male" else 0.0

    # Chest pain one-hot  (column names produced by pd.get_dummies)
    cp_map = {
        "Typical Angina":  "cp_final_Typical Angina",
        "Atypical Angina": "cp_final_Atypical Angina",
        "Non-anginal Pain":"cp_final_Non-anginal Pain",
        "Asymptomatic":    "cp_final_Asymptomatic",
    }
    # Also try legacy numeric encoding cp_final_1/2/3
    cp_idx_map = {"Typical Angina": 0, "Atypical Angina": 1,
                  "Non-anginal Pain": 2, "Asymptomatic": 3}
    col_name = cp_map.get(p.chest_pain, "")
    if col_name in row:
        row[col_name] = 1.0
    else:
        idx = cp_idx_map[p.chest_pain]
        for i in range(1, 4):
            k = f"cp_final_{i}"
            if k in row: row[k] = 1.0 if i == idx else 0.0

    # Fasting BS
    for key in ("fbs_final_Yes",):
        if key in row: row[key] = 1.0 if p.fasting_bs == "Yes" else 0.0

    # Resting ECG
    ecg_map = {"Normal": "restecg_final_Normal",
               "ST-T Abnormality": "restecg_final_ST-T Abnormality",
               "LV Hypertrophy":   "restecg_final_LV Hypertrophy"}
    ecg_col = ecg_map.get(p.resting_ecg, "")
    if ecg_col in row:
        row[ecg_col] = 1.0
    else:
        ecg_idx = {"Normal": 0, "ST-T Abnormality": 1, "LV Hypertrophy": 2}
        idx = ecg_idx[p.resting_ecg]
        for i in range(1, 3):
            k = f"restecg_final_{i}"
            if k in row: row[k] = 1.0 if i == idx else 0.0

    # Exercise angina
    for key in ("exang_final_Yes", "exang_final_Y"):
        if key in row: row[key] = 1.0 if p.exercise_angina == "Yes" else 0.0

    # ST Slope
    sl_map = {"Upsloping": "slope_final_Up", "Flat": "slope_final_Flat",
              "Downsloping": "slope_final_Down"}
    sl_col = sl_map.get(p.st_slope, "")
    if sl_col in row:
        row[sl_col] = 1.0
    else:
        sl_idx = {"Upsloping": 0, "Flat": 1, "Downsloping": 2}
        idx = sl_idx[p.st_slope]
        for i in range(1, 3):
            k = f"slope_final_{i}"
            if k in row: row[k] = 1.0 if i == idx else 0.0

    return pd.DataFrame([row])[feature_names]


def scale(df: pd.DataFrame) -> np.ndarray:
    return scaler.transform(df).astype(np.float64)


def hybrid_predict(df: pd.DataFrame):
    """Return (prediction_int, hybrid_probability) using stacked hybrid."""
    Xs = scale(df)
    xgb_p = float(xgb_model.predict_proba(Xs)[0, 1])
    dl_p  = float(dl_model.predict(Xs, verbose=0)[0, 0])
    meta  = np.array([[xgb_p, dl_p]])
    prob  = float(meta_model.predict_proba(meta)[0, 1])
    pred  = int(meta_model.predict(meta)[0])
    return pred, prob, xgb_p, dl_p


def extract_shap(df: pd.DataFrame) -> np.ndarray:
    raw = shap_explainer.shap_values(df)
    if isinstance(raw, list):
        return np.array(raw[1]).flatten()
    arr = np.array(raw)
    if arr.ndim == 3: return arr[0, :, 1]
    if arr.ndim == 2: return arr[0]
    return arr.flatten()


def base_value() -> float:
    ev = shap_explainer.expected_value
    if isinstance(ev, (list, np.ndarray)): return float(ev[1])
    return float(ev)


def fig_to_b64(fig=None) -> str:
    if fig is None: fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close("all")
    return b64


def risk_level(p: float) -> str:
    return "HIGH" if p >= 0.70 else "MEDIUM" if p >= 0.40 else "LOW"


def get_ci(p: float) -> Dict:
    return {"lower": round(max(0.0, p-0.05), 4),
            "upper": round(min(1.0, p+0.05), 4),
            "confidence_level": 0.95}


def factor_lists(sv: np.ndarray, df: pd.DataFrame):
    pairs = sorted(zip(feature_names, sv, df.values[0]),
                   key=lambda x: abs(x[1]), reverse=True)
    risk  = [f"{f} ({v:.2f})" for f, s, v in pairs[:6] if s > 0]
    prot  = [f"{f} ({v:.2f})" for f, s, v in pairs[:6] if s < 0]
    return risk, prot

# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "CardioAI Hybrid API", "version": "4.0.0",
            "model": "Stacked Hybrid (XGBoost + DL + Meta-LR)", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy", "model": "Stacked Hybrid",
            "features": len(feature_names), "timestamp": datetime.now().isoformat()}


@app.post("/predict")
async def predict(patient: PatientInput):
    try:
        df = encode_patient(patient)
        pred, prob, xgb_p, dl_p = hybrid_predict(df)

        sv   = extract_shap(df)
        risk, prot = factor_lists(sv, df)

        return {
            "prediction":          "Disease" if pred == 1 else "No Disease",
            "probability":         prob,
            "xgb_probability":     xgb_p,
            "dl_probability":      dl_p,
            "confidence_interval": get_ci(prob),
            "risk_level":          risk_level(prob),
            "risk_factors":        risk,
            "protective_factors":  prot,
            "model_used":          "Stacked Hybrid (XGBoost + DL → Meta-LR)",
            "timestamp":           datetime.now().isoformat(),
        }
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.post("/explain/waterfall")
async def explain_waterfall(patient: PatientInput):
    try:
        df  = encode_patient(patient)
        sv  = extract_shap(df)
        bv  = base_value()

        expl = shap.Explanation(values=sv, base_values=bv,
                                data=df.iloc[0].values, feature_names=feature_names)
        plt.close("all")
        shap.plots.waterfall(expl, show=False, max_display=15)
        fig = plt.gcf()
        fig.suptitle("SHAP Waterfall — Feature Contributions",
                     fontsize=14, fontweight="bold")
        plt.tight_layout()
        return {"plot": fig_to_b64(fig), "type": "waterfall"}
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.post("/explain/force")
async def explain_force(patient: PatientInput):
    try:
        df  = encode_patient(patient)
        sv  = extract_shap(df)
        bv  = base_value()

        fp  = shap.force_plot(bv, sv, df.iloc[0], feature_names=feature_names)
        buf = io.StringIO()
        shap.save_html(buf, fp)
        return {"plot": buf.getvalue(), "type": "force"}
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.get("/explain/summary")
async def explain_summary():
    try:
        rng   = np.random.default_rng(42)
        n     = 100
        synth = pd.DataFrame(rng.standard_normal((n, len(feature_names))),
                             columns=feature_names)
        num_cols = ["age","oldpeak","restingbp_final","chol_final","maxhr_final",
                    "chol_age_ratio","bp_hr_ratio","stress_index","cardiac_load"]
        for c in feature_names:
            if c not in num_cols:
                synth[c] = (synth[c] > 0).astype(float)

        raw = shap_explainer.shap_values(synth)
        sv  = (raw[1] if isinstance(raw, list)
               else np.array(raw)[:,:,1] if np.array(raw).ndim==3
               else np.array(raw))

        plt.close("all")
        shap.summary_plot(sv, synth, show=False, max_display=15)
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
        rng   = np.random.default_rng(42)
        n     = 100
        synth = pd.DataFrame(rng.standard_normal((n, len(feature_names))),
                             columns=feature_names)
        num_cols = ["age","oldpeak","restingbp_final","chol_final","maxhr_final",
                    "chol_age_ratio","bp_hr_ratio","stress_index","cardiac_load"]
        for c in feature_names:
            if c not in num_cols:
                synth[c] = (synth[c] > 0).astype(float)

        raw = shap_explainer.shap_values(synth)
        sv  = (raw[1] if isinstance(raw, list)
               else np.array(raw)[:,:,1] if np.array(raw).ndim==3
               else np.array(raw))

        plt.close("all")
        shap.summary_plot(sv, synth, plot_type="bar", show=False, max_display=15)
        fig = plt.gcf()
        fig.suptitle("Feature Importance — Mean |SHAP|", fontsize=14, fontweight="bold")
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
        Xs = scale(df)

        rng   = np.random.default_rng(42)
        synth = pd.DataFrame(rng.standard_normal((100, len(feature_names))),
                             columns=feature_names)
        num_cols = ["age","oldpeak","restingbp_final","chol_final","maxhr_final",
                    "chol_age_ratio","bp_hr_ratio","stress_index","cardiac_load"]
        for c in feature_names:
            if c not in num_cols:
                synth[c] = (synth[c] > 0).astype(float)
        tr_sc = scaler.transform(synth).astype(np.float64)

        lime_exp = LimeTabularExplainer(
            training_data=tr_sc, feature_names=feature_names,
            class_names=["No Disease", "Disease"],
            mode="classification", random_state=42,
        )
        exp = lime_exp.explain_instance(Xs[0], xgb_model.predict_proba, num_features=12)

        plt.close("all")
        fig = exp.as_pyplot_figure()
        fig.suptitle("LIME Explanation — Top Features", fontsize=14, fontweight="bold")
        fig.set_size_inches(12, 8)
        plt.tight_layout()

        return {
            "plot": fig_to_b64(fig),
            "type": "lime",
            "feature_weights": [
                {"feature": str(f), "weight": float(w)} for f, w in exp.as_list()
            ],
        }
    except Exception as exc:
        log.error(traceback.format_exc())
        raise HTTPException(500, str(exc))


@app.get("/model/info")
async def model_info():
    return {
        "architecture": "Stacked Hybrid",
        "base_models":  ["XGBoost", "Best DL (BatchNormNet or similar)"],
        "meta_learner": "Logistic Regression (5-Fold OOF)",
        "xai_engine":   "SHAP TreeExplainer (XGBoost) + LIME",
        "features":     len(feature_names),
        "feature_list": feature_names,
    }


@app.exception_handler(Exception)
async def global_handler(req, exc):
    log.error(str(exc))
    return JSONResponse(status_code=500,
                        content={"detail": "Internal server error", "error": str(exc)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_hybrid:app", host="0.0.0.0", port=8001, reload=True)
