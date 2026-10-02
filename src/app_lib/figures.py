import pandas as pd
import plotly.graph_objects as go

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

def whatif_fan_figure(vm: dict) -> go.Figure:
    fig = go.Figure()
    palette = _get_palette()
    scen_colors = get_config()["app"]["scenario_colors"]
    
    past_glu = vm["history_window"]["glucose"]
    past_times = pd.to_datetime([s["timestamp"] for s in past_glu])
    past_vals = [s["glucose_mgdl"] for s in past_glu]
    now = past_times.iloc[-1] if len(past_times) > 0 else None
    
    # Target range
    if now is not None:
        fig.add_hrect(y0=70, y1=180, fillcolor=palette["target_range"], line_width=0, layer="below")
        fig.add_trace(go.Scatter(
            x=past_times, y=past_vals,
            mode="lines+markers",
            line=dict(color=palette["glucose"], width=2),
            marker=dict(size=4),
            name="Observed"
        ))
        fig.add_vline(x=now, line_dash="dash", line_color="gray", annotation_text="Now")
        
    scenarios = vm.get("scenarios", [])
    if vm.get("baseline"):
        scenarios = [vm["baseline"]] + scenarios
        
    show_all_bands = len(scenarios) <= 3
    
    interval_m = get_config()["sampling_interval_minutes"]
    for s in scenarios:
        color = scen_colors.get(s["name"], scen_colors["custom"])
        
        f_med = s["median_trajectory"]
        f_low = s["p10_trajectory"]
        f_up = s["p90_trajectory"]
        
        # generate future times
        if now is not None:
            f_times = [now + pd.Timedelta(minutes=interval_m * (i+1)) for i in range(len(f_med))]
            
            last_g = past_vals[-1]
            if pd.isna(last_g): last_g = f_med[0]
            f_times = [now] + f_times
            f_med = [last_g] + f_med
            f_low = [last_g] + f_low
            f_up = [last_g] + f_up
            
            # Band
            if show_all_bands or s["name"] == "baseline":
                rgba = color
                if color.startswith("#"):
                    h = color.lstrip('#')
                    rgba = f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, 0.2)"
                    
                fig.add_trace(go.Scatter(
                    x=list(f_times) + list(f_times)[::-1],
                    y=list(f_up) + list(f_low)[::-1],
                    fill="toself",
                    fillcolor=rgba,
                    line=dict(color="rgba(255,255,255,0)"),
                    name=s["name"] + " range",
                    showlegend=False
                ))
                
            # Line
            fig.add_trace(go.Scatter(
                x=f_times, y=f_med,
                mode="lines",
                line=dict(color=color, width=2, dash="solid" if s["name"] != "baseline" else "dash"),
                name=s["name"].replace("_", " ").capitalize()
            ))
            
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Time",
        yaxis_title="Glucose (mg/dL)",
        yaxis_range=[40, 300],
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def whatif_effects_figure(vm: dict) -> go.Figure:
    fig = go.Figure()
    scen_colors = get_config()["app"]["scenario_colors"]
    
    scenarios = vm.get("scenarios", [])
    if not scenarios:
        return fig
        
    names = [s["name"].replace("_", " ").capitalize() for s in scenarios]
    peaks = [s["delta_peak_median"] for s in scenarios]
    peaks_err_minus = [s["delta_peak_median"] - s["delta_peak_p10"] for s in scenarios]
    peaks_err_plus = [s["delta_peak_p90"] - s["delta_peak_median"] for s in scenarios]
    colors = [scen_colors.get(s["name"], scen_colors["custom"]) for s in scenarios]
    
    fig.add_trace(go.Bar(
        x=peaks,
        y=names,
        orientation='h',
        marker_color=colors,
        error_x=dict(type='data', array=peaks_err_plus, arrayminus=peaks_err_minus),
        name="Delta Peak"
    ))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Estimated Peak Glucose Difference vs Baseline (mg/dL)",
        yaxis_title="",
        showlegend=False
    )
    return fig

def p_improvement_figure(vm: dict) -> go.Figure:
    fig = go.Figure()
    scenarios = vm.get("scenarios", [])
    if not scenarios:
        return fig
        
    names = [s["name"].replace("_", " ").capitalize() for s in scenarios]
    p_imp = [s["p_improvement"] * 100 for s in scenarios]
    scen_colors = get_config()["app"]["scenario_colors"]
    colors = [scen_colors.get(s["name"], scen_colors["custom"]) for s in scenarios]
    
    fig.add_trace(go.Bar(
        x=p_imp,
        y=names,
        orientation='h',
        marker_color=colors,
    ))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Probability of Improvement (%)",
        yaxis_title="",
        xaxis_range=[0, 100]
    )
    return fig
