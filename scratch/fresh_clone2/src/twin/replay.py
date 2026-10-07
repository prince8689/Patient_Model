from collections.abc import Generator

import pandas as pd


class StreamReplayer:
    def __init__(self, raw_path: str, patient_id: str, start_time: str = None, end_time: str = None):
        self.df = pd.read_csv(raw_path)
        self.df = self.df[self.df["patient_id"] == patient_id].copy()
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
        
        if start_time:
            self.df = self.df[self.df["timestamp"] >= pd.to_datetime(start_time)]
        if end_time:
            self.df = self.df[self.df["timestamp"] <= pd.to_datetime(end_time)]
            
        self.df = self.df.sort_values("timestamp")
        
    def stream(self) -> Generator[dict, None, None]:
        for _, row in self.df.iterrows():
            d = row.to_dict()
            d["timestamp"] = d["timestamp"].isoformat()
            yield d
