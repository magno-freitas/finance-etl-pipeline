import pandas as pd
import glob
import os
import io
import unicodedata
import warnings

def normalize_string(text):
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if unicodedata.category(c) != 'Mn')
    return text

def extract_dynamic_header_from_sheet(excel_file, sheet_name):
    try:
        # User Real (Not Ideal) - Excel tables often have 10-15 rows of garbage filters and aggregations at the top
        df_raw = excel_file.parse(sheet_name, nrows=40, header=None)
        
        # Aggressive drop of completely empty rows/cols to prevent NaN skewing
        df_raw.dropna(how='all', inplace=True)
        df_raw.dropna(axis=1, how='all', inplace=True)

        header_idx = 0
        keywords = ['conta', 'rotulos', 'row labels', 'descricao', 'numero do documento', 'customers', 'services', 'account', 'item', 'document number', 'memo']

        found = False
        for idx, row in df_raw.iterrows():
            row_vals = [normalize_string(val) for val in row.values]
            if any(kw in val for val in row_vals for kw in keywords):
                header_idx = idx
                found = True
                break
                
        # Read clean with correct header
        if found:
            df_clean = excel_file.parse(sheet_name, header=header_idx)
        else:
            df_clean = excel_file.parse(sheet_name, header=0)
        
        # Enterprise Sanitization
        df_clean.dropna(how='all', inplace=True) # Exclude entirely blank rows appended by Excel
        df_clean.dropna(axis=1, how='all', inplace=True) # Exclude entirely blank columns (prevents 16384+ column bloat)
        df_clean.columns = df_clean.columns.astype(str).str.strip()
        df_clean = df_clean.loc[:, ~df_clean.columns.str.contains('^unnamed', case=False)] # Extra safety against blank headers
        
        return df_clean
    except Exception as e:
        print(f"Warning: Could not parse sheet {sheet_name} due to: {str(e)}")
        return pd.DataFrame()

def extract_dynamic_header(file_obj):
    """
    Robust Schema Validation: scans ALL valid SHEETS to find the true accounting headers.
    Returns a concatenated dataframe correctly formatted and strongly typed.
    """
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
        
    try:
        xls = pd.ExcelFile(file_obj)
    except Exception as e:
        raise ValueError(f"Invalid Excel format or corrupted file: {str(e)}")

    all_dfs = []
    
    exclude_sheets = ['templates', 'dashboard', 'summary', 'resumo', 'metadata']
    
    # Catching 'User Real' Warnings like Openpyxl Data Validation issues
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for sheet in xls.sheet_names:
            if any(ex in normalize_string(sheet) for ex in exclude_sheets):
                continue
                
            print(f"Parsing sheet: {sheet}")
            df_sheet = extract_dynamic_header_from_sheet(xls, sheet)
            
            # Sub-sheet validation: Real users often leave empty placeholder sheets
            if df_sheet is None or df_sheet.empty or len(df_sheet.columns) < 2:
                print(f"Skipping {sheet}: Unusable data topology.")
                continue
            
            df_sheet['_source_sheet'] = sheet
            all_dfs.append(df_sheet)

    if all_dfs:
        df_final = pd.concat(all_dfs, ignore_index=True)
    else:
        df_final = pd.DataFrame()
        
    return df_final
