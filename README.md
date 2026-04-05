# Cloud-Native Finance ETL & AI Pipeline

[![Python Pipeline](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Google BigQuery](https://img.shields.io/badge/Google%20Cloud-BigQuery-4285F4?logo=google-cloud)](https://cloud.google.com/bigquery)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini%20Flash-4285F4?logo=google-cloud)](https://cloud.google.com/vertex-ai)

> **Architect:** Magno Freitas - Senior Software/Data Engineer  
> **Phase:** 2 (Business Automation & Cloud Data Pipeline)

An enterprise-grade, localized Data Engineering toolset engineered for ingesting, transforming, and centralizing heavily unstructured financial spreadsheets into an analytical Data Warehouse (Google BigQuery). It integrates Google Vertex AI to automatically synthesize executive financial summaries.

## 🚀 Business Impact & Architecture

Financial reconciliation often relies on disparate, manually-edited Excel files containing inconsistent formatting (BRL vs USD commas, missing values, string encoding). 

This pipeline acts as a robust local ingestion layer that minimizes Cloud cost exposure while maximizing data quality. Once transformed (`Pandas`), data is efficiently upserted to **Google BigQuery** for high-performance querying. Simultaneously, **Google Vertex AI** (`gemini-flash-latest`) is leveraged to analyze the processed batch and output highly actionable executive summaries, connecting raw numbers to business strategy.

### Core Workflows
1. **Extraction (Local Robustness):** Safely loads multi-file, potentially malformed Excel reports. Supports batch processing of up to 5 concurrent spreadsheets.
2. **Transformation (Cleaning & Auditing):** Utilizes `pandas` to forcefully standardize dates, currencies (BRL/USD numerical sanitization), classify transaction statuses, and purge empty artifacts. 
3. **Loading (Cloud Upsertion):** Directly syncs the heavily sanitized datasets into Google BigQuery using append/merge patterns, preparing the schema for analytical modeling.
4. **Generative Feedback (Vertex AI):** Consumes key daily metrics (e.g., total processed volume, pending liabilities, top clients) and generates an AI-driven, executive read-out.

## 🛠️ Tech Stack & Decisions
* **Python:** Chosen for its unmatched ecosystem in Data Engineering and local automation capabilities (avoiding GitHub Actions headless blockages on external sites).
* **Pandas & NumPy:** For high-speed, vectorized data transformations and cleanup.
* **Google Cloud BigQuery:** Serving as our highly scalable Data Warehouse.
* **Google Vertex AI (`gemini-flash`):** Used over other LLMs for its robust reasoning capabilities regarding financial numeric summarizations at an optimal cost.
* **Streamlit:** Local, no-code-feeling UI preventing finance staff from interacting with terminal windows.
* **MS Teams Webhooks & Windows Task Scheduler:** High-quality asynchronous corporate alerts and dark batch automation.

## 📋 Installation & Fast Start

1. **Clone and Configure**
   ```bash
   git clone https://github.com/magno-freitas/finance-etl-pipeline.git
   cd finance-etl-pipeline
   ```

2. **Environment Assembly**
   Create a virtual environment and load dependencies:
   ```powershell
   python base -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Cloud Authentication Setup**
   Place your GCP Service Account Key at the root level and configure the `.env` file (see `.env.example`).
   ```env
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_APPLICATION_CREDENTIALS="path/to/sa-key.json"
   GOOGLE_CLOUD_LOCATION=us-central1
   TEAMS_WEBHOOK_URL="your-teams-webhook"
   ```

## 🚀 How to Execute (Phase 3 Enterprise Options)

### Opção 1: The Graphic Interface (Streamlit)
To start the modern GUI and do drag-and-drop accounting without terminal commands, run:
```powershell
.\.venv\Scripts\python.exe -m streamlit run src/app.py
```

### Opção 2: The Terminal Orchestrator (Manual Batch)
Drop the raw, unstructured `.xlsx` files into `data/raw/` and execute the orchestrator:
```powershell
.\.venv\Scripts\python.exe src/main.py
```

### Opção 3: True Automation (Windows Task Scheduler)
Execute the script `/scripts/setup_task.ps1` as an Administrator to implement the 18:00 Zero-Click daily task.

## 🔒 Security & Best Practices

- **Zero Cloud Exposure:** Raw business files remain strictly on the local drive until sanitized and securely transported to BigQuery.
- **Strict Typing & Sanitization:** Floating point truncation and Brazilian format conversions are strongly enforced to prevent financial miscalculations.
- **Traceability:** Local copies of the cleaned datasets are kept in `data/processed/` with execution timestamps for audit trailing.

---
*This repository is part of Magno Freitas' Senior Hub Portfolio. Designed for real-world reliability, cost-efficiency, and scalability within modern cloud ecosystems.*