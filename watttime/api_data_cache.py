import pandas as pd

class DataCache:
    def __init__(self, data: pd.DataFrame, time_col: str):
        self.data = data
        self.time_col = time_col

        data[self.time_col] = pd.to_datetime(data[self.time_col])

        self.start_time = data[self.time_col].iloc[0]
        self.end_time = data[self.time_col].iloc[-1]
        

    def get_data(
        self, 
        query_start: pd.Timestamp, 
        query_end: pd.Timestamp,
    ) -> pd.DataFrame:
        print(query_start)
        print(self.start_time)
        assert query_start < query_end
        assert self.start_time <= query_start + pd.Timedelta(minutes=5)
        assert query_end <= self.end_time

        return self.data[(self.data[self.time_col] >= query_start) & (self.data[self.time_col] < query_end)]

    
