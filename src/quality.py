import numpy as np
import pandas as pd

class DataQualityScorer:
    """
    Computes per-ward data-quality score in [0, 1] based on three core epidemiological reporting indicators:
    1. Missingness penalty: fraction of missing reports in a rolling window.
    2. Reporting delay / latency penalty: variance in report cadence / sudden batch reporting.
    3. Inconsistency / Spikiness penalty: outlier ratio computed via rolling Median Absolute Deviation (MAD)
       or rolling Z-score to detect impossible zero-to-hundred batch reporting dumps.
       
    Score = 1.0 - (w_miss * penalty_miss + w_delay * penalty_delay + w_inconsistency * penalty_inconsistency)
    Clipped to [0.0, 1.0].
    """
    def __init__(self, window_size=12, w_miss=0.50, w_delay=0.25, w_inconsistency=0.25):
        self.window_size = window_size
        self.w_miss = w_miss
        self.w_delay = w_delay
        self.w_inconsistency = w_inconsistency
        assert np.isclose(w_miss + w_delay + w_inconsistency, 1.0), "Weights must sum to 1.0"

    def compute_ward_quality_series(self, ward_cases_series: pd.Series) -> pd.Series:
        """
        Takes a time series of reported cases (with NaNs for missing weeks) for a single ward,
        and outputs a rolling quality score series in [0, 1].
        """
        n = len(ward_cases_series)
        scores = np.ones(n, dtype=float)
        
        is_nan = ward_cases_series.isna()
        
        # 1. Rolling Missingness
        # Share of missing weeks in the trailing window_size weeks
        rolling_miss = is_nan.rolling(window=self.window_size, min_periods=1).mean()
        penalty_miss = rolling_miss.fillna(0.0).values
        
        # 2. Reporting Inconsistency via Rolling MAD / Spikiness
        # Fill NaN temporarily by forward fill for fluctuation calculation
        filled = ward_cases_series.ffill().fillna(0.0)
        diff = filled.diff().abs()
        
        # Rolling Median Absolute Deviation (MAD)
        rolling_median = filled.rolling(window=self.window_size, min_periods=3).median()
        rolling_mad = (filled - rolling_median).abs().rolling(window=self.window_size, min_periods=3).median()
        # Avoid division by zero
        rolling_mad = rolling_mad.replace(0.0, 1.0)
        
        # Modified z-score = 0.6745 * (x - median) / MAD
        mod_z = (0.6745 * (filled - rolling_median).abs() / rolling_mad).fillna(0.0)
        # Fraction of severe spikes in window
        severe_spikes = (mod_z > 3.5).rolling(window=self.window_size, min_periods=1).mean().fillna(0.0).values
        penalty_inconsistency = np.clip(severe_spikes * 2.0, 0.0, 1.0)
        
        # 3. Delay / Zero-clustering penalty:
        # A common reporting artifact is multiple zeros followed by a massive surge
        consecutive_nans = is_nan.astype(int).groupby((~is_nan).cumsum()).cumsum()
        penalty_delay = np.clip(consecutive_nans / 4.0, 0.0, 1.0).values

        # Combined penalty
        total_penalty = (
            self.w_miss * penalty_miss +
            self.w_delay * penalty_delay +
            self.w_inconsistency * penalty_inconsistency
        )
        
        scores = np.clip(1.0 - total_penalty, 0.0, 1.0)
        return pd.Series(scores, index=ward_cases_series.index)

    def score_dataset(self, df: pd.DataFrame, case_col="reported_cases") -> pd.DataFrame:
        """
        Adds a 'quality_score' column [0, 1] to the dataframe grouped by ward_id.
        """
        df_out = df.copy()
        df_out = df_out.sort_values(["ward_id", "date"]).reset_index(drop=True)
        
        quality_list = []
        for ward_id, group in df_out.groupby("ward_id"):
            q_series = self.compute_ward_quality_series(group[case_col])
            quality_list.append(q_series)
            
        df_out["quality_score"] = pd.concat(quality_list).values
        # Ensure exact [0, 1] range
        df_out["quality_score"] = np.clip(df_out["quality_score"], 0.0, 1.0)
        return df_out
