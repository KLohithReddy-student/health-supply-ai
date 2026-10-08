import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ui.components import render_header, render_kpi
from ml.predictor import predictor
from ml.train_model import train_demand_forecasting_model


def render_model_eval_view():
    render_header(
        "Machine Learning Model Performance & Analytics",
        "Evaluation Metrics, Actual vs Predicted Diagnostics & Feature Importance"
    )

    metrics = predictor.get_model_metrics()

    if not metrics:
        st.warning("Model metrics not found. Please train the model first.")
        if st.button("Train Model Now", type="primary"):
            with st.spinner("Training Random Forest model..."):
                metrics = train_demand_forecasting_model()
                st.success("✓ Model trained successfully!")
                st.rerun()
        return

    rf_res = metrics.get("random_forest", {})
    lr_res = metrics.get("baseline_linear_regression", {})

    # Top KPI Metrics Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi("Model Architecture", "Random Forest", "120 Decision Trees", "#3b82f6")
    with c2:
        render_kpi("MAE", f"{rf_res.get('mae', 0):.2f}", "Mean Absolute Error", "#10b981")
    with c3:
        render_kpi("RMSE", f"{rf_res.get('rmse', 0):.2f}", "Root Mean Squared Error", "#6366f1")
    with c4:
        render_kpi("R² Score", f"{rf_res.get('r2_score', 0):.3f}", "Variance Explained", "#8b5cf6")
    with c5:
        render_kpi("Test Set Samples", f"{metrics.get('test_samples', 0)}", f"Since {metrics.get('split_date')}", "#0284c7")

    st.markdown("<br>", unsafe_allow_html=True)

    # Academic Comparison: Random Forest vs Linear Regression
    st.subheader("📊 Comparative Algorithm Benchmark (Review-1 Specification)")
    bench_data = [
        {
            "Algorithm": "Random Forest Regressor (Proposed)",
            "MAE (Lower is Better)": rf_res.get("mae"),
            "RMSE (Lower is Better)": rf_res.get("rmse"),
            "R² Score (Higher is Better)": rf_res.get("r2_score"),
            "Handling Non-Linear Patterns": "High (Tree ensembles capture non-linear seasonality)",
            "Status": "⭐ Selected Primary Model"
        },
        {
            "Algorithm": "Linear Regression (Baseline Benchmark)",
            "MAE (Lower is Better)": lr_res.get("mae"),
            "RMSE (Lower is Better)": lr_res.get("rmse"),
            "R² Score (Higher is Better)": lr_res.get("r2_score"),
            "Handling Non-Linear Patterns": "Moderate (Linear assumptions)",
            "Status": "Baseline Comparison"
        }
    ]
    st.table(pd.DataFrame(bench_data))

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🎯 Actual vs Predicted Demand (Hold-out Test Set)")
        eval_samples = metrics.get("sample_evaluations", [])
        if eval_samples:
            eval_df = pd.DataFrame(eval_samples).tail(60)
            fig_eval = go.Figure()
            fig_eval.add_trace(go.Scatter(
                y=eval_df["quantity_sold"],
                mode="lines+markers",
                name="Actual Sales",
                line=dict(color="#0284c7", width=2.5),
                marker=dict(size=4)
            ))
            fig_eval.add_trace(go.Scatter(
                y=eval_df["predicted_sold"],
                mode="lines+markers",
                name="Random Forest Predicted",
                line=dict(color="#10b981", width=2, dash="dot"),
                marker=dict(size=4)
            ))
            fig_eval.update_layout(
                template="plotly_white",
                height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis_title="Units Sold",
                xaxis_title="Recent Test Observations",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_eval, use_container_width=True)
        else:
            st.info("No evaluation sample points available.")

    with col_right:
        st.subheader("🌲 Random Forest Feature Importance")
        importances = metrics.get("feature_importances", [])
        if importances:
            imp_df = pd.DataFrame(importances[:10])
            fig_imp = px.bar(
                imp_df,
                x="importance",
                y="feature",
                orientation="h",
                labels={"importance": "Gini Importance", "feature": "Engineered Feature"},
                color="importance",
                color_continuous_scale="Viridis"
            )
            fig_imp.update_layout(
                template="plotly_white",
                height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_imp, use_container_width=True)
        else:
            st.info("No feature importance data.")

    st.markdown("---")

    # Retrain Model Control
    st.subheader("🔄 Model Lifecycle & Retraining")
    st.write(f"Last Trained: `{metrics.get('trained_at', 'N/A')}` across `{metrics.get('training_samples', 0)}` historical training samples.")
    if st.button("🚀 Re-Train Model on Updated Sales Data", type="secondary"):
        with st.spinner("Executing temporal train/test split and re-fitting Random Forest Regressor..."):
            new_m = train_demand_forecasting_model()
            st.success("✓ Model retrained and evaluated successfully!")
            st.rerun()
