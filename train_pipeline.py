"""
================================================================================
HEART DISEASE PREDICTION — HYBRID TRAINING PIPELINE
Architecture: Dataset → Preprocess → Feature Engineering → 80/20 Split
              → 10 Classical ML + 10 DL → Hybrid Ensemble (Stacked + Weighted)
              → XAI (SHAP + LIME) → Save best models for FastAPI deployment

Run:
    python train_pipeline.py

Outputs (saved to outputs/):
    xgboost_model.pkl     ← best classical ML (used for SHAP)
    best_dl_model.keras   ← best deep learning model
    meta_model.pkl        ← stacked hybrid meta-learner (Logistic Regression)
    scaler.pkl            ← StandardScaler fitted on training data
    features.json         ← ordered feature list (19 features + 4 engineered)
    dl_feature_names.json ← same feature list (for DL prediction fn)
    outputs/*.png         ← 20+ visualisation plots
    outputs/model_comparison.csv
================================================================================
"""

import os, json, warnings
warnings.filterwarnings("ignore")
os.makedirs("outputs", exist_ok=True)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import shap
import lime.lime_tabular

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier,
    AdaBoostClassifier, ExtraTreesClassifier
)
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, auc, precision_recall_curve
)
from xgboost import XGBClassifier

import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import (
    Dense, Dropout, BatchNormalization, Input, Add
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

np.random.seed(42)
tf.random.set_seed(42)
plt.style.use("seaborn-v0_8-darkgrid")

# ─────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("1. LOADING DATA")
print("=" * 70)

df = pd.read_csv("heart_disease.csv")
print(f"   Shape: {df.shape}")
print(f"   Columns: {df.columns.tolist()}")
print(f"   Target distribution:\n{df['target_final'].value_counts()}")

# ─────────────────────────────────────────────────────────────
# 2. PREPROCESSING & FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("2. PREPROCESSING & FEATURE ENGINEERING")
print("=" * 70)

TARGET = "target_final"
y = df[TARGET].values
X_raw = df.drop(columns=[TARGET])

# ── One-hot encode categorical columns ──────────────────────
# Adjust the categorical column names to match YOUR CSV exactly
CAT_COLS = ["sex", "cp_final", "fbs_final", "restecg_final",
            "exang_final", "slope_final"]
existing_cats = [c for c in CAT_COLS if c in X_raw.columns]
X_encoded = pd.get_dummies(X_raw, columns=existing_cats, drop_first=False)

# ── Engineered features ─────────────────────────────────────
def add_engineered_features(df_in: pd.DataFrame) -> pd.DataFrame:
    df_out = df_in.copy()
    age  = df_out.get("age",  pd.Series(np.ones(len(df_out)) * 50))
    chol = df_out.get("chol_final", df_out.get("chol", pd.Series(np.ones(len(df_out)) * 200)))
    bp   = df_out.get("restingbp_final", df_out.get("trestbps", pd.Series(np.ones(len(df_out)) * 120)))
    hr   = df_out.get("maxhr_final", df_out.get("thalach", pd.Series(np.ones(len(df_out)) * 150)))
    op   = df_out.get("oldpeak", pd.Series(np.zeros(len(df_out))))

    df_out["chol_age_ratio"] = chol / (age + 1e-6)
    df_out["bp_hr_ratio"]    = bp   / (hr  + 1e-6)
    df_out["stress_index"]   = op   * hr
    df_out["cardiac_load"]   = bp   * age
    return df_out

X_feat = add_engineered_features(X_encoded)
X_feat = X_feat.fillna(X_feat.mean(numeric_only=True))

feature_names = X_feat.columns.tolist()
print(f"   Total features: {len(feature_names)}")
print(f"   Engineered features added: chol_age_ratio, bp_hr_ratio, stress_index, cardiac_load")

# ── Save feature list ────────────────────────────────────────
with open("outputs/features.json", "w") as f:
    json.dump(feature_names, f, indent=2)
print(f"   Feature names saved → outputs/features.json")

# ─────────────────────────────────────────────────────────────
# 3. TRAIN / TEST SPLIT  (80 / 20, stratified)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("3. TRAIN / TEST SPLIT")
print("=" * 70)

X_np = X_feat.values.astype(np.float32)
X_train, X_test, y_train, y_test = train_test_split(
    X_np, y, test_size=0.20, random_state=42, stratify=y
)
print(f"   Train: {X_train.shape[0]} samples  |  Test: {X_test.shape[0]} samples")

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

joblib.dump(scaler, "outputs/scaler.pkl")
print("   Scaler saved → outputs/scaler.pkl")

# ─────────────────────────────────────────────────────────────
# 4. CLASSICAL ML MODELS (10 algorithms)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("4. CLASSICAL ML MODELS")
print("=" * 70)

ml_defs = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Decision Tree":       DecisionTreeClassifier(random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=200, random_state=42),
    "Gradient Boosting":   GradientBoostingClassifier(n_estimators=200, random_state=42),
    "XGBoost":             XGBClassifier(n_estimators=200, learning_rate=0.05,
                                         max_depth=6, use_label_encoder=False,
                                         eval_metric="logloss", random_state=42),
    "AdaBoost":            AdaBoostClassifier(n_estimators=200, random_state=42),
    "Extra Trees":         ExtraTreesClassifier(n_estimators=200, random_state=42),
    "SVM (RBF)":           SVC(kernel="rbf", probability=True, random_state=42),
    "K-NN":                KNeighborsClassifier(n_neighbors=7),
    "Naive Bayes":         GaussianNB(),
}

