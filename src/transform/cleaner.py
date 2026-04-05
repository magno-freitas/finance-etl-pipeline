import pandas as pd
import numpy as np
import re

def parse_currency(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    val = str(val).strip()
    if not val or val.lower() == 'nan':
        return 0.0
        
    # User Real: BRL formatting R$ -1.500,00 vs US formatting -1,500.00
    val = re.sub(r'[^\d\,\.-]', '', val)
    if not val:
        return 0.0
        
    # Logic: if both . and , exist, the last one is the decimal separator
    if '.' in val and ',' in val:
        if val.rfind(',') > val.rfind('.'):
            # European/LATAM: 1.500,00 -> 1500.00
            val = val.replace('.', '').replace(',', '.')
        else:
            # US/Accounting: 1,500.00 -> 1500.00
            val = val.replace(',', '')
    elif ',' in val:
        # Check if it's like 100,00 (decimal) or 100,000 (thousand) - heuristics
        parts = val.split(',')
        if len(parts[-1]) == 2: # Likely a decimal (e.g. ,00)
            val = val.replace(',', '.')
        else:
            val = val.replace(',', '') # Probably thousand separator
            
    try:
        return round(float(val), 2)
    except ValueError:
        return 0.0

def fuzzy_match_col(col_name, master_mapping):
    c = str(col_name).lower().strip()
    for target, patterns in master_mapping.items():
        if any(p in c for p in patterns):
            return target
    return col_name

CATEGORY_MAPPING = {
    'fx': ['variação', 'variacao', 'cambial', 'fx', 'cambio', 'exchange'],
    'reversal': ['reversão', 'reversao', 'reversal'],
    'provision': ['provisão', 'provisao', 'provision', 'contratos wms', 'projeto', 'aguardando', 'back log', 'accrual'],
    'revenue': ['reconhecimento', 'faturamento', 'receita', 'revenue', 'ff', 't&m', 'faturado', 'professional services', 'licenças', 'licenses', 'sales', 'hardware', 'software', 'support', 'hw -', 'swp -', 'robos', 'carregadores', 'amr', 'third party', 'workstation', 'wear part', '42000', '40010', '43005', '41000', '43020', '44000', '44015', '44010', 'bartender', 'framework', 'squad', '3pl', 'wa admin', 'api rest', 'conversion', 'comission', 'subscription', 'renewal', 'multilog', 'legado', 'tecnológica', 'psg - sce services br', 'psg - sce prepay br', 'renner', 'camicado', 'adimax', 'lojas renner', 'kbr', 'psg - sce services cl', 'ms - sce wms admin', 'cl_610', 'brl_650_655', 'san bernardo', 'expansión renca', 'antofagasta', 'horas variáveis', 'badamax', 'preunic', 'soprole', 'emasa', 'comercial mk', 'alpargatas', 'cobasi', 'clp_230', 'brl_230', 'körber supply chain', 'uvi tech', 'qu-icl', 'qu-kcl', 'op-kcl', 'k.motion']
}

def categorize_transaction(context_val):
    if pd.isna(context_val):
        txt = ''
    else:
        txt = str(context_val).lower()
        
    for category, keywords in CATEGORY_MAPPING.items():
        if any(x in txt for x in keywords):
            return category

    return 'unmapped'

def process_infios_receita(df_receita, df_latam):
    print("Applying Enterprise Corporate Accounting Rules (Full DRE)...")
    
    frames = []
    if isinstance(df_receita, pd.DataFrame) and not df_receita.empty:
        frames.append(df_receita)
    if isinstance(df_latam, pd.DataFrame) and not df_latam.empty:
        frames.append(df_latam)
        
    if not frames:
        return pd.DataFrame(), {}
        
    df_combined = pd.concat(frames, ignore_index=True)
    
    # Fuzzy matching dictionary
    fuzzy_col_mapping = {
        'internal_id_rv_memo': ['conta (linha)', 'rótulos', 'row labels', 'services', 'account', 'conta', 'gl account'],
        'description': ['descrição', 'descri', 'item', 'memo', 'detalhe', ' particulars'],
        'document_number': ['número do documento', 'sales order', 'document number', 'doc num', 'je text', 'documento'],
        'balance': ['total', 'soma de total', 'valor', 'amount', 'balance', 'montante', 'saldo', 'total/financeiro']
    }
    
    df_combined.columns = [fuzzy_match_col(c, fuzzy_col_mapping) for c in df_combined.columns]
    
    final_cols = {}
    for col in df_combined.columns.unique():
        data = df_combined[col]
        if isinstance(data, pd.DataFrame):
            final_cols[col] = data.bfill(axis=1).iloc[:, 0]
        else:
            final_cols[col] = data
            
    df_combined = pd.DataFrame(final_cols)
    
    if 'internal_id_rv_memo' not in df_combined.columns and not df_combined.columns.empty:
        df_combined.rename(columns={df_combined.columns[0]: 'internal_id_rv_memo'}, inplace=True)
        
    if 'document_number' not in df_combined.columns:
        df_combined['document_number'] = 'No-Doc'
    if 'description' not in df_combined.columns:
        df_combined['description'] = ''
        
    account_source = (
        df_combined.get('description', '').fillna('').astype(str)
        + ' '
        + df_combined['internal_id_rv_memo'].fillna('').astype(str)
    )
    # Strict account extraction to avoid capturing years like 2025/2026 as account codes.
    df_combined['derived_account'] = account_source.str.extract(r'\b(4\d{4})\b', expand=False)
    df_combined['derived_account'] = df_combined['derived_account'].ffill()
    
    df_tx = df_combined.dropna(subset=['derived_account', 'internal_id_rv_memo']).copy()
    df_tx = df_tx[~df_tx['internal_id_rv_memo'].astype(str).str.contains('Total|Soma|Grand|Result|nan', case=False, na=False)]

    if 'balance' in df_tx.columns:
        df_tx['balance'] = df_tx['balance'].apply(parse_currency)
    else:
        num_cols = df_tx.select_dtypes(include=[np.number]).columns
        if not num_cols.empty:
             df_tx['balance'] = df_tx[num_cols[-1]].apply(parse_currency)
        else:
            df_tx['balance'] = 0.0
            
    df_tx = df_tx[df_tx['balance'] != 0.0]

    df_tx['context_string'] = df_tx.get('description', pd.Series([''] * len(df_tx), index=df_tx.index)).fillna('').astype(str) + " " + df_tx['internal_id_rv_memo'].fillna('').astype(str)
    
    df_tx['category'] = df_tx['context_string'].apply(categorize_transaction)

    metrics = {
        "total_revenue": round(float(df_tx.loc[df_tx['category'] == 'revenue', 'balance'].sum()), 2),
        "total_reversals": round(float(df_tx.loc[df_tx['category'] == 'reversal', 'balance'].sum()), 2),
        "total_provisions": round(float(df_tx.loc[df_tx['category'] == 'provision', 'balance'].sum()), 2),
        "variacao_cambial": round(float(df_tx.loc[df_tx['category'] == 'fx', 'balance'].sum()), 2)
    }

    df_orphan = df_tx[df_tx['category'] == 'unmapped'].copy()
    if not df_orphan.empty:
        df_orphan['tag'] = 'Divergência Thiago (Unmapped Item/Account)'
        
    import os
    os.makedirs("data/processed", exist_ok=True)
    
    if not df_orphan.empty:
        df_orphan.to_excel("data/processed/erros.xlsx", index=False)
    else:
        pd.DataFrame(columns=df_tx.columns).to_excel("data/processed/erros.xlsx", index=False)

    print(f"Enterprise Transformation complete. Total Revenue mapped: {metrics['total_revenue']:.2f}")
    return df_tx, metrics

