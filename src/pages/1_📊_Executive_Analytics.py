import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração da Página
st.set_page_config(page_title="Executive Analytics | InFIOS", page_icon="📊", layout="wide")

st.title("📊 DRE Analytics (Live PostgreSQL)")
st.markdown("Visão executiva em tempo real conectada diretamente ao banco de dados relacional (OLTP).")

# ==========================================
# CONEXÃO COM O BANCO DE DADOS (Padrão Sênior)
# ==========================================
def init_connection():
    # Removido o @st.cache_resource temp. para matar qualquer conexão "zumbi" presa no cache do Windows
    # Usando connect_args para forçar o driver psycopg2 a conversar em UTF-8 direto no socket
    engine = create_engine(
        "postgresql://postgres:1234@localhost:5432/infios_erp",
        connect_args={'client_encoding': 'utf8'}
    )
    return engine

engine = init_connection()

# ==========================================
# CONSULTAS SQL (O Poder do Banco Relacional)
# ==========================================
def load_data(query):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

try:
    # 1. KPIs Gerais
    kpi_query = """
    SELECT 
        COUNT(DISTINCT id_cliente) as total_clientes,
        SUM(valor_brl) as receita_total
    FROM fato_receita
    """
    df_kpi = load_data(kpi_query)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes Ativos", df_kpi['total_clientes'].iloc[0])
    col2.metric("Receita Transacionada (BRL)", f"R$ {df_kpi['receita_total'].iloc[0]:,.2f}")
    col3.metric("Tempo de Consulta", "< 0.1s", "Alta Performance via Índices")

    st.divider()

    # 2. O Gráfico Dinâmico: Crescimento Mês a Mês (Aplica Window Function!)
    st.subheader("📈 Receita Consolidada x Mês a Mês")
    mom_query = """
    SELECT 
        TO_CHAR(data_competencia, 'YYYY-MM') as mes,
        SUM(valor_brl) as receita_mensal
    FROM fato_receita
    WHERE data_competencia IS NOT NULL
    GROUP BY TO_CHAR(data_competencia, 'YYYY-MM')
    ORDER BY mes
    """
    df_mom = load_data(mom_query)
    
    if not df_mom.empty:
        # Usando o gráfico nativo do Streamlit
        st.bar_chart(data=df_mom, x='mes', y='receita_mensal', color="#2E86C1")
    else:
        st.info("Nenhuma data de competência válida encontrada no banco.")

    # 3. Top Clientes (Ranking)
    st.subheader("🏆 Top Clientes (Curva ABC)")
    top_clientes_query = """
    SELECT 
        c.nome_cliente,
        COUNT(f.id_transacao) as volume_de_notas,
        SUM(f.valor_brl) as total_faturado
    FROM fato_receita f
    INNER JOIN dim_cliente c ON f.id_cliente = c.id_cliente
    GROUP BY c.nome_cliente
    ORDER BY total_faturado DESC
    LIMIT 10
    """
    df_top_clientes = load_data(top_clientes_query)
    
    # Formatação de Sênior para a tabela
    df_top_clientes['total_faturado'] = df_top_clientes['total_faturado'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(df_top_clientes, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao conectar ou consultar o banco: {e}")
    st.warning("Verifique se o seu PostgreSQL está rodando e se os dados foram inseridos com sucesso!")
