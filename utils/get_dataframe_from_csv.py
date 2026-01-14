import pandas as pd

def get_dataframe_from_csv(filepath: str, columns: list[str]):
    df = pd.read_csv(filepath, encoding='cp1252')
    return df[columns]