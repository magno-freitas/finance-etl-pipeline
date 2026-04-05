import os
import glob
import pandas as pd
from sqlalchemy import create_engine, text

# ==============================================================================
# INFIOS FINANCE OS - ETL PARA POSTGRESQL (MODELAGEM 3FN OLTP)
# Script de inserção massiva usando chaves dimensionais e upsert inteligente.
# ==============================================================================

# ======================= ATENÇÃO MAGNO =======================
# Troque a variável DB_PASS abaixo pela SENHA que você colocou 
# ao instalar o PostgreSQL na sua máquina.
# =============================================================
DB_USER = "postgres"
DB_PASS = "Doku!031207" 
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "infios_erp"

# Motor de conexão do SQLAlchemy
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def get_latest_csv():
    """Busca o último CSV processado gerado pela automação."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    processed_dir = os.path.join(base_dir, "data", "processed")
    
    csv_files = glob.glob(os.path.join(processed_dir, "cleaned_financials_*.csv"))
    if not csv_files:
         # Try the alternate naming convention just in case
         csv_files = glob.glob(os.path.join(processed_dir, "cleaned_infios_financials_*.csv"))
         
    if not csv_files:
         raise FileNotFoundError("Nenhum CSV limpo encontrado em data/processed. Rode o app.py primeiro!")
    
    return max(csv_files, key=os.path.getctime)

def main():
    print(f"[{pd.Timestamp.now()}] Iniciando DWH Sync Local (PostgreSQL)...")
    
    latest_csv = get_latest_csv()
    print(f"-> Lendo o arquivo: {os.path.basename(latest_csv)}")
    df = pd.read_csv(latest_csv)
    
    # 1. Tratamento Básico de Nulos
    print("-> Padronizando registros nulos...")
    df['client_description'] = df.get('client_description', df.get('Customers')).fillna('NÃO INFORMADO')
    df['status'] = df.get('status', pd.Series('NÃO INFORMADO', index=df.index)).fillna('NÃO INFORMADO')
    df['_source_file'] = df.get('_source_file', df.get('_source_sheet', pd.Series('DESCONHECIDO', index=df.index))).fillna('DESCONHECIDO')
    
    # Prevenção caso as colunas venham de versões antigas do CSV
    df['category'] = df.get('category', df.get('categoria_contabil', pd.Series('unmapped', index=df.index)))

    print("-> Sincronizando Tabelas de Dimensão (Clientes, Departamentos, Origens)...")
    with engine.connect() as conn:
        # 2A. Inserção Dinâmica - Clientes 
        for c in df['client_description'].unique():
            conn.execute(
                text("INSERT INTO dim_cliente (nome_cliente) VALUES (:c) ON CONFLICT (nome_cliente) DO NOTHING"), 
                {"c": str(c)[:250]} # Evita erro de limite de caracteres
            )
            
        # 2B. Inserção Dinâmica - Status (Usando como Departamento para manter a estrutura)
        for d in df['status'].unique():
            conn.execute(
                text("INSERT INTO dim_departamento (codigo_departamento) VALUES (:d) ON CONFLICT (codigo_departamento) DO NOTHING"), 
                {"d": str(d)[:250]}
            )
            
        # 2C. Inserção Dinâmica - Origem
        for s in df['_source_file'].unique():
            conn.execute(
                text("INSERT INTO dim_origem (source_sheet) VALUES (:s) ON CONFLICT (source_sheet) DO NOTHING"), 
                {"s": str(s)[:100]}
            )
        conn.commit()
        
        print("-> Mapeando IDs (Foreign Keys) para a Tabela Fato...")
        dim_cliente = pd.read_sql(text("SELECT id_cliente, nome_cliente FROM dim_cliente"), conn)
        dim_dep = pd.read_sql(text("SELECT id_departamento, codigo_departamento FROM dim_departamento"), conn)
        dim_origem = pd.read_sql(text("SELECT id_origem, source_sheet FROM dim_origem"), conn)

    # Renomeando as colunas do banco para dar o merge no Pandas
    dim_cliente.rename(columns={'nome_cliente': 'client_description'}, inplace=True)
    dim_dep.rename(columns={'codigo_departamento': 'status'}, inplace=True)
    dim_origem.rename(columns={'source_sheet': '_source_file'}, inplace=True)

    df = df.merge(dim_cliente, on='client_description', how='left')
    df = df.merge(dim_dep, on='status', how='left')
    df = df.merge(dim_origem, on='_source_file', how='left')

    # 4. Modelando a Tabela Fato
    print("-> Preparando carga massiva para a fato_receita...")
    
    # Criando chaves falsas caso não existam no arquivo
    df['document_number'] = df.get('document_number', pd.Series('N/A', index=df.index))
    df['revenue_record'] = df.get('Criar a partir de', pd.Series('N/A', index=df.index))
    df['internal_id_memo'] = df.get('observations', pd.Series('N/A', index=df.index))
    
    fato_df = pd.DataFrame({
        'id_cliente': df['id_cliente'],
        'id_departamento': df['id_departamento'],
        'id_origem': df['id_origem'],
        'document_number': df['document_number'].fillna('N/A').astype(str),
        'revenue_record': df['revenue_record'].fillna('N/A').astype(str),
        'internal_id_memo': df['internal_id_memo'].fillna('N/A').astype(str),
        
        'data_competencia': pd.to_datetime(df.get('payment_date', df.get('Data')), errors='coerce'), 
        'valor_brl': pd.to_numeric(df.get('amount_brl', df.get('balance')), errors='coerce').fillna(0),
        'categoria_contabil': df['category'].astype(str)
    })

    # 5. Carga Bruta! (append na tabela fato)
    try:
        fato_df.to_sql('fato_receita', engine, if_exists='append', index=False)
        print(f"[{pd.Timestamp.now()}] SUCESSO! {len(fato_df)} registros de faturamento inseridos no PostgreSQL!")
        print("-> Abra o pgAdmin, clique em 'fato_receita' e comemore: Você dominou o ETL Relacional OLTP.")
    except Exception as e:
        print(f"ERRO DE INSERÇÃO: {e}")

if __name__ == "__main__":
    main()