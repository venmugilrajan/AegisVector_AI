import numpy as np
import pandas as pd

class DecisionEngine:
    """
    Abstain Logic: Tri-state decision system for public health intervention.
    
    States:
    1. 'Alert' (High Actionability):
       Risk is elevated AND predictive interval is sufficiently narrow / confident.
    2. 'Watch' (Monitoring):
       Risk is moderate or rising, with acceptable interval width.
    3. 'Insufficient Confidence' (Abstain / Caution):
       Prediction interval is excessively wide OR local data quality score is below threshold.
       
    The system knows WHEN NOT TO TRUST ITSELF.
    """
    def __init__(
        self,
        risk_alert_threshold=25.0,     # Case threshold for Alert
        risk_watch_threshold=12.0,     # Case threshold for Watch
        max_rel_width=1.5,             # Max allowed ratio: interval_width / (point_forecast + 5.0)
        min_quality_score=0.65         # Data quality floor below which model abstains
    ):
        self.risk_alert_threshold = risk_alert_threshold
        self.risk_watch_threshold = risk_watch_threshold
        self.max_rel_width = max_rel_width
        self.min_quality_score = min_quality_score

    def classify(
        self,
        point_forecast: float,
        interval_width: float,
        quality_score: float
    ) -> str:
        # 1. Gate: Quality floor or excessive uncertainty triggers Insufficient Confidence
        rel_width = interval_width / (point_forecast + 5.0)
        
        if quality_score < self.min_quality_score or rel_width > self.max_rel_width:
            return "Insufficient confidence"
            
        # 2. Alert criteria
        if point_forecast >= self.risk_alert_threshold:
            return "Alert"
            
        # 3. Watch criteria
        if point_forecast >= self.risk_watch_threshold:
            return "Watch"
            
        return "Normal"

    def classify_dataframe(
        self,
        df: pd.DataFrame,
        point_col="point",
        width_col="interval_width",
        quality_col="quality_score"
    ) -> pd.Series:
        """
        Vectorized classification across ward forecasts.
        """
        point = df[point_col].values
        width = df[width_col].values
        quality = df[quality_col].values
        
        rel_width = width / (point + 5.0)
        
        # Insufficient confidence condition
        abstain_mask = (quality < self.min_quality_score) | (rel_width > self.max_rel_width)
        
        alert_mask = (~abstain_mask) & (point >= self.risk_alert_threshold)
        watch_mask = (~abstain_mask) & (~alert_mask) & (point >= self.risk_watch_threshold)
        
        status = np.full(len(df), "Normal", dtype=object)
        status[abstain_mask] = "Insufficient confidence"
        status[alert_mask] = "Alert"
        status[watch_mask] = "Watch"
        
        return pd.Series(status, index=df.index)
