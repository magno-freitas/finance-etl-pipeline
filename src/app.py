import streamlit as st
import pandas as pd
import time
import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transform.cleaner import process_infios_receita
from ai.vertex_summarizer import generate_financial_summary
from notify.teams_notifier import send_teams_notification
from extract.loader import extract_dynamic_header
from load.bigquery_loader import upsert_to_bigquery

st.set_page_config(page_title="Infios Finance OS", page_icon="🏢", layout="wide")

st.title("InFIOS Finance OS - Revenue Accounting")
st.markdown("Automated Daily Workflow for **Global Accounting** DRE & Provisão Reconciliation (Includes 41000, 43020, Intercompany).")

st.sidebar.header("📁 Data Upload (Local)")
st.sidebar.info("Upload standard Infios business files (Receitas + LATAM). No manual cleaning required. The system will handle filters and messy headers automatically.")

upload_receita = st.sidebar.file_uploader("Upload BR_Analise (Detalhamento Receitas)", type=['xlsx', 'xls', 'xlsm', 'xlsb'])
upload_latam = st.sidebar.file_uploader("Upload LATAM Baseline", type=['xlsx', 'xls', 'xlsm', 'xlsb'])

btn_process = st.sidebar.button("⚙️ Execute DRE Match & Cloud Sync", type="primary")

if btn_process:
    if not upload_receita or not upload_latam:
         st.error("⚠️ Missing Uploads: Both global forms are required for full DRE reconciliation.")
    else:
         start_time = time.time()
         
         status = st.status("Initializing Enterprise ETL Pipeline...", expanded=True)
         
         try:
             status.update(label="Scanning files & Extracting dynamically...", state="running")
             df_receita = extract_dynamic_header(upload_receita)
             df_latam = extract_dynamic_header(upload_latam)
             
             if df_receita.empty and df_latam.empty:
                 status.update(label="Pipeline Halted: No interpretable accounting tables found.", state="error")
                 st.error("Failed to detect valid accounting properties in the provided files. Ensure the uploaded spreadsheets contain revenue data.")
                 st.stop()
                 
             status.update(label="Applying Core DRE Analytics & Typings...", state="running")
             df_clean, metrics = process_infios_receita(df_receita, df_latam)
             
             err_file_path = os.path.join("data", "processed", "erros.xlsx")
             divergent_count = len(pd.read_excel(err_file_path)) if os.path.exists(err_file_path) else 0

             status.update(label="Synchronizing Data Warehouse (Google BigQuery)...", state="running")
             bq_success = upsert_to_bigquery(df_clean)

             end_time = time.time()
             exec_diff = end_time - start_time

             status.update(label="Calling Google genai (Vertex) for readouts...", state="running")
             genai_summary = generate_financial_summary(metrics, exec_diff)
             send_teams_notification(metrics, genai_summary, divergent_count, exec_diff)

             status.update(label=f"Pipeline Fully Reconciled & Synced in {exec_diff:.2f}s", state="complete")
             
             if bq_success:
                  st.success("✅ **Cloud Success:** Dataset successfully streamed to BigQuery (finance_analytics.revenue_transactions).")
             else:
                  st.warning("⚠️ **Data Warehouse Bypass:** Local DRE processing succeeded, but BigQuery synchronization failed or was skipped (Check logs/credentials).")

             col1, col2, col3, col4, col5 = st.columns(5)
             col1.metric("Accounting (Total Créditos)", f"R$ {metrics.get('total_revenue', 0):,.2f}")
             col2.metric("Accounting (Total Reversões)", f"R$ {metrics.get('total_reversals', 0):,.2f}")
             col3.metric("Accounting (Provisão)", f"R$ {metrics.get('total_provisions', 0):,.2f}")
             col4.metric("Cambial (VAR)", f"R$ {metrics.get('variacao_cambial', 0):,.2f}")
             col5.metric(label="Thiago Divergence Count", value=divergent_count,
                         delta="-0% Error Leakage" if divergent_count == 0 else f"{divergent_count} Escapes",
                         delta_color="normal" if divergent_count == 0 else "inverse")

             st.divider()

             c_exec, c_err = st.columns([1, 1])

             with c_exec:
                  st.markdown("### 🤖 Vertex AI Executive Readout")
                  st.info(genai_summary)

             with c_err:
                  st.markdown("### 🛑 Divergência Tracker (Global Accounts)")
                  if os.path.exists(err_file_path):
                       df_erros_disp = pd.read_excel(err_file_path)
                       st.dataframe(df_erros_disp, use_container_width=True)
                  else:
                       st.write("No divergencies flagged.")

             with st.expander("📄 View Fully Synchronized Internal Dataset"):
                  if not df_clean.empty:
                      st.dataframe(df_clean.head(100), use_container_width=True)
                  else:
                      st.write("Dataset resulted in 0 valid items after DRE filtration.")
             st.balloons()
             
         except Exception as e:
             status.update(label="Fatal Engine Fault.", state="error")
             st.error("### System Crash - Diagnostic Log")
             st.code(traceback.format_exc(), language='python')
             st.warning("A falha acima ocorreu na injeção bruta dos dados. Revise se os extratos não vieram completamente corrompidos ou em branco do SAP/NetSuite.")

