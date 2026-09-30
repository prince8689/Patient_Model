import sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.utils.config import load_config
from src.twin.timeline import build_timeline, get_state_at
import dataclasses

def main():
    config = load_config()
    df_tl = build_timeline("P007", config=config)
    alerts = df_tl[(df_tl["alert_fired"] == True) & (df_tl["probability"] > 0)]
    if not alerts.empty:
        snap_ts = alerts.iloc[-1]["timestamp"].isoformat()
    else:
        snap_ts = df_tl.iloc[-1]["timestamp"].isoformat()
    state = get_state_at("P007", snap_ts, config)
    
    def asdict_factory(data):
        return {k: v for k, v in data if v is not None}
    
    print(json.dumps(dataclasses.asdict(state), indent=2, default=str))

if __name__ == "__main__":
    main()