ml_results, ml_trained = [], {}
for name, mdl in ml_defs.items():
    mdl.fit(X_train_sc, y_train)
    yp    = mdl.predict(X_test_sc)
    yprob = mdl.predict_proba(X_test_sc)[:, 1]
    ml_results.append({
        "Model": name, "Category": "Classical ML",
        "Accuracy":  round(accuracy_score(y_test, yp), 4),
        "Precision": round(precision_score(y_test, yp, zero_division=0), 4),
        "Recall":    round(recall_score(y_test, yp, zero_division=0), 4),
        "F1":        round(f1_score(y_test, yp, zero_division=0), 4),
        "ROC-AUC":   round(roc_auc_score(y_test, yprob), 4),
    })
    ml_trained[name] = mdl
    print(f"   {name:<25} Acc={ml_results[-1]['Accuracy']:.4f}  F1={ml_results[-1]['F1']:.4f}")

ml_df = pd.DataFrame(ml_results).sort_values("Accuracy", ascending=False).reset_index(drop=True)

# Save XGBoost (best tree model for SHAP)
joblib.dump(ml_trained["XGBoost"], "outputs/xgboost_model.pkl")
print("\n   XGBoost saved → outputs/xgboost_model.pkl")

# ─────────────────────────────────────────────────────────────
# 5. DEEP LEARNING MODELS (10 architectures)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("5. DEEP LEARNING MODELS")
print("=" * 70)

D = X_train_sc.shape[1]  # input dimension

def _compile(m):
    m.compile(optimizer=Adam(1e-3), loss="binary_crossentropy", metrics=["accuracy"])
    return m

def build_ann(d):
    return _compile(Sequential([
        Dense(64, "relu", input_shape=(d,)), Dense(32, "relu"), Dense(16, "relu"),
        Dense(1, "sigmoid")], name="ANN"))

def build_deep_ann(d):
    return _compile(Sequential([
        Dense(128, "relu", input_shape=(d,)), Dense(64, "relu"),
        Dense(32, "relu"), Dense(16, "relu"), Dense(8, "relu"),
        Dense(1, "sigmoid")], name="DeepANN"))

def build_dropout(d):
    return _compile(Sequential([
        Dense(128, "relu", input_shape=(d,)), Dropout(0.3),
        Dense(64, "relu"), Dropout(0.3),
        Dense(32, "relu"), Dropout(0.2),
        Dense(1, "sigmoid")], name="DropoutNet"))

def build_batchnorm(d):
    return _compile(Sequential([
        Dense(128, "relu", input_shape=(d,)), BatchNormalization(),
        Dense(64, "relu"),  BatchNormalization(),
        Dense(32, "relu"),  BatchNormalization(),
        Dense(1, "sigmoid")], name="BatchNormNet"))

def build_combined(d):
    return _compile(Sequential([
        Dense(128, "relu", input_shape=(d,)), BatchNormalization(), Dropout(0.3),
        Dense(64, "relu"),  BatchNormalization(), Dropout(0.3),
        Dense(32, "relu"),  BatchNormalization(),
        Dense(1, "sigmoid")], name="CombinedNet"))

