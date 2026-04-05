import pandas as pd
from src.extract.loader import load_infios_data
from src.transform.cleaner import process_infios_receita

df_rec, df_lat = load_infios_data("data/raw")
if df_rec.empty and df_lat.empty:
    df_rec, df_lat = load_infios_data(".")

df_tx, metrics = process_infios_receita(df_rec, df_lat)
print("METRICS:", metrics)
print("Sample Balance Column Summary:")
print(df_tx['balance'].describe())

print("\nReversao Rows Sample:")
print(df_tx[df_tx['balance'] < 0][['description', 'internal_id_rv_memo', 'document_number', 'balance']].head(10))
