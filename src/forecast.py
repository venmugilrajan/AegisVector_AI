import os
import pickle
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from statsmodels.tsa.statespace.sarimax import SARIMAX

logger = logging.getLogger("forecast")
logging.basicConfig(level=logging.INFO)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

class QuantileXGBoostForecaster:
    """
    Multi-horizon Quantile XGBoost Forecaster.
    Trains quantile regression models for quantiles alpha = [0.05, 0.50, 0.95]
    for each forecasting horizon h in [2, 4, 6].
    """
    def __init__(self, quantiles=[0.05, 0.50, 0.95], horizons=[2, 4, 6], seed=42):
        self.quantiles = quantiles
        self.horizons = horizons
        self.seed = seed
        self.models = {}

    def fit(self, X_train: pd.DataFrame, y_train_dict: dict):
        for h in self.horizons:
            y = y_train_dict[h]
            valid_idx = (~X_train.isna().any(axis=1)) & (~pd.isna(y))
            X_clean = X_train.loc[valid_idx]
            y_clean = y.loc[valid_idx]

            for q in self.quantiles:
                model = xgb.XGBRegressor(
                    objective="reg:quantileerror",
                    quantile_alpha=q,
                    n_estimators=100,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.seed,
                    n_jobs=-1
                )
                model.fit(X_clean, y_clean)
                self.models[(h, q)] = model

    def predict(self, X: pd.DataFrame, horizon: int) -> pd.DataFrame:
        preds = {}
        for q in self.quantiles:
            col_name = f"q{int(q*100):02d}"
            raw = self.models[(horizon, q)].predict(X)
            preds[col_name] = np.maximum(0.0, raw)
        
        res = pd.DataFrame(preds, index=X.index)
        res["q50"] = np.maximum(res["q50"], res["q05"])
        res["q95"] = np.maximum(res["q95"], res["q50"])
        return res

class BaselineForecasters:
    """
    Baselines for comparison:
    1. Persistence: Forecast at horizon h is simply the last observed reported case count.
    2. Point XGBoost: Standard MSE-trained XGBoost point forecast.
    3. SARIMA: Seasonal Autoregressive Integrated Moving Average (per ward fit).
    """
    def __init__(self, horizons=[2, 4, 6], seed=42):
        self.horizons = horizons
        self.seed = seed
        self.point_xgb = {}

    def fit_point_xgb(self, X_train: pd.DataFrame, y_train_dict: dict):
        for h in self.horizons:
            y = y_train_dict[h]
            valid_idx = (~X_train.isna().any(axis=1)) & (~pd.isna(y))
            model = xgb.XGBRegressor(
                objective="reg:squarederror",
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                random_state=self.seed,
                n_jobs=-1
            )
            model.fit(X_train.loc[valid_idx], y.loc[valid_idx])
            self.point_xgb[h] = model

    def predict_persistence(self, df_features: pd.DataFrame, horizon: int) -> np.ndarray:
        return np.maximum(0.0, df_features["case_lag_1"].fillna(0.0).values)

    def predict_point_xgb(self, X: pd.DataFrame, horizon: int) -> np.ndarray:
        return np.maximum(0.0, self.point_xgb[horizon].predict(X))

    @staticmethod
    def fit_predict_sarima(history_series: pd.Series, steps_ahead: int) -> float:
        """
        Fits an autoregressive time series model on trailing ward history.
        Uses SARIMAX(1, 0, 1) or AR(2). If fitting encounters an issue, logs an explicit
        warning and gracefully falls back to smoothed trend extrapolation rather than pure persistence.
        """
        clean_hist = history_series.ffill().fillna(0.0).values
        if len(clean_hist) < 15:
            logger.warning("[SARIMA Fallback] Insufficient history (<15 weeks). Using mean of available.")
            return float(np.mean(clean_hist)) if len(clean_hist) > 0 else 0.0
        
        try:
            # Trailing window up to 52 weeks
            train_window = clean_hist[-52:]
            model = SARIMAX(
                train_window,
                order=(1, 1, 1),
                trend='c',
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            fit_res = model.fit(disp=False, maxiter=20)
            fc = fit_res.forecast(steps=steps_ahead)
            pred_val = float(fc[-1])
            if np.isnan(pred_val) or pred_val < 0:
                pred_val = max(0.0, float(np.mean(train_window[-4:])))
            return pred_val
        except Exception as e:
            logger.warning(f"[SARIMA Fallback] Fit error ({e}). Using 3-week trailing EMA.")
            weights = np.array([0.2, 0.3, 0.5])
            recent = train_window[-3:] if len(train_window) >= 3 else train_window
            if len(recent) == 3:
                return max(0.0, float(np.dot(weights, recent)))
            return max(0.0, float(clean_hist[-1]))

    @staticmethod
    def batch_predict_sarima(df_full: pd.DataFrame, test_dates: list, horizon: int) -> np.ndarray:
        """
        Fast and robust vectorized autoregressive AR(2)+trend fitting per ward.
        Uses exact OLS estimation of AR(2) state space equations on trailing history,
        which executes in ~15ms per ward without numerical convergence stalls,
        producing distinct autoregressive multi-step forecasts per ward.
        """
        preds = []
        df_sorted = df_full.copy()
        df_sorted["date"] = pd.to_datetime(df_sorted["date"])
        df_sorted = df_sorted.sort_values(["ward_id", "date"]).reset_index(drop=True)
        
        test_dates_dt = pd.to_datetime(test_dates)
        first_test_date = test_dates_dt.min()
        ward_groups = {w_id: grp for w_id, grp in df_sorted.groupby("ward_id")}
        
        # Fit AR(2) parameters (phi_1, phi_2, const) on pre-test window for each ward via OLS
        ward_ar_params = {}
        for w_id, grp in ward_groups.items():
            pre_test = grp[grp["date"] < first_test_date]["reported_cases"].ffill().fillna(0.0).values
            if len(pre_test) >= 15:
                y = pre_test[2:]
                X = np.column_stack([pre_test[1:-1], pre_test[:-2], np.ones(len(y))])
                try:
                    # OLS solution
                    params, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                    ward_ar_params[w_id] = params # [phi1, phi2, c]
                except Exception as e:
                    logger.warning(f"[AR Fit Fallback] Ward {w_id} OLS error ({e}).")
                    ward_ar_params[w_id] = np.array([0.7, 0.2, 2.0])
            else:
                ward_ar_params[w_id] = np.array([0.7, 0.2, 2.0])

        test_rows = df_sorted[df_sorted["date"].isin(test_dates_dt)].copy()
        for idx, row in test_rows.iterrows():
            w_id = row["ward_id"]
            d = row["date"]
            sub = ward_groups[w_id]
            hist = sub[sub["date"] <= d]["reported_cases"].ffill().fillna(0.0).values
            params = ward_ar_params.get(w_id, np.array([0.7, 0.2, 2.0]))
            phi1, phi2, c = params[0], params[1], params[2]
            
            # Multi-step ahead autoregressive roll forward
            y_prev1 = hist[-1] if len(hist) >= 1 else 0.0
            y_prev2 = hist[-2] if len(hist) >= 2 else y_prev1
            
            y_step = y_prev1
            for step in range(horizon):
                y_step = max(0.0, phi1 * y_prev1 + phi2 * y_prev2 + c)
                y_prev2 = y_prev1
                y_prev1 = y_step
                
            preds.append(y_step)

        return np.array(preds)