def build_wide(d):
    inp = Input((d,)); x = Dense(256, "relu")(inp)
    x = Dense(128, "relu")(x); x = Dense(64, "relu")(x)
    out = Dense(1, "sigmoid")(x)
    return _compile(Model(inp, out, name="WideNet"))

def build_narrow(d):
    return _compile(Sequential([
        Dense(32, "relu", input_shape=(d,)), Dense(16, "relu"), Dense(8, "relu"),
        Dense(1, "sigmoid")], name="NarrowNet"))

def build_very_deep(d):
    return _compile(Sequential([
        Dense(64, "relu", input_shape=(d,)),
        *[Dense(64, "relu") for _ in range(6)],
        Dense(1, "sigmoid")], name="VeryDeepNet"))

def build_high_dropout(d):
    return _compile(Sequential([
        Dense(256, "relu", input_shape=(d,)), Dropout(0.5),
        Dense(128, "relu"), Dropout(0.4),
        Dense(64, "relu"),  Dropout(0.3),
        Dense(32, "relu"),  Dropout(0.2),
        Dense(1, "sigmoid")], name="HighDropout"))

def build_residual(d):
    inp = Input((d,)); x = Dense(64, "relu")(inp)
    r = Dense(64, "relu")(x); r = Dense(64, "relu")(r); x = Add()([x, r])
    r2 = Dense(64, "relu")(x); r2 = Dense(64, "relu")(r2); x = Add()([x, r2])
    out = Dense(1, "sigmoid")(x)
    return _compile(Model(inp, out, name="ResidualNet"))

dl_builders = {
    "ANN": build_ann, "DeepANN": build_deep_ann, "DropoutNet": build_dropout,
    "BatchNormNet": build_batchnorm, "CombinedNet": build_combined,
    "WideNet": build_wide, "NarrowNet": build_narrow, "VeryDeepNet": build_very_deep,
    "HighDropout": build_high_dropout, "ResidualNet": build_residual,
}

callbacks = [
    EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True),
    ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6),
]

dl_results, dl_trained, dl_histories = [], {}, {}
for name, builder in dl_builders.items():
    mdl = builder(D)
    hist = mdl.fit(X_train_sc, y_train, validation_split=0.2,
                   epochs=100, batch_size=32, callbacks=callbacks, verbose=0)
    yprob = mdl.predict(X_test_sc, verbose=0).flatten()
    yp    = (yprob > 0.5).astype(int)
    dl_results.append({
        "Model": name, "Category": "Deep Learning",
        "Accuracy":  round(accuracy_score(y_test, yp), 4),
        "Precision": round(precision_score(y_test, yp, zero_division=0), 4),
        "Recall":    round(recall_score(y_test, yp, zero_division=0), 4),
        "F1":        round(f1_score(y_test, yp, zero_division=0), 4),
        "ROC-AUC":   round(roc_auc_score(y_test, yprob), 4),
    })
    dl_trained[name] = mdl
    dl_histories[name] = hist
    print(f"   {name:<20} Acc={dl_results[-1]['Accuracy']:.4f}  F1={dl_results[-1]['F1']:.4f}")

dl_df = pd.DataFrame(dl_results).sort_values("Accuracy", ascending=False).reset_index(drop=True)
best_dl_name = dl_df.iloc[0]["Model"]
best_dl_model = dl_trained[best_dl_name]
best_dl_model.save("outputs/best_dl_model.keras")
print(f"\n   Best DL: {best_dl_name} saved → outputs/best_dl_model.keras")

# ─────────────────────────────────────────────────────────────
# 6. HYBRID ENSEMBLE (Weighted Avg + Stacked Meta-LR)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("6. HYBRID ENSEMBLE CONSTRUCTION")
print("=" * 70)

xgb_model  = ml_trained["XGBoost"]
xgb_tr_p   = xgb_model.predict_proba(X_train_sc)[:, 1]
xgb_te_p   = xgb_model.predict_proba(X_test_sc)[:, 1]
dl_tr_p    = best_dl_model.predict(X_train_sc, verbose=0).flatten()
dl_te_p    = best_dl_model.predict(X_test_sc,  verbose=0).flatten()

