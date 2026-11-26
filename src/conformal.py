import numpy as np
import pandas as pd

class SplitConformalCalibrator:
    """
    Split-conformal prediction calibrator for time-series forecasting.
    Given raw quantile forecasts (e.g. q05, q50, q95) or point forecasts on a held-out
    calibration window, it computes conformal non-conformity scores:
    
    Residual score: R_i = max(q05_i - y_i, y_i - q95_i)
    or asymmetric coverage adjustment.
    
    At test time, the calibrated 1 - alpha (e.g., 90%) prediction interval is:
    [q05 - Q_(1-alpha)(R), q95 + Q_(1-alpha)(R)]
    clipped at 0 (since epidemiological counts cannot be negative).
    
    Guarantees finite-sample marginal coverage under exchangeability.
    """
    def __init__(self, target_coverage=0.90):
        self.target_coverage = target_coverage
        self.q_hat = {}  # horizon -> calibrated expansion threshold

    def calibrate(self, calib_df: pd.DataFrame, horizons=[2, 4, 6]):
        """
        calib_df must contain columns:
        - target_h{h}
        - q05_h{h}, q50_h{h}, q95_h{h}
        """
        for h in horizons:
            y = calib_df[f"target_h{h}"].values
            q05 = calib_df[f"q05_h{h}"].values
            q95 = calib_df[f"q95_h{h}"].values

            valid = (~np.isnan(y)) & (~np.isnan(q05)) & (~np.isnan(q95))
            y_v = y[valid]
            q05_v = q05[valid]
            q95_v = q95[valid]

            n = len(y_v)
            if n == 0:
                self.q_hat[h] = 0.0
                continue

            # Non-conformity scores: distance outside the raw quantile band
            # E_i = max(q05_i - y_i, y_i - q95_i)
            # If y_i is inside [q05_i, q95_i], score is <= 0
            scores = np.maximum(q05_v - y_v, y_v - q95_v)
            
            # Conformal quantile level: ceil((n+1) * (1 - alpha)) / n
            k = int(np.ceil((n + 1) * self.target_coverage))
            k = min(max(k, 1), n)
            q_val = np.sort(scores)[k - 1]
            self.q_hat[h] = float(q_val)

    def predict_interval(self, raw_preds: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """
        Applies calibration to raw predictions DataFrame (having 'q05', 'q50', 'q95').
        Returns DataFrame with 'lower', 'point', 'upper', 'interval_width'.
        """
        q_corr = self.q_hat.get(horizon, 0.0)
        
        lower = np.maximum(0.0, raw_preds["q05"] - q_corr)
        point = raw_preds["q50"]
        upper = np.maximum(lower, raw_preds["q95"] + q_corr)
        
        res = pd.DataFrame({
            "lower": lower,
            "point": point,
            "upper": upper,
            "interval_width": upper - lower
        }, index=raw_preds.index)
        return res

    def evaluate_coverage(self, y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict:
        """
        Calculates empirical coverage and mean interval width.
        """
        valid = (~np.isnan(y_true)) & (~np.isnan(lower)) & (~np.isnan(upper))
        if valid.sum() == 0:
            return {"coverage": 0.0, "mean_width": 0.0, "n_samples": 0}
        
        covered = (y_true[valid] >= lower[valid]) & (y_true[valid] <= upper[valid])
        coverage = float(np.mean(covered))
        mean_width = float(np.mean(upper[valid] - lower[valid]))
        return {
            "coverage": coverage,
            "mean_width": mean_width,
            "n_samples": int(valid.sum())
        }
