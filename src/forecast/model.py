import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import xgboost as xgb
from sklearn.model_selection import GroupKFold
from scipy.interpolate import pchip_interpolate
from typing import Dict

class GlucoseForecaster:
    def __init__(self, config: dict):
        self.config = config
        self.horizons = config["forecast"]["horizons_minutes"]
        self.quantiles = config["forecast"]["quantiles"]
        self.models = {} # (h, q) -> xgb model
        self.imputer = None
        
    def _get_hyperparams(self, X, y, groups):
        # Tuning on 60m median
        trials = self.config["forecast"]["tuning_trials"]
        best_loss = np.inf
        best_params = None
        best_n_estimators = 100
        
        for _ in range(trials):
            params = {
                "max_depth": np.random.randint(3, 8),
                "learning_rate": np.exp(np.random.uniform(np.log(0.03), np.log(0.2))),
                "min_child_weight": np.random.uniform(1, 20),
                "subsample": np.random.uniform(0.6, 1.0),
                "colsample_bytree": np.random.uniform(0.5, 1.0),
                "reg_lambda": np.random.uniform(0.5, 10),
                "objective": "reg:quantileerror",
                "quantile_alpha": 0.5,
                "tree_method": "hist",
                "n_estimators": self.config["forecast"]["max_estimators"],
                "early_stopping_rounds": self.config["forecast"]["xgb_early_stopping_rounds"]
            }
            
            gkf = GroupKFold(n_splits=self.config["forecast"]["cv_folds"])
            losses = []
            best_iters = []
            for train_idx, val_idx in gkf.split(X, y, groups):
                X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
                X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
                
                model = xgb.XGBRegressor(**params)
                model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
                
                preds = model.predict(X_val)
                # Pinball loss for q=0.5 (which is 0.5 * MAE)
                q = 0.5
                errors = y_val - preds
                loss = np.mean(np.maximum(q * errors, (q - 1) * errors))
                losses.append(loss)
                best_iters.append(model.best_iteration)
                
            mean_loss = np.mean(losses)
            if mean_loss < best_loss:
                best_loss = mean_loss
                best_params = params.copy()
                best_n_estimators = int(np.mean(best_iters) * 1.1)
                
        # Remove early stopping for final fit
        del best_params["early_stopping_rounds"]
        best_params["n_estimators"] = best_n_estimators
        return best_params
        
    def fit(self, X, y_dict, groups):
        # 1. Fit Imputer
        self.imputer = SimpleImputer(strategy="median")
        X_imp = pd.DataFrame(self.imputer.fit_transform(X), columns=X.columns, index=X.index)
        
        # 2. Tune on 60m median
        print("Tuning hyperparameters on 60m median...")
        y_60 = y_dict[60]
        mask = ~y_60.isna()
        best_params = self._get_hyperparams(X_imp[mask], y_60[mask], groups[mask])
        print(f"Best params: {best_params}")
        
        # 3. Fit all models
        for h in self.horizons:
            y_h = y_dict[h]
            mask = ~y_h.isna()
            X_curr = X_imp[mask]
            y_curr = y_h[mask]
            
            for q in self.quantiles:
                print(f"Fitting horizon {h}m, quantile {q}...")
                params = best_params.copy()
                params["quantile_alpha"] = q
                model = xgb.XGBRegressor(**params)
                model.fit(X_curr, y_curr, verbose=False)
                self.models[(h, q)] = model

    def predict_quantiles(self, X: pd.DataFrame) -> np.ndarray:
        X_imp = pd.DataFrame(self.imputer.transform(X), columns=X.columns, index=X.index)
        n = len(X)
        out = np.zeros((n, len(self.horizons), len(self.quantiles)))
        
        for i, h in enumerate(self.horizons):
            for j, q in enumerate(self.quantiles):
                out[:, i, j] = self.models[(h, q)].predict(X_imp)
                
        # Enforce non-crossing (rearrangement)
        out_sorted = np.sort(out, axis=2)
        crossing_mask = (out != out_sorted)
        crossing_rate = crossing_mask.any(axis=2).mean()
        # print(f"Quantile crossing rate fixed: {crossing_rate:.2%}")
        return out_sorted

    def get_trajectory(self, current_glucose: np.ndarray, quantiles_delta: np.ndarray) -> np.ndarray:
        """
        Interpolates the 5-minute trajectory.
        quantiles_delta: [n_rows, n_horizons, n_quantiles]
        Returns: [n_rows, n_steps, n_quantiles]
        """
        n_rows = len(current_glucose)
        interval = self.config["sampling_interval_minutes"]
        max_horizon = max(self.horizons)
        n_steps = int(max_horizon / interval) + 1
        
        x_knots = [0] + self.horizons
        x_eval = np.arange(0, max_horizon + interval, interval)
        
        traj = np.zeros((n_rows, len(x_eval), len(self.quantiles)))
        
        for i in range(n_rows):
            for j in range(len(self.quantiles)):
                y_knots = [current_glucose[i]] + [current_glucose[i] + quantiles_delta[i, k, j] for k in range(len(self.horizons))]
                y_knots = np.clip(y_knots, self.config["glucose_min"], self.config["glucose_max"])
                traj[i, :, j] = pchip_interpolate(x_knots, y_knots, x_eval)
                
        # Enforce ordering across trajectory
        traj = np.sort(traj, axis=2)
        return traj