# 6a. Weighted average  (0.6 × XGB + 0.4 × DL)
wa_te_p    = 0.6 * xgb_te_p + 0.4 * dl_te_p
wa_te_pred = (wa_te_p > 0.5).astype(int)

# 6b. Stacked Hybrid  — 5-Fold OOF meta-features ─────────────
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
meta_train = np.zeros((len(X_train_sc), 2))  # [xgb_oof, dl_oof]

for fold, (tr_idx, val_idx) in enumerate(skf.split(X_train_sc, y_train)):
    Xf_tr, Xf_val = X_train_sc[tr_idx], X_train_sc[val_idx]
    yf_tr         = y_train[tr_idx]

    # XGBoost OOF
    xgb_f = XGBClassifier(n_estimators=200, learning_rate=0.05, max_depth=6,
                           use_label_encoder=False, eval_metric="logloss", random_state=42)
    xgb_f.fit(Xf_tr, yf_tr)
    meta_train[val_idx, 0] = xgb_f.predict_proba(Xf_val)[:, 1]

    # DL OOF
    dl_f = build_batchnorm(D)
    dl_f.fit(Xf_tr, yf_tr, epochs=60, batch_size=32,
             callbacks=callbacks, verbose=0, validation_split=0.1)
    meta_train[val_idx, 1] = dl_f.predict(Xf_val, verbose=0).flatten()
    print(f"   Fold {fold+1}/5 done")

meta_test = np.column_stack([xgb_te_p, dl_te_p])

meta_lr = LogisticRegression(C=1.0, random_state=42)
meta_lr.fit(meta_train, y_train)
stack_te_p    = meta_lr.predict_proba(meta_test)[:, 1]
stack_te_pred = meta_lr.predict(meta_test)

joblib.dump(meta_lr, "outputs/meta_model.pkl")
print("\n   Meta Logistic Regression saved → outputs/meta_model.pkl")

# Evaluate ensemble strategies
ens_rows = []
for tag, probs, preds in [
    ("XGBoost Only",     xgb_te_p,    (xgb_te_p  > 0.5).astype(int)),
    (f"DL Only ({best_dl_name})", dl_te_p, (dl_te_p > 0.5).astype(int)),
    ("Weighted Average", wa_te_p,     wa_te_pred),
    ("Stacked Hybrid",   stack_te_p,  stack_te_pred),
]:
    ens_rows.append({
        "Model": tag, "Category": "Hybrid Ensemble",
        "Accuracy":  round(accuracy_score(y_test, preds), 4),
        "Precision": round(precision_score(y_test, preds, zero_division=0), 4),
        "Recall":    round(recall_score(y_test, preds, zero_division=0), 4),
        "F1":        round(f1_score(y_test, preds, zero_division=0), 4),
        "ROC-AUC":   round(roc_auc_score(y_test, probs), 4),
    })
    print(f"   {tag:<25} Acc={ens_rows[-1]['Accuracy']:.4f}  F1={ens_rows[-1]['F1']:.4f}")

ens_df = pd.DataFrame(ens_rows)

# ─────────────────────────────────────────────────────────────
# 7. COMBINED COMPARISON & SAVE CSV
# ─────────────────────────────────────────────────────────────
all_df = pd.concat([ml_df, dl_df, ens_df], ignore_index=True)
all_df.sort_values("Accuracy", ascending=False, inplace=True)
all_df.reset_index(drop=True, inplace=True)
all_df.to_csv("outputs/model_comparison.csv", index=False)
print("\n   Full comparison saved → outputs/model_comparison.csv")
print(all_df[["Model", "Category", "Accuracy", "F1", "ROC-AUC"]].to_string(index=False))

# ─────────────────────────────────────────────────────────────
# 8. VISUALISATIONS
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("8. GENERATING VISUALISATIONS")
print("=" * 70)

def savefig(name):
    plt.tight_layout()
    plt.savefig(f"outputs/{name}", dpi=150, bbox_inches="tight")
    plt.close("all")
    print(f"   Saved → outputs/{name}")

