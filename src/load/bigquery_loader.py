import os
import logging
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, GoogleAPIError

logger = logging.getLogger(__name__)

def _normalize_credentials_path() -> str:
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    cred_path = str(cred_path).strip().strip('"').strip("'")
    if not cred_path:
        return ""

    if not os.path.isabs(cred_path):
        cred_path = os.path.abspath(cred_path)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
    return cred_path

def get_bq_client():
    """
    Initializes a robust BigQuery client utilizing the credentials from the explicit .env path.
    """
    try:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            # Keep running even if python-dotenv is unavailable.
            pass

        cred_path = _normalize_credentials_path()

        # Check if GOOGLE_APPLICATION_CREDENTIALS is in the environment
        if not cred_path:
            logger.warning("No GOOGLE_APPLICATION_CREDENTIALS mapped. Skipping BigQuery Connection.")
            return None

        if not os.path.exists(cred_path):
            logger.warning(f"Credential file not found at path: {cred_path}")
            return None
            
        client = bigquery.Client()
        return client
    except Exception as e:
        logger.error(f"Failed to initialize BigQuery client (Service Account Error): {e}")
        return None

def enforce_bq_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enterprise Defensive Data Formatting:
    BigQuery rejects dirty types (e.g., mixed float/str in the same column, NaN vs None).
    """
    # Keep only curated columns for DWH stability. Raw spreadsheet columns can contain mixed object types.
    curated_cols = [
        'internal_id_rv_memo',
        'description',
        'document_number',
        'derived_account',
        'balance',
        'context_string',
        'category',
        'tag',
        '_source_sheet',
        '_source_file',
    ]

    available_cols = [c for c in curated_cols if c in df.columns]
    df_bq = df.loc[:, available_cols].copy()

    # Cast known numeric columns strictly
    if 'balance' in df_bq.columns:
        df_bq['balance'] = pd.to_numeric(df_bq['balance'], errors='coerce').fillna(0.0).astype(float)

    # Cast all strings explicitly and handle NaN/blank-like values
    string_cols = ['internal_id_rv_memo', 'description', 'document_number', 'derived_account', 'context_string', 'category', 'tag', '_source_sheet', '_source_file']
    for col in string_cols:
        if col in df_bq.columns:
            df_bq[col] = (
                df_bq[col]
                .fillna('')
                .astype(str)
                .str.strip()
                .replace({'nan': '', 'None': ''})
            )

    # Add a processing timestamp for auditing
    df_bq['extracted_at'] = pd.Timestamp.utcnow()
    
    return df_bq

def upsert_to_bigquery(
    df: pd.DataFrame,
    dataset_id: str = "finance_analytics",
    table_id: str = "revenue_transactions"
) -> bool:
    """
    Google-tier BigQuery Ingestion.
    Ensures dataset/table existence, enforces schema, and validates data insertion.
    """
    client = get_bq_client()
    if not client:
        return False

    if df.empty:
        logger.warning("Empty DataFrame passed to BigQuery Loader. Skipping.")
        return False

    # Defensive formatting
    df_bq = enforce_bq_schema(df)
    
    try:
        # Construct exact table reference
        project = client.project or os.environ.get("GOOGLE_CLOUD_PROJECT", "finance-analytics-mvf")
        dataset_ref = bigquery.DatasetReference(project, dataset_id)
        table_ref = dataset_ref.table(table_id)
        full_table_id = f"{project}.{dataset_id}.{table_id}"

        # Ensure Dataset Exists
        try:
            client.get_dataset(dataset_ref)
        except NotFound:
            print(f"Dataset {dataset_id} not found. Creating in multi-region US...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset, timeout=30)
            
        print(f"Streaming {len(df_bq)} sanitized rows into BigQuery ({full_table_id})...")

        # Load job config
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE, # Overwrites for daily idempotency (Stateless DRE)
            autodetect=True, # Auto-generate schema based on curated df_bq types
        )
        
        job = client.load_table_from_dataframe(df_bq, table_ref, job_config=job_config)
        job.result()  # Blocks until load is completed

        table = client.get_table(table_ref)
        print(f"BQ Stream Success: Total rows resting in DWH: {table.num_rows}")  
        return True
        
    except GoogleAPIError as api_err:
        print(f"Google Cloud API Exception: {api_err}")
        return False
    except Exception as e:
        print(f"Fatal Error during BigQuery Load: {e}")
        return False

