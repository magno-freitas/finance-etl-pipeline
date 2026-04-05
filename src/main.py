import os
import time
import datetime
from extract.loader import load_infios_data
from transform.cleaner import process_infios_receita
from load.bigquery_loader import upsert_to_bigquery
from ai.vertex_summarizer import generate_financial_summary

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")

# Ensure required business process directories exist
os.makedirs(DATA_RAW, exist_ok=True)
os.makedirs(DATA_PROCESSED, exist_ok=True)

def main():
    print(f"[{datetime.datetime.now()}] Starting Infios Finance OS Data Workflow (Phase 2)...")
    start_time = time.time()
    
    # 1. Extraction: Load BR Analise and LATAM files uniquely
    # You must place original files in the workspace root or data/raw/
    df_receita, df_latam = load_infios_data(raw_dir=BASE_DIR) # Checking directly in the project root for testing
    
    if df_receita.empty and df_latam.empty:
         print("CRITICAL: Failed to locate raw Infios financial forms. Aborting pipeline.")
         return

    # 2. Transformation: Pure pandas DRE matching & compliance logic
    df_clean, metrics = process_infios_receita(df_receita, df_latam)
    
    # 3. Load: Upsert into BigQuery and Audit logs
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_path = os.path.join(DATA_PROCESSED, f"cleaned_infios_financials_{timestamp_str}.csv")
    
    if not df_clean.empty:
         df_clean.to_csv(processed_path, index=False)
         print(f"Saved local processed copy at: {processed_path}")
         upsert_to_bigquery(df_clean)
    
    # Measure total execution cycle for ROI reporting
    end_time = time.time()
    exec_diff = end_time - start_time
    
    # 4. Actionable AI: Vertex AI generates closing reporting compliance
    summary = generate_financial_summary(metrics, exec_diff)
    
    print("\n" + "="*60)
    print(" INFIOS OS: EXECUTIVE FINANCIAL SUMMARY ".center(60, "="))
    print("="*60)
    print(summary)
    print("="*60 + "\n")
    
    print(f"[{datetime.datetime.now()}] Infios Financial ETL successfully closed in {exec_diff:.2f} seconds.")

if __name__ == "__main__":
    main()