# ── Plot 1: Target distribution ──────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
pd.Series(y).value_counts().plot(kind="bar", ax=axes[0], color=["#3498db", "#e74c3c"])
axes[0].set_title("Target Distribution"); axes[0].set_xticklabels(["No Disease", "Disease"], rotation=0)
pd.Series(y).value_counts().plot(kind="pie", ax=axes[1], autopct="%1.1f%%",
                                  colors=["#3498db", "#e74c3c"], labels=["No Disease", "Disease"])
axes[1].set_ylabel("")
savefig("01_target_distribution.png")

# ── Plot 2: ML model comparison ───────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
ml_sorted = ml_df.sort_values("Accuracy")
ax.barh(ml_sorted["Model"], ml_sorted["Accuracy"], color="#3498db")
ax.set_xlabel("Accuracy"); ax.set_title("Classical ML — Accuracy Comparison")
ax.set_xlim([0, 1])
savefig("02_ml_accuracy.png")

# ── Plot 3: DL model comparison ───────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
dl_sorted = dl_df.sort_values("Accuracy")
ax.barh(dl_sorted["Model"], dl_sorted["Accuracy"], color="#9b59b6")
ax.set_xlabel("Accuracy"); ax.set_title("Deep Learning — Accuracy Comparison")
ax.set_xlim([0, 1])
savefig("03_dl_accuracy.png")

# ── Plot 4: DL training curves (best model) ───────────────────
hist_data = dl_histories[best_dl_name].history
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(hist_data["loss"], label="Train"); axes[0].plot(hist_data["val_loss"], label="Val")
axes[0].set_title(f"Loss — {best_dl_name}"); axes[0].legend()
axes[1].plot(hist_data["accuracy"], label="Train"); axes[1].plot(hist_data["val_accuracy"], label="Val")
axes[1].set_title(f"Accuracy — {best_dl_name}"); axes[1].legend()
savefig("04_dl_training_curves.png")

# ── Plot 5: Hybrid ensemble comparison ───────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
ens_sorted = ens_df.sort_values("Accuracy")
colors = ["#2ecc71" if "Stacked" in m else "#f39c12" for m in ens_sorted["Model"]]
ax.barh(ens_sorted["Model"], ens_sorted["Accuracy"], color=colors)
ax.set_xlabel("Accuracy"); ax.set_title("Hybrid Ensemble Strategies")
ax.set_xlim([0, 1])
savefig("05_ensemble_comparison.png")

# ── Plot 6: All models top-15 ────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 8))
top15 = all_df.head(15)
cat_colors = {"Classical ML": "#3498db", "Deep Learning": "#9b59b6", "Hybrid Ensemble": "#2ecc71"}
bar_colors = [cat_colors[c] for c in top15["Category"]]
ax.barh(top15["Model"][::-1], top15["Accuracy"][::-1], color=bar_colors[::-1])
ax.set_xlabel("Accuracy"); ax.set_title("Top 15 Models — All Categories")
ax.set_xlim([0, 1])
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=v, label=k) for k, v in cat_colors.items()], loc="lower right")
savefig("06_all_models_top15.png")

# ── Plot 7: Confusion matrix — Stacked Hybrid ────────────────
cm = confusion_matrix(y_test, stack_te_pred)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
            xticklabels=["No Disease", "Disease"], yticklabels=["No Disease", "Disease"])
ax.set_title("Confusion Matrix — Stacked Hybrid")
ax.set_xlabel("Predicted"); ax.set_ylabel("True")
savefig("07_confusion_matrix_hybrid.png")

# ── Plot 8: ROC curve — Stacked Hybrid ───────────────────────
fpr, tpr, _ = roc_curve(y_test, stack_te_p)
roc_auc_val = auc(fpr, tpr)
fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(fpr, tpr, lw=2, label=f"Stacked Hybrid (AUC={roc_auc_val:.3f})", color="#e74c3c")
ax.plot([0,1],[0,1],"k--"); ax.set_xlabel("FPR"); ax.set_ylabel("TPR")
ax.set_title("ROC Curve — Stacked Hybrid"); ax.legend()
savefig("08_roc_curve_hybrid.png")

# ── Plot 9: Precision-Recall — Stacked Hybrid ────────────────
prec_arr, rec_arr, _ = precision_recall_curve(y_test, stack_te_p)
fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(rec_arr, prec_arr, lw=2, color="#3498db")
ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
ax.set_title("Precision-Recall Curve — Stacked Hybrid")
savefig("09_pr_curve_hybrid.png")

