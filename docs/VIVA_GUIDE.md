# Health Supply AI: Comprehensive Academic Viva Guide
**Department of Computer Science & Engineering (Data Science)**  
**Vardhaman College of Engineering (Autonomous)**  
**Batch:** 2024–28 | **Academic Year:** 2026–27 | **Batch ID:** `24MPCSD-B07`  
**Project Title:** *Health Supply AI: Medicine Demand Prediction and Smart Restocking Using Agentic AI*  
**Team Members:** Bamandla Deekshitha (24881A6774), K Lohith Reddy (24881A6787), Ramasani Shivanand (24881A67B5)  
**Project Guide:** Mr. V Vinod Kumar (Assistant Professor, CSE-DS)

---

## Table of Contents
1. [Core Project & Domain Questions (Q1–Q6)](#1-core-project--domain-questions)
2. [Machine Learning & Forecasting Algorithms (Q7–Q14)](#2-machine-learning--forecasting-algorithms)
3. [Evaluation Metrics & Performance Diagnostics (Q15–Q18)](#3-evaluation-metrics--performance-diagnostics)
4. [Feature Engineering & Time-Series Data Leakage (Q19–Q22)](#4-feature-engineering--time-series-data-leakage)
5. [Multi-Agent Architecture & Agentic Workflow (Q23–Q26)](#5-multi-agent-architecture--agentic-workflow)
6. [Inventory Optimization, ROP & Safety Stock Logic (Q27–Q30)](#6-inventory-optimization-rop--safety-stock-logic)
7. [System Architecture, Database & Deployment (Q31–Q35)](#7-system-architecture-database--deployment)

---

### 1. Core Project & Domain Questions

#### Q1: What is the core problem addressed by Health Supply AI?
**Answer:**  
Traditional retail and hospital pharmacies rely on reactive, manual inventory tracking or static Min-Max heuristics. This results in two costly failure modes:
1. **Stockouts:** Shortages of critical life-saving medications (e.g., insulin, antibiotics during seasonal viral spikes), directly endangering patient health and causing revenue loss.
2. **Overstocking & Wastage:** Holding excess inventory ties up working capital and leads to expired, unsellable medicines that must be discarded at total financial loss.

*Health Supply AI* transforms this into a proactive, data-driven system by utilizing supervised machine learning (Random Forest Regression) to forecast demand ahead of supplier lead times, coupled with an explainable restocking calculation and multi-agent coordination with human oversight.

#### Q2: How does your system differ from existing pharmacy ERP software?
**Answer:**  
Existing commercial pharmacy software systems (like basic billing POS or Tally) are strictly **transactional**—they record sales and count what is currently on the shelf. They only alert the user *after* inventory falls to zero.  
In contrast, *Health Supply AI* is an **intelligent decision-support system**:
- It forecasts future requirements *before* stock runs out.
- It considers seasonal disease patterns, day-of-week surges, and supplier delivery lead times.
- It calculates dynamic safety stock buffers rather than static numbers.
- It employs an autonomous multi-agent pipeline that packages actionable replenishment proposals requiring pharmacist verification.

#### Q3: Why is this system defined as a "Decision Support System" rather than an autonomous ordering system?
**Answer:**  
In healthcare and pharmaceutical supply chains, completely unconstrained autonomous procurement carries legal, financial, and clinical liability risks. A pharmaceutical distributor contract involves substantial financial commitments, storage limitations (e.g., cold-chain refrigeration capacity for insulin), and regulatory drug batch compliance. Therefore, our system enforces a **Human-in-the-Loop (HITL)** architecture: AI agents analyze, predict, and optimize proposals, but final approval, quantity adjustment, or rejection is reserved exclusively for the licensed pharmacist.

#### Q4: What are the main functional modules of Health Supply AI?
**Answer:**  
1. **Interactive Analytics Dashboard:** Real-time visibility into inventory valuation, critical stock alerts, fast-moving medicines, and replenishment queues.
2. **Inventory & Expiry Surveillance:** Medicine catalog management tracking batches, stock units, reorder levels, unit prices, and expiration countdowns.
3. **Dispensation & Sales Tracker:** Point-of-sale recording, transaction logging, and bulk CSV ingestion.
4. **ML Demand Forecasting Engine:** Multi-horizon (7, 14, 30 days) predictive regression using Random Forest.
5. **Smart Restocking Optimization:** Explainable inventory calculations incorporating safety stock buffers and lead times.
6. **Early Warning Alerts Center:** Real-time detection of low stock, expiry hazards (<90 days), and demand surges.
7. **Agentic AI Orchestrator:** 4-agent sequential workflow pipeline with transparent activity tracking.
8. **Human Approval & Procurement Desk:** Reviewing, modifying, approving, and fulfilling purchase proposals.

#### Q5: Is the system diagnosing illnesses or recommending medications to patients?
**Answer:**  
No. The system strictly addresses **supply-chain inventory optimization** (pharmaceutical operations). It does not analyze patient medical histories, diagnose medical conditions, or recommend clinical drug regimens.

#### Q6: How does the system handle medicines with different shelf-lives?
**Answer:**  
Each medicine record stores an `expiry_date`. The Alert module computes `days_to_expiry = (expiry_date - today).days`. If `days_to_expiry <= 90`, a warning alert is triggered. If `days_to_expiry <= 30`, a Critical alert is generated. This alerts the pharmacy to apply First-Expired, First-Out (FEFO) dispensation protocols or return batches to distributors before expiration occurs.

---

### 2. Machine Learning & Forecasting Algorithms

#### Q7: Why did you choose Random Forest Regression as your primary predictive model?
**Answer:**  
Random Forest Regression is an ensemble learning method based on bagging (Bootstrap Aggregating) of decorrelated decision trees. It is ideally suited for medicine demand forecasting because:
1. **Non-linear Relationship Modeling:** Pharmaceutical demand exhibits complex non-linear interactions between day-of-week, seasonality, price points, and recent lag sales that linear models fail to capture.
2. **Robustness to Outliers & Noise:** Daily pharmacy sales contain random volatility; averaging predictions across 120 decision trees significantly reduces variance without increasing bias.
3. **No Rigid Stationarity Requirement:** Unlike classical ARIMA or SARIMA models which require strict mathematical stationarity and struggle with multi-variate external features (like lead time or promotion flags), Random Forest natively accepts tabular feature matrices.
4. **Feature Importance Interpretability:** Random Forest calculates Mean Decrease in Impurity (Gini importance), providing clear transparency into which factors drove the prediction.

#### Q8: How does Random Forest Regression make a continuous prediction?
**Answer:**  
Given an input feature vector $\mathbf{x}$, the Random Forest constructs $B$ individual decision trees ($T_1, T_2, \dots, T_B$), each trained on a bootstrap sample of the training data. For regression, the final prediction $\hat{y}$ is the mathematical mean of the individual tree predictions:
$$\hat{y}(\mathbf{x}) = \frac{1}{B} \sum_{b=1}^{B} T_b(\mathbf{x})$$
In our implementation, $B = 120$ trees with a constrained `max_depth=14` to prevent leaf memorization and overfitting.

#### Q9: Why not use Deep Learning architectures like LSTM or GRU?
**Answer:**  
While recurrent neural networks (RNNs/LSTMs) are powerful for massive sequential datasets, for retail pharmacy inventory:
- Retail pharmacy records (daily sales across dozens or hundreds of SKUs) do not possess the millions of continuous data points required to prevent deep networks from severe overfitting.
- Random Forest trains in seconds, requires negligible computational infrastructure (runs smoothly on commodity hardware as specified in our Review-1 hardware requirements), and requires no GPU acceleration.
- Tree ensembles produce direct feature importance scores, essential for regulatory explainability in healthcare.

#### Q10: How does your Random Forest model compare against the baseline Linear Regression model?
**Answer:**  
In our comparative evaluation:
- **Random Forest Regressor:** MAE = 4.49 units, RMSE = 6.61 units, $R^2 \approx 0.71$.
- **Linear Regression Baseline:** MAE = 4.63 units, RMSE = 6.83 units, $R^2 \approx 0.68$.
Random Forest outperforms Linear Regression across all metrics because sales demand exhibits sharp weekend spikes and seasonal surges (e.g., flu season) that represent piecewise non-linear steps rather than continuous linear slopes.

#### Q11: How does the model generate multi-step future forecasts (7, 14, 30 days)?
**Answer:**  
We employ an **iterative recursive autoregressive forecasting strategy**:
1. To predict day $t+1$, the model uses historical features up to day $t$.
2. The predicted sales value $\hat{y}_{t+1}$ is fed back into the working feature vector as the new `lag_1` value for day $t+2$.
3. Rolling statistics (such as 7-day rolling mean) are dynamically updated to incorporate the newly forecasted points.
4. This process recurses until the target horizon (7, 14, or 30 days) is reached.

#### Q12: What hyperparameters were tuned in the Random Forest model?
**Answer:**  
- `n_estimators = 120`: Number of decision trees. Provides a stable ensemble average without prohibitive latency.
- `max_depth = 14`: Bounds the maximum depth of each tree, preventing deep leaf overfitting on anomalous sales days.
- `min_samples_split = 4`: Requires at least 4 samples to attempt an internal node split.
- `min_samples_leaf = 2`: Ensures terminal leaf nodes contain at least 2 samples, smoothing prediction boundaries.
- `random_state = 42`: Ensures deterministic reproducibility across evaluation runs.

#### Q13: How does the model handle cold-start medicines with zero sales history?
**Answer:**  
If a newly registered medicine has fewer than 7 days of sales history, the system activates a rule-based fallback heuristic:
$$\text{Estimated Daily Demand} = \frac{\text{Reorder Level}}{7.0}$$
Once the medicine accumulates 30 days of sales history, the statistical feature extraction pipeline activates and transitions the SKU to the ML Random Forest engine.

#### Q14: Does Random Forest claim to be a novel algorithm created by your team?
**Answer:**  
No. Random Forest is an established, peer-reviewed machine learning algorithm introduced by Leo Breiman (2001). Our project's practical contribution lies in the **domain-specific engineering**: creating seasonal lag-rolling feature matrices, establishing an explainable replenishment mathematical formulation, structuring an autonomous multi-agent pipeline, and integrating it into an interactive clinical inventory decision-support system.

---

### 3. Evaluation Metrics & Performance Diagnostics

#### Q15: What is Mean Absolute Error (MAE) and what does it mean in this project?
**Answer:**  
MAE measures the average magnitude of absolute errors between predicted sales $\hat{y}_i$ and actual sales $y_i$:
$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$
In our system, an MAE of **4.49** means that, on average, the demand forecast deviates from actual daily medicine dispensations by approximately 4.5 units (pills/bottles). Because MAE uses absolute differences, it treats all deviations linearly and provides an intuitive, business-friendly error metric for the pharmacist.

#### Q16: What is Root Mean Squared Error (RMSE) and why is it reported alongside MAE?
**Answer:**  
RMSE is the square root of the average of squared differences between predictions and actuals:
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$
Because the errors are squared before averaging, RMSE penalizes large errors much more severely than small errors. In our model, RMSE is **6.61**. The fact that RMSE is close to MAE indicates that our model does not suffer from extreme outlier errors or catastrophic under-prediction spikes.

#### Q17: What does the $R^2$ Score (Coefficient of Determination) represent?
**Answer:**  
$R^2$ measures the proportion of variance in medicine sales explained by the independent features:
$$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$
An $R^2$ of **0.705 (70.5%)** indicates that over 70% of daily sales fluctuations across all 12 medicine categories are captured by our calendar, seasonal, lag, and rolling statistics features. The remaining variance is stochastic noise inherent to retail pharmacy walk-ins.

#### Q18: What were the most important features according to the model?
**Answer:**  
Gini feature importance analysis revealed:
1. `rolling_mean_7` (7-day historical moving average): ~38% importance—captures current baseline consumption velocity.
2. `lag_1` (sales from the previous day): ~18% importance—captures immediate day-to-day momentum.
3. `dayofweek` / `is_weekend`: ~12% importance—captures the weekend surge in retail footfall.
4. `sin_dayofyear` / `cos_dayofyear`: ~9% importance—encodes macro annual seasonality (monsoon and winter flu cycles).
5. `rolling_std_7` (demand volatility): ~6% importance—quantifies demand instability.

---

### 4. Feature Engineering & Time-Series Data Leakage

#### Q19: What is data leakage in time-series forecasting and how did you prevent it?
**Answer:**  
Data leakage occurs when information from the test set or future time periods is inadvertently exposed to the model during training or feature construction.  
We strictly prevented data leakage through two design rules:
1. **Lag Shifting by at Least 1 Day:** Every lag and rolling feature is shifted by at least 1 day (`df.shift(1)`). When predicting sales for day $t$, only data from day $t-1$ or earlier is used.
2. **Temporal (Chronological) Train/Test Split:** Standard randomized $K$-fold cross-validation or `train_test_split(shuffle=True)` is forbidden in time-series because it allows future days to train the model to predict past days. Instead, we performed a temporal split: the first ~10 months served as the training set, and the final 60 days served as the held-out test evaluation set.

#### Q20: What features did you engineer from raw sales data?
**Answer:**  
We engineered 25 distinct features:
- **Autoregressive Lags:** `lag_1`, `lag_2`, `lag_3`, `lag_7` (same day last week), `lag_14`, `lag_30`.
- **Rolling Windows:** `rolling_mean_7`, `rolling_std_7`, `rolling_mean_14`, `rolling_mean_30`, `rolling_max_7`, `rolling_min_7`.
- **Momentum:** `demand_momentum = (rolling_mean_7 + 1) / (rolling_mean_30 + 1)` (identifies whether sales are accelerating or decelerating).
- **Calendar & Refill Cycles:** `dayofweek`, `is_weekend`, `month`, `quarter`, `is_month_start` (payday/pension refill surges), `is_month_end`.
- **Trigonometric Cyclical Seasonality:** `sin_dayofyear`, `cos_dayofyear`, `sin_month`, `cos_month`.

#### Q21: Why use Sine and Cosine encoding for calendar features?
**Answer:**  
Calendar variables like months (1 to 12) or days of year (1 to 365) are cyclical. In simple integer encoding, Month 12 (December) and Month 1 (January) have a numerical distance of 11, even though they are adjacent calendar months with identical winter weather patterns. Transforming them via:
$$\sin\left(\frac{2\pi \times \text{month}}{12}\right), \quad \cos\left(\frac{2\pi \times \text{month}}{12}\right)$$
maps the calendar onto a continuous unit circle where December and January are spatially adjacent.

---

### 5. Multi-Agent Architecture & Agentic Workflow

#### Q22: What are the four agents in your system and what are their exact roles?
**Answer:**  
1. **Inventory Analyst Agent:** Reads database records for the target medicine, evaluates current stock against reorder thresholds, checks expiry dates, and analyzes 30-day sales trajectory to classify demand trends (Surging, Stable, or Declining).
2. **Demand Forecaster Agent:** Invokes the trained Random Forest model to generate daily and total demand predictions over the specified horizon (7, 14, or 30 days) and reports model MAE and RMSE metrics.
3. **Restock Optimization Agent:** Combines predicted demand, current stock, supplier lead time, and dynamic safety stock to compute the exact replenishment quantity using our explainable formula, and assigns priority (Critical, High, Medium, Low).
4. **Procurement & Compliance Agent:** Verifies the proposal against supplier lead time constraints, computes estimated purchase order cost, validates pricing sanity, formats a formal Purchase Order Proposal, and presents it for human authorization.

#### Q23: How do the agents communicate and share state?
**Answer:**  
The agents utilize a shared `AgentWorkflowState` data object managed by the `HealthSupplyAgentOrchestrator`. Each agent receives the state, performs its specialized task, populates its dedicated state dictionary (`inventory_data`, `forecast_data`, `restock_data`, `proposal_data`), logs a human-readable action entry, and passes the updated state to the next agent in sequence.

#### Q24: What is the benefit of using an Agentic AI workflow over a single monolithic script?
**Answer:**  
- **Modularity & Separation of Concerns:** If forecasting models are upgraded from Random Forest to XGBoost, only the Demand Forecaster Agent is modified without impacting inventory analysis or procurement compliance logic.
- **Explainability & Transparency:** Rather than outputting a black-box number, the user-facing activity log details every step: data retrieval $\rightarrow$ forecast execution $\rightarrow$ safety stock formula $\rightarrow$ procurement proposal.
- **Fail-Safe Checkpoints:** If the inventory agent identifies adequate stock, subsequent procurement agent steps are skipped, saving computation and avoiding unnecessary order alerts.

#### Q25: Does the Procurement Agent place orders automatically with suppliers?
**Answer:**  
No. Real-world purchase orders are never placed automatically. The Procurement Agent prepares a formal proposal and marks the state as `awaiting_approval`. Only when the human pharmacist clicks "Approve Order" does the system commit the approval to the database.

---

### 6. Inventory Optimization, ROP & Safety Stock Logic

#### Q26: What is the exact mathematical formula used for smart restocking?
**Answer:**  
$$\text{Recommended Restock Quantity} = \max(0, \text{Predicted Demand} + \text{Safety Stock} - \text{Current Stock})$$
- If `(Predicted Demand + Safety Stock) <= Current Stock`, the formula evaluates to 0 (no restocking needed).
- If `(Predicted Demand + Safety Stock) > Current Stock`, the system recommends replenishing exactly enough units to cover predicted consumption while maintaining the safety stock buffer.

#### Q27: How is Safety Stock calculated in your system?
**Answer:**  
We utilize the classical inventory management formula:
$$\text{Safety Stock} = Z \times \sigma_d \times \sqrt{L}$$
Where:
- $Z = 1.65$: Service level factor corresponding to a **95% cycle service level** (preventing 95% of random stockout events).
- $\sigma_d$: Standard deviation of daily sales over the past 30 days (quantifies demand uncertainty).
- $L$: Supplier delivery lead time in days.

If historical sales data has insufficient variance, the system uses the operational fallback:
$$\text{Safety Stock} = \text{Average Daily Demand} \times L \times 0.5$$

#### Q28: What is Reorder Point (ROP) and how is it used?
**Answer:**  
The Reorder Point is the stock level that triggers a replenishment order:
$$\text{ROP} = (\text{Average Daily Demand} \times \text{Lead Time}) + \text{Safety Stock}$$
When `current_stock <= ROP`, the medicine will deplete before a new shipment arrives unless reordered immediately. This state triggers an automated **Low-Stock Alert** and flags the item for the Procurement Agent.

#### Q29: How does the system assign priority to restocking recommendations?
**Answer:**  
- **Critical Priority:** Assigned when `current_stock == 0` (stockout) OR `current_stock / daily_demand <= lead_time` (inventory will hit zero before delivery arrives).
- **High Priority:** Assigned when `current_stock <= reorder_level`.
- **Medium Priority:** Assigned when `current_stock > reorder_level` but predicted multi-week demand exceeds available stock plus safety buffers.
- **Low Priority:** Assigned when current stock is fully adequate for the horizon.

---

### 7. System Architecture, Database & Deployment

#### Q30: What database architecture did you use and why?
**Answer:**  
We implemented **SQLAlchemy ORM** connected to **MySQL** as the primary relational database, with an **automatic zero-configuration SQLite fallback**.  
This dual-engine strategy provides:
1. Complete adherence to our college Review-1 specification (MySQL + SQLAlchemy).
2. Frictionless portability: examiners or evaluators can run the project on any computer without needing a pre-installed, pre-configured local MySQL server instance running.

#### Q31: What are the primary tables in your relational database schema?
**Answer:**  
1. `pharmacy_users`: Authentication credentials and pharmacist access roles.
2. `medicines`: Medicine catalog, category, current stock, reorder level, unit price, expiry date, supplier, lead time.
3. `sales_records`: Transactional dispensation log with foreign key referencing `medicines.medicine_id`.
4. `demand_predictions`: Historical records of ML forecasts with prediction date, horizon, and algorithm used.
5. `restocking_recommendations`: Restock proposals with recommended quantity, approved quantity, priority, and status (`Pending`, `Approved`, `Rejected`, `Fulfilled`).
6. `alerts`: Active/resolved alerts tracking Low Stock, Expiry Risks, and Demand Surges.

#### Q32: How did you ensure data integrity across transactions?
**Answer:**  
- **Database Constraints:** Table-level check constraints enforce non-negative stock (`current_stock >= 0`), positive sales (`quantity_sold >= 0`), and positive prices (`unit_price >= 0`).
- **Atomic Sessions:** Database operations use SQLAlchemy context managers (`with get_db() as session:`) with automatic `session.commit()` on success and `session.rollback()` on exceptions.
- **Cascading Deletions:** Foreign keys use `ondelete="CASCADE"` to prevent orphaned sales or prediction records if a medicine is removed from the catalog.

#### Q33: How does Streamlit handle state between user interactions?
**Answer:**  
Streamlit re-executes Python scripts from top to bottom on each widget interaction. To preserve execution history and workflow state across interactions:
- We utilize `st.session_state` to store the active `agent_workflow_state`.
- Persistent data (inventory changes, approvals, sales logs) is written immediately to the relational database, ensuring that data is never lost upon browser refresh.

#### Q34: What are the real-world limitations of this system?
**Answer:**  
1. **Supplier Supply Disruptions:** The current model assumes supplier lead time is deterministic; in reality, distributor backorders or manufacturing shortages introduce stochastic lead times.
2. **Cold-Chain / Storage Constraints:** The restocking optimizer assumes unconstrained warehouse capacity and does not yet optimize for limited refrigeration volumes.
3. **External Epidemic Spikes:** Unprecedented outbreaks (like COVID-19) represent black-swan events that historical time-series data alone cannot anticipate without external epidemiological inputs.

#### Q35: What is the future scope for this project?
**Answer:**  
1. **Automated EDI / Vendor Integration:** Connecting approved purchase orders directly to pharmaceutical distributor APIs (Electronic Data Interchange) for automated order transmission.
2. **Batch-Specific Barcode Scanning:** Integrating handheld 2D DataMatrix barcode scanners for automated physical stock intake and dispensation verification.
3. **Multi-Echelon Hospital Inventory:** Expanding from a single retail store to a hub-and-spoke model managing central pharmacy stores and satellite ward dispensaries.
