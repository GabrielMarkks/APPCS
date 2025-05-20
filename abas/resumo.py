import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ga4_utils import (
    fetch_ga4_kpis,
    fetch_conversoes_por_canal,
    fetch_produtos_mais_vendidos,
    fetch_regioes_mais_acessadas
)
from diagnostico_utils import gerar_prompt, chamar_ia, exportar_docx

def aba_resumo_executivo(property_id, start_date, end_date, customer_root):
    st.subheader("📌 Resumo Executivo de Performance")

    st.markdown("""
### Como interpretar o Resumo Executivo
Este painel resume os principais indicadores de performance do seu e-commerce com base nos dados do GA4.

- **Receita Total:** Valor total vendido no período.
- **Vendas:** Número de transações realizadas.
- **Taxa de Conversão:** Proporção entre sessões e compras.
- **Ticket Médio:** Valor médio por compra.
- **Destaques:** Canais, produtos e regiões com melhor desempenho.
""")

    # === KPIs ATUAIS ===
    kpis = fetch_ga4_kpis(property_id, start_date, end_date, customer_root)

    # === CÁLCULO DO PERÍODO ANTERIOR ===
    inicio_dt = datetime.strptime(start_date, "%Y-%m-%d")
    fim_dt = datetime.strptime(end_date, "%Y-%m-%d")
    dias_periodo = (fim_dt - inicio_dt).days + 1

    inicio_anterior = (inicio_dt - timedelta(days=dias_periodo)).strftime("%Y-%m-%d")
    fim_anterior = (inicio_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    kpis_anterior = fetch_ga4_kpis(property_id, inicio_anterior, fim_anterior, customer_root)

    def calc_var(novo, antigo):
        if antigo == 0:
            return "n/d"
        return f"{((novo - antigo) / antigo) * 100:.2f}%"

    variacoes = {
        "receita": calc_var(kpis["receita_total"], kpis_anterior["receita_total"]),
        "vendas": calc_var(kpis["vendas"], kpis_anterior["vendas"]),
        "conversao": calc_var(kpis["taxa_conversao"], kpis_anterior["taxa_conversao"]),
        "ticket": calc_var(kpis["ticket_medio"], kpis_anterior["ticket_medio"])
    }

    # === KPIs + VARIAÇÕES ===
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Total", f"R$ {kpis['receita_total']:,.2f}".replace(".", ","), variacoes["receita"])
    col2.metric("Vendas", f"{kpis['vendas']}", variacoes["vendas"])
    col3.metric("Taxa de Conversão", f"{kpis['taxa_conversao']:.2%}", variacoes["conversao"])
    col4.metric("Ticket Médio", f"R$ {kpis['ticket_medio']:,.2f}".replace(".", ","), variacoes["ticket"])

    # === DESTAQUES ===
    canais = fetch_conversoes_por_canal(property_id, start_date, end_date, customer_root)
    produtos = fetch_produtos_mais_vendidos(property_id, start_date, end_date, customer_root)
    regioes = fetch_regioes_mais_acessadas(property_id, start_date, end_date, customer_root)

    top_canal = canais.iloc[0]['Canal'] if not canais.empty else 'N/D'
    top_produto = produtos.iloc[0]['Produto'] if not produtos.empty else 'N/D'
    top_regiao = regioes.iloc[0]['Cidade'] if not regioes.empty else 'N/D'

    st.markdown("""
### 🏆 Destaques Estratégicos
- **Top Canal:** Origem de tráfego com maior geração de receita.
- **Top Produto:** Produto com maior valor vendido no período.
- **Top Região:** Cidade com maior número de acessos.
""")
    col5, col6, col7 = st.columns(3)
    col5.success(f"Top Canal: {top_canal}")
    col6.success(f"Top Produto: {top_produto}")
    col7.success(f"Top Região: {top_regiao}")

    # === DIAGNÓSTICO RESUMIDO ===
    with st.expander("🤖 Ver Diagnóstico Estratégico com IA"):
        dados_sinteticos = {
            "kpis": kpis,
            "top_canal": top_canal,
            "top_produto": top_produto,
            "top_regiao": top_regiao
        }
        prompt = gerar_prompt(dados_sinteticos, customer_root or "Todos", start_date, end_date)
        resultado = chamar_ia(prompt)
        st.text_area("Diagnóstico IA:", resultado, height=300)

        docx_path = exportar_docx(resultado)
        with open(docx_path, "rb") as f:
            st.download_button("📥 Baixar Relatório .docx", f, file_name="resumo-executivo.docx")