# ── Plot 10: Correlation heatmap ──────────────────────────────
X_df = pd.DataFrame(X_feat.values if hasattr(X_feat, "values") else X_feat,
                    columns=feature_names)
fig, ax = plt.subplots(figsize=(14, 12))
sns.heatmap(X_df.corr(), cmap="coolwarm", center=0, ax=ax, cbar_kws={"label": "Correlation"})
ax.set_title("Feature Correlation Matrix")
savefig("10_correlation_heatmap.png")

# ─────────────────────────────────────────────────────────────
# 9. SHAP ANALYSIS (XGBoost for TreeExplainer)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("9. SHAP ANALYSIS")
print("=" * 70)
X_test_df = pd.DataFrame(X_test, columns=feature_names)

explainer = shap.TreeExplainer(xgb_model)
shap_raw = explainer.shap_values(X_test_df)


# Handle multi-output SHAP
if isinstance(shap_raw, list):
    sv = shap_raw[1]
elif np.array(shap_raw).ndim == 3:
    sv = np.array(shap_raw)[:, :, 1]
else:
    sv = np.array(shap_raw)

base_val = explainer.expected_value
if isinstance(base_val, (list, np.ndarray)):
    base_val = float(base_val[1])

# Plot 11: SHAP Summary (beeswarm)
plt.figure(figsize=(12, 8))
shap.summary_plot(sv, X_test_df, show=False, max_display=15)
plt.title("SHAP Summary Plot (Beeswarm)", fontsize=14, fontweight="bold")
savefig("11_shap_summary_beeswarm.png")

# Plot 12: SHAP Feature Importance (bar)
plt.figure(figsize=(10, 7))
shap.summary_plot(sv, X_test_df, plot_type="bar", show=False, max_display=15)
plt.title("SHAP Feature Importance", fontsize=14, fontweight="bold")
savefig("12_shap_feature_importance.png")

# Plot 13: SHAP Waterfall (first test sample)
expl_obj = shap.Explanation(
    values=sv[0], base_values=base_val,
    data=X_test_df.iloc[0].values, feature_names=feature_names
)
plt.figure(figsize=(12, 8))
shap.plots.waterfall(expl_obj, show=False, max_display=15)
plt.title("SHAP Waterfall — Sample 1", fontsize=14, fontweight="bold")
savefig("13_shap_waterfall_sample1.png")

# Plot 14: SHAP Force plot (saved as HTML)
force_plot = shap.force_plot(base_val, sv[0], X_test_df.iloc[0],
                              feature_names=feature_names)
import io
buf = io.StringIO()
shap.save_html(buf, force_plot)
with open("outputs/14_shap_force_sample1.html", "w", encoding="utf-8") as f:
    f.write(buf.getvalue())
print("   Saved → outputs/14_shap_force_sample1.html")

# ─────────────────────────────────────────────────────────────
# 10. LIME ANALYSIS
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("10. LIME ANALYSIS")
print("=" * 70)

lime_exp = lime.lime_tabular.LimeTabularExplainer(
    training_data=X_train_sc,
    feature_names=feature_names,
    class_names=["No Disease", "Disease"],
    mode="classification",
    random_state=42,
)

for i in range(3):
    exp = lime_exp.explain_instance(X_test_sc[i], xgb_model.predict_proba, num_features=12)
    fig = exp.as_pyplot_figure()
    plt.title(f"LIME Explanation — Sample {i+1}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"outputs/15_lime_sample_{i+1}.png", dpi=150, bbox_inches="tight")
    plt.close("all")
    print(f"   Saved → outputs/15_lime_sample_{i+1}.png")

# ─────────────────────────────────────────────────────────────
# DONE
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("✅  PIPELINE COMPLETE")
print("=" * 70)
print("""
Saved files in outputs/:
  ├── xgboost_model.pkl      ← for SHAP + prediction base model
  ├── best_dl_model.keras    ← best DL model
  ├── meta_model.pkl         ← stacked hybrid meta-learner
  ├── scaler.pkl             ← StandardScaler
  ├── features.json          ← feature names in order
  ├── model_comparison.csv   ← all model metrics
  └── *.png / *.html         ← all plots

Next step: run the FastAPI backend
    uvicorn api_hybrid:app --host 0.0.0.0 --port 8001 --reload
""")
