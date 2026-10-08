import pytest
import pandas as pd
from src.real_data.gaps import compute_slots_and_gaps

def test_slots_and_gaps_handmade():
    # Observed slots 0, 1, 4 (missing 2, 3) -> gap of 2 slots, length 30 minutes
    # first timestamp at 00:00
    ts = pd.to_datetime([
        "2026-01-01 00:00:00",
        "2026-01-01 00:15:00",
        "2026-01-01 01:00:00"  # slot 4
    ])
    
    total_slots, missing_slots, gaps = compute_slots_and_gaps(ts, slot_interval_minutes=15)
    
    assert total_slots == 5
    assert missing_slots == 2
    assert gaps == [30.0]
