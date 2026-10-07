import numpy as np


def estimate_spike_probability(quantiles_delta, quantiles=[0.1, 0.5, 0.9], threshold=50):
    """
    Estimates the probability of a spike (delta >= 50) from the forecast quantiles.
    quantiles_delta: [n_rows, n_horizons, len(quantiles)]
    """
    max_delta_q = np.max(quantiles_delta, axis=1)
    p_spike = np.zeros(len(max_delta_q))
    
    for i in range(len(max_delta_q)):
        q0 = max_delta_q[i, 0] # 10th percentile
        q1 = max_delta_q[i, 1] # 50th percentile
        q2 = max_delta_q[i, 2] # 90th percentile
        
        if threshold <= q0:
            p = 0.9 + 0.1 * ((q0 - threshold) / max(q0, 1e-5))
            p = min(1.0, p)
        elif threshold <= q1:
            frac = (threshold - q0) / max(q1 - q0, 1e-5)
            f_val = 0.1 + frac * 0.4
            p = 1 - f_val
        elif threshold <= q2:
            frac = (threshold - q1) / max(q2 - q1, 1e-5)
            f_val = 0.5 + frac * 0.4
            p = 1 - f_val
        else:
            p = 0.1 * max(0, 1 - (threshold - q2) / 50.0)
            p = max(0.0, p)
            
        p_spike[i] = p
        
    return p_spike
