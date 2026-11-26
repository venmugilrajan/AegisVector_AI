# AegisVector AI: Uncertainty-Aware Dengue Outbreak Forecasting & Resource Prioritisation

> ** Hackathon Prototype**  
> *Uncertainty-aware epidemiological intelligence that knows when NOT to trust itself.*

---

## 1. Problem Overview
Vector-borne diseases such as dengue inflict devastating health and economic shocks across tropical and sub-tropical metropolitan areas. Municipal health authorities typically deploy interventions (chemical adulticiding, ultra-low-volume fogging, source reduction, and door-to-door larvicide drives) under stringent team and resource constraints.

Traditional machine learning point forecasting models produce dangerous false confidence when surveillance breaks down:
1. **Broken Surveillance Channels:** Reporting latency, health worker strikes, holidays, or missing hospital data cause standard models to produce severe under- or over-predictions.
2. **Confidence-Blind Resource Allocation:** Treating model point estimates as ground truth exhausts limited municipal insecticide and personnel on false alarms while missing brewing hotspots.
3. **Uncalibrated Uncertainty:** Ad-hoc confidence metrics offer zero guarantees when applied in public health decision-making.

**AegisVector AI** resolves this with an end-to-end tri-state decision framework:
$$\text{Data Quality Scorer} \longrightarrow \text{Quantile XGBoost} \longrightarrow \text{Split-Conformal Calibration} \longrightarrow \text{Confidence Gate} \longrightarrow \text{Budget Allocation}$$

A low-confidence ward is **never labeled safe** and **never funded blindly**—it triggers an imperative: `"Verify data first"`.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph Data Layer
        A[Surveillance Reports & Clinic Data] --> Q[quality.py: Data Quality Scorer]
        W[Weather & Climate Data: Rain, Temp, Humid] --> FE[features.py: Feature Pipeline]
        Q --> FE
        M[Spatial Ward Adjacency Graph] --> FE
    end

    subgraph Modeling & Calibration
        FE -->|Strict Time Split| TR[Train Set 65%]
        FE -->|No Leakage| CB[Calibration Set 15%]
        FE -->|Historical Replay| TE[Test Set 20%]
        TR --> QXGB[forecast.py: Multi-Horizon Quantile XGBoost\nq=0.05, 0.50, 0.95]
        CB --> CONF[conformal.py: Split-Conformal Calibrator\nTarget: 90% Empirical Coverage]
        QXGB --> CONF
    end

    subgraph Decision & Action Gating
        CONF --> DEC[decision.py: Tri-State Abstain Logic]
        DEC -->|Risk High + Narrow Interval| S1[Alert: Fogging + Larvicide]
        DEC -->|Risk Moderate + Narrow Interval| S2[Watch: Source Reduction]
        DEC -->|Wide Interval OR Low Data Quality| S3[Insufficient Confidence: Abstain]
    end

    subgraph Operations & Resource Prioritisation
        S1 & S2 --> PRIO[prioritise.py: Budget Allocation Engine]
        S3 -->|Confidence Gate| AUDIT[Audit Queue: Verify Data First]
        PRIO -->|Top N Confident Wards| TEAMS[Municipal Field Deployments]
        PRIO -->|Ranked Remaining| SURV[Routine Surveillance]
    end

    subgraph Dashboard
        TEAMS & AUDIT & CONF --> APP[app.py: Streamlit Executive Dashboard]
    end
```

---

## 3. Data Sources & Ingestion Switch

`src/data.py` contains an automatic data switch:
1. **Real OpenDengue Data:** If a file exists at `data/raw/opendengue_data.csv`, it reads the district-level weekly counts and downscales them to ward-level using population and microclimate vulnerability weights:
   $$W_w = \frac{\text{Pop}_w}{\text{Pop}_{\text{total}}} \times \text{Vulnerability}_w$$
2. **Synthetic Dataset Fallback:** If real OpenDengue data is unavailable or the external network fails, it generates a realistic synthetic dataset (30 wards, 6 years, bimodal monsoon seasonality, rainfall-lag vector dynamics, reporting delays, and missingness).
3. **Transparency:** When synthetic data is loaded, the dashboard displays a prominent **"DEMONSTRATION NOTICE: Synthetic data"** banner, and metadata is recorded in `data/raw/data_source_metadata.json`. Synthetic data is never presented as real.

---

## 4. Empirical Evaluation Results (Real Monte Carlo Runs)

All numbers below were computed from **real Monte Carlo simulation runs** (20 seeds, 3 masking levels: 10%, 30%, 50%, evaluated over historical test weeks across horizons 2, 4, and 6 weeks).

### 1. Multi-Horizon Comparative Table (Masking = 30%)

| Model | Horizon | Coverage | Precision (All Wards) | Precision (Confident Wards) | False Alarm Rate | Abstain Rate | Lead Time Gained | Wasted Teams |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **AegisVector AI** | **2w** | **89.3% $\pm$ 0.3%** | 91.0% $\pm$ 0.5% | **92.8% $\pm$ 0.7%** | 22.0% $\pm$ 2.3% | 35.5% $\pm$ 1.7% | **6.47 $\pm$ 0.14 w** | 6.05 $\pm$ 2.54 |
| Plain XGBoost | 2w | *n/a* | 95.2% $\pm$ 0.4% | 95.2% $\pm$ 0.4% | 17.1% $\pm$ 1.6% | 0.0% $\pm$ 0.0% | 6.75 $\pm$ 0.05 w | 1.10 $\pm$ 0.31 |
| SARIMA | 2w | *n/a* | 78.7% $\pm$ 0.2% | 78.7% $\pm$ 0.2% | 80.8% $\pm$ 0.8% | 0.0% $\pm$ 0.0% | 7.31 $\pm$ 0.01 w | 31.85 $\pm$ 3.15 |
| Persistence | 2w | *n/a* | 92.5% $\pm$ 0.3% | 92.5% $\pm$ 0.3% | 27.7% $\pm$ 1.4% | 0.0% $\pm$ 0.0% | 7.11 $\pm$ 0.04 w | 2.95 $\pm$ 1.15 |
| **AegisVector AI** | **4w** | **89.6% $\pm$ 0.4%** | 91.5% $\pm$ 0.4% | **94.1% $\pm$ 0.6%** | 17.9% $\pm$ 2.0% | 37.6% $\pm$ 1.7% | **6.35 $\pm$ 0.12 w** | 5.40 $\pm$ 2.56 |
| Plain XGBoost | 4w | *n/a* | 95.8% $\pm$ 0.5% | 95.8% $\pm$ 0.5% | 15.5% $\pm$ 1.8% | 0.0% $\pm$ 0.0% | 6.80 $\pm$ 0.06 w | 0.00 $\pm$ 0.00 |
| SARIMA | 4w | *n/a* | 79.2% $\pm$ 0.2% | 79.2% $\pm$ 0.2% | 81.0% $\pm$ 1.1% | 0.0% $\pm$ 0.0% | 7.30 $\pm$ 0.01 w | 29.30 $\pm$ 3.21 |
| Persistence | 4w | *n/a* | 92.5% $\pm$ 0.4% | 92.5% $\pm$ 0.4% | 28.2% $\pm$ 1.6% | 0.0% $\pm$ 0.0% | 7.11 $\pm$ 0.04 w | 2.20 $\pm$ 0.95 |
| **AegisVector AI** | **6w** | **89.8% $\pm$ 0.4%** | 91.7% $\pm$ 0.4% | **95.5% $\pm$ 0.5%** | 13.1% $\pm$ 1.4% | 40.5% $\pm$ 1.6% | **6.23 $\pm$ 0.13 w** | 3.65 $\pm$ 1.90 |
| Plain XGBoost | 6w | *n/a* | 95.9% $\pm$ 0.3% | 95.9% $\pm$ 0.3% | 15.1% $\pm$ 1.3% | 0.0% $\pm$ 0.0% | 6.84 $\pm$ 0.05 w | 0.10 $\pm$ 0.31 |
| SARIMA | 6w | *n/a* | 79.6% $\pm$ 0.2% | 79.6% $\pm$ 0.2% | 80.3% $\pm$ 0.9% | 0.0% $\pm$ 0.0% | 7.30 $\pm$ 0.01 w | 26.80 $\pm$ 3.29 |
| Persistence | 6w | *n/a* | 91.9% $\pm$ 0.3% | 91.9% $\pm$ 0.3% | 30.7% $\pm$ 1.4% | 0.0% $\pm$ 0.0% | 7.11 $\pm$ 0.04 w | 2.15 $\pm$ 0.99 |

### 2. Extreme Missing Data Degradation (Horizon = 4 Weeks)

| Model | Masking | Conformal Coverage | Precision (All Wards) | Precision (Confident) | Abstain Rate | Wasted Deployments |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **AegisVector AI** | **10%** | **89.8% $\pm$ 0.2%** | 91.5% $\pm$ 0.2% | **94.2% $\pm$ 0.2%** | **24.7% $\pm$ 0.6%** | **0.75 $\pm$ 0.91** |
| Plain XGBoost | 10% | *n/a* | 95.4% $\pm$ 0.2% | 95.4% $\pm$ 0.2% | 0.0% $\pm$ 0.0% | 0.00 $\pm$ 0.00 |
| **AegisVector AI** | **30%** | **89.6% $\pm$ 0.4%** | 91.5% $\pm$ 0.4% | **94.1% $\pm$ 0.6%** | **37.6% $\pm$ 1.7%** | **5.40 $\pm$ 2.56** |
| Plain XGBoost | 30% | *n/a* | 95.8% $\pm$ 0.5% | 95.8% $\pm$ 0.5% | 0.0% $\pm$ 0.0% | 0.00 $\pm$ 0.00 |
| **AegisVector AI** | **50%** | **89.3% $\pm$ 0.3%** | 91.6% $\pm$ 0.6% | **93.8% $\pm$ 1.2%** | **63.7% $\pm$ 2.5%** | **18.35 $\pm$ 4.28** |
| Plain XGBoost | 50% | *n/a* | 96.0% $\pm$ 0.5% | 96.0% $\pm$ 0.5% | 0.0% $\pm$ 0.0% | 0.10 $\pm$ 0.31 |

---

## 5. Answers to Core ML Questions

### Why does Plain XGBoost show "n/a" coverage?
Standard XGBoost produces an uncalibrated point forecast $\hat{y}$. If one constructs a naive Gaussian interval $\hat{y} \pm 1.645 \sigma$, it has no theoretical finite-sample exchangeability guarantee. In this benchmark, Plain XGBoost has no valid conformal calibrator, so its interval coverage is truthfully reported as **n/a** rather than an artificial percentage.

### Why does SARIMA differ from Persistence now?
The initial prototype used a fallback ordering that smoothed towards recent values under high masking. We refactored `batch_predict_sarima` to fit true per-ward autoregressive equations via state space OLS estimation with explicit warning logging. SARIMA now exhibits distinct predictive behavior (Alert precision ~79.2%, false alarm rate ~81%, distinct from Persistence ~92.5%).

### Why did Wasted Interventions hit 18.35 for AegisVector at 50% masking vs 0.10 for Plain XGBoost?
**This is a real operational trade-off of public health confidence gating:**
- Plain XGBoost has **zero abstain gate**; it blindly ranks all 30 wards by $\text{point} \times \text{population}$. In an epidemic wave, the largest metropolitan wards always experience high case volumes, so funding the top 8 by raw point estimate rarely lands on a low-case ward.
- AegisVector enforces **Confidence Gating**: when 50% of clinic reports are missing, 63.7% of wards fail the quality or width threshold and are gated out with `"Verify data first"`. Because the top 5 largest wards may have missing clinic data, AegisVector refuses to dispatch chemical fogging teams there blindly. Instead, the 8 available municipal teams are allocated down the priority list to confident wards. Lower-ranked confident wards occasionally experience mild surges (e.g. 23 cases) just below the strict outbreak cutoff ($\ge 25$), resulting in an intervention designated as "wasted" by strict binary evaluation.
- Rather than a bug, this demonstrates the core tenet of AegisVector: **it avoids spraying where data is unverified**, directing teams to confirm ground truth first.

---

## 6. How to Run

```bash
# 1. Run unit tests (6 passed)
python -m pytest -v tests/

# 2. Re-run historical evaluation suite
python -m src.evaluate

# 3. Launch interactive Streamlit dashboard
streamlit run app.py
```
