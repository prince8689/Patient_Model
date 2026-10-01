import plotly.graph_objects go
import pandas as pd
from src.app_lib.data_access import get_config

def _get_palette():
    return get_config()["app"]["palette"]

def glucose_forecast_figure(view: dict) -> go.Figure:
    fig = go.Figure()
    palette = _get_palette()
    
    past_times = pd.to_datetime(view["glucose_history"]["timestamp"])
    past_glu = view["glucose_history"]["glucose"]
    now = past_times.iloc[-1] if not past_times.empty else None
    
    # Target range
    if now is not None:
        fig.add_hrect(y0=70, y1=180, fillcolor=palette["target_range"], line_width=0, layer="below")
        
        # Past glucose
        fig.add_trace(go.Scatter(
            x=past_times, y=past_glu,
            mode="lines+markers",
            line=dict(color=palette["glucose"], width=2),
            marker=dict(size=4),
            name="Observed Glucose"
        ))
        
        # Meal and Activity markers
        for t, m in zip(past_times, view["glucose_history"]["meal_carbs"]):
            if pd.notna(m) and m > 0:
                fig.add_trace(go.Scatter(
                    x=[t], y=[min(150, past_glu[past_times == t].iloc[0] + 10) if not past_glu[past_times == t].empty else 150],
                    mode="markers+text",
                    marker=dict(symbol="triangle-up", size=10, color=palette["meal"]),
                    text=[f"{m:.0f}g"], textposition="top center",
                    name="Meal"
                ))
                
        # Now line
        fig.add_vline(x=now, line_dash="dash", line_color="gray", annotation_text="Now")
        
    # Forecast
    if view["forecast"]:
        f_times = pd.to_datetime(view["forecast"]["timestamp"])
        f_med = view["forecast"]["median"]
        f_low = view["forecast"]["lower"]
        f_up = view["forecast"]["upper"]
        
        # Connect past and future
        if now is not None and not past_times.empty:
            f_times = [now] + f_times.tolist()
            last_g = past_glu.iloc[-1]
            if pd.isna(last_g): last_g = f_med[0]
            f_med = [last_g] + f_med
            f_low = [last_g] + f_low
            f_up = [last_g] + f_up
            
        fig.add_trace(go.Scatter(
            x=list(f_times) + list(f_times)[::-1],
            y=list(f_up) + list(f_low)[::-1],
            fill="toself",
            fillcolor=palette["forecast_band"],
            line=dict(color="rgba(255,255,255,0)"),
            name="Likely Range"
        ))
        
        fig.add_trace(go.Scatter(
            x=f_times, y=f_med,
            mode="lines",
            line=dict(color=palette["glucose"], width=2, dash="dash"),
            name="Forecast Median"
        ))
        
    # Actual overlay
    if view["actual_overlay"]:
        a_times = pd.to_datetime(view["actual_overlay"]["timestamp"])
        a_glu = view["actual_overlay"]["glucose"]
        
        if now is not None and not past_times.empty:
            a_times = [now] + a_times.tolist()
            last_g = past_glu.iloc[-1]
            if pd.isna(last_g): last_g = a_glu[0]
            a_glu = [last_g] + a_glu
            
        fig.add_trace(go.Scatter(
            x=a_times, y=a_glu,
            mode="lines+markers",
            line=dict(color=palette["actual_overlay"], width=2, dash="dot"),
            marker=dict(size=4),
            name="Actual (evaluation only)"
        ))
        
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Time",
        yaxis_title="Glucose (mg/dL)",
        yaxis_range=[40, 300],
        showlegend=False,
        hovermode="x unified"
    )
    return fig

def risk_strip_figure(view: dict) -> go.Figure:
    fig = go.Figure()
    palette = _get_palette()
    
    times = pd.to_datetime(view["risk_history"]["timestamp"])
    probs = view["risk_history"]["probability"]
    
    if times.empty:
        return fig
        
    fig.add_trace(go.Scatter(
        x=times, y=probs,
        mode="lines",
        line=dict(color="black", width=1),
        fill="tozeroy",
        name="Risk Probability"
    ))
    
    # Shade background by thresholds
    config = get_config()
    t_med = config["twin"]["thresholds"]["Medium"] if "thresholds" in config["twin"] else 0.5 # fallback, should come from twin or hardcoded for now? Actually from thresholds_v1.json.
    # To keep pure without streamlit imports, we'll just shade standard or skip background shading and color line instead.
    
    for alert in view["alerts_48h"]:
        fig.add_vline(x=pd.to_datetime(alert["timestamp"]), line_color=palette[alert["band"].lower()], line_dash="dot")
        
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="",
        yaxis_title="Prob",
        yaxis_range=[0, 1],
        height=150,
        showlegend=False
    )
    return fig

def sparkline_figure(values: list) -> go.Figure:
    fig = go.Figure()
    palette = _get_palette()
    if not values:
        return fig
    fig.add_trace(go.Scatter(
        y=values,
        mode="lines",
        line=dict(color=palette["glucose"], width=2),
        hoverinfo="skip"
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[40, 300]),
        height=30,
        width=100,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig
