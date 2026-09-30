import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

class PersistenceForecaster:
    def __init__(self, horizons, quantiles):
        self.horizons = horizons
        self.quantiles = quantiles
        self.residuals = {}

    def fit(self, X, y_dict):
        for h in self.horizons:
            # y_dict[h] is a pd.Series of deltas
            # Persistence prediction is 0. Residual is 0 - y = -y
            resids = 0 - y_dict[h].values
            self.residuals[h] = np.quantile(resids, [0.1, 0.5, 0.9])
            
    def predict_quantiles(self, X):
        n = len(X)
        out = np.zeros((n, len(self.horizons), len(self.quantiles)))
        for i, h in enumerate(self.horizons):
            # med = 0, + quantiles of residuals
            for j, q in enumerate(self.quantiles):
                # The prediction for quantile q is 0 - residual quantile (1-q)
                # But it's simpler: empirical quantiles of y_dict[h]
                out[:, i, j] = -self.residuals[h][len(self.quantiles)-1-j]
        return out

class LinearExtrapolationForecaster:
    def __init__(self, horizons, quantiles):
        self.horizons = horizons
        self.quantiles = quantiles
        self.damping_factors = {}
        self.residuals = {}
        
    def fit(self, X, y_dict):
        # We need glu_slope_30m
        slope = X["glu_slope_30m"].fillna(0).values
        for h in self.horizons:
            y = y_dict[h].values
            # minimize MAE: sum | y - slope * h * c |
            # simple grid search for c between 0 and 1
            best_c = 0.0
            best_mae = np.inf
            for c in np.linspace(0, 1, 11):
                pred = slope * h * c
                mae = np.mean(np.abs(y - pred))
                if mae < best_mae:
                    best_mae = mae
                    best_c = c
            self.damping_factors[h] = best_c
            resids = (slope * h * best_c) - y
            self.residuals[h] = np.quantile(resids, [0.1, 0.5, 0.9])
            
    def predict_quantiles(self, X):
        n = len(X)
        slope = X["glu_slope_30m"].fillna(0).values
        out = np.zeros((n, len(self.horizons), len(self.quantiles)))
        for i, h in enumerate(self.horizons):
            c = self.damping_factors[h]
            base_pred = slope * h * c
            for j, q in enumerate(self.quantiles):
                out[:, i, j] = base_pred - self.residuals[h][len(self.quantiles)-1-j]
        return out

class RidgeForecaster:
    def __init__(self, horizons, quantiles):
        self.horizons = horizons
        self.quantiles = quantiles
        self.models = {}
        self.residuals = {}
        
    def fit(self, X, y_dict):
        for h in self.horizons:
            pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("ridge", Ridge(alpha=1.0))
            ])
            y = y_dict[h].values
            # Filter NaNs in target
            mask = ~np.isnan(y)
            pipe.fit(X[mask], y[mask])
            self.models[h] = pipe
            
            pred = pipe.predict(X[mask])
            resids = pred - y[mask]
            self.residuals[h] = np.quantile(resids, [0.1, 0.5, 0.9])
            
    def predict_quantiles(self, X):
        n = len(X)
        out = np.zeros((n, len(self.horizons), len(self.quantiles)))
        for i, h in enumerate(self.horizons):
            pred = self.models[h].predict(X)
            for j, q in enumerate(self.quantiles):
                out[:, i, j] = pred - self.residuals[h][len(self.quantiles)-1-j]
        return out
