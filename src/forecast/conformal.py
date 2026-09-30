import numpy as np

class ConformalCalibrator:
    def __init__(self, horizons, quantiles, target_coverage):
        self.horizons = horizons
        self.quantiles = quantiles
        self.target_coverage = target_coverage
        self.q_hat = {} # scalars per horizon
        
    def fit(self, y_true_dict, y_pred_dict):
        """
        y_true_dict: dict of horizon -> pd.Series
        y_pred_dict: dict of horizon -> np.ndarray [n, len(quantiles)]
        """
        alpha = 1 - self.target_coverage
        
        for h in self.horizons:
            y = y_true_dict[h].values
            mask = ~np.isnan(y)
            y_val = y[mask]
            pred = y_pred_dict[h][mask]
            
            # Assuming lower is idx 0 and upper is idx 2
            lower = pred[:, 0]
            upper = pred[:, 2]
            
            # CQR nonconformity score
            scores = np.maximum(lower - y_val, y_val - upper)
            
            n = len(y_val)
            q_level = np.ceil((n + 1) * (1 - alpha)) / n
            q_level = np.clip(q_level, 0, 1)
            self.q_hat[h] = float(np.quantile(scores, q_level))
            
    def apply(self, y_pred_full):
        """
        y_pred_full: [n, n_horizons, len(quantiles)]
        """
        out = y_pred_full.copy()
        for i, h in enumerate(self.horizons):
            q_val = self.q_hat[h]
            out[:, i, 0] -= q_val
            out[:, i, 2] += q_val
        return out
