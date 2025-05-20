import streamlit as st
from datetime import datetime, timedelta
from ga4_utils import fetch_ga4_kpis, fetch_funil_conversao, fetch_receita_transacoes_por_dia
import plotly.graph_objects as go
import plotly.express as px


def aba_vendas_receita(property_id, start_date, end_date, customer_root):
    st.subheader("🔹 Vendas e Receita")

    # KPIs atuais
    kpis = fetch_ga4_kpis(property_id, start_date, end_date, customer_root)

    # Período anterior
    inicio_dt = datetime.strptime(start_date, "%Y-%m-%d")
    fim_dt = datetime.strptime(end_date, "%Y-%m-%d")
    dias_periodo = (fim_dt - inicio_dt).days + 1
    inicio_ant = (inicio_dt - timedelta(days=dias_periodo)).strftime("%Y-%m-%d")
    fim_ant = (inicio_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    kpis_ant = fetch_ga4_kpis(property_id, inicio_ant, fim_ant, customer_root)

    def calc_var(novo, antigo):
        if antigo == 0:
            return "n/d"
        return f"{((novo - antigo) / antigo) * 100:.2f}%"

    var = {
        "receita": calc_var(kpis["receita_total"], kpis_ant["receita_total"]),
        "vendas": calc_var(kpis["vendas"], kpis_ant["vendas"]),
        "conversao": calc_var(kpis["taxa_conversao"], kpis_ant["taxa_conversao"]),
        "ticket": calc_var(kpis["ticket_medio"], kpis_ant["ticket_medio"])
    }

    # KPIs com variação
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Total", f"R$ {kpis['receita_total']:,.2f}".replace(".", ","), var["receita"])
    col2.metric("Vendas", f"{kpis['vendas']}", var["vendas"])
    col3.metric("Taxa de Conversão", f"{kpis['taxa_conversao']:.2%}", var["conversao"])
    col4.metric("Ticket Médio", f"R$ {kpis['ticket_medio']:,.2f}".replace(".", ","), var["ticket"])

    # Funil de conversao
    st.subheader("🔸 Funil de Conversão")
    funil = fetch_funil_conversao(property_id, start_date, end_date, customer_root)
    fig = go.Figure(go.Funnel(
        y=["Sessões", "Carrinhos", "Checkouts", "Compras"],
        x=[funil["sessao"], funil["carrinho"], funil["checkout"], funil["compra"]],
        textinfo="value+percent previous+percent total",
        marker={"color": "lightblue"}
    ))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # Receita por dia
    st.subheader("📈 Receita por Dia")
    receita_dia = fetch_receita_transacoes_por_dia(property_id, start_date, end_date, customer_root)

    if not receita_dia.empty:
        receita_dia = receita_dia.groupby("Data", as_index=False)["Receita"].sum()
        fig_receita = px.line(
            receita_dia,
            x="Data",
            y="Receita",
            title="Evolução de Receita por Dia",
            markers=True,
            template="plotly_dark",
        )
        fig_receita.update_layout(
            yaxis_title="Receita (R$)",
            xaxis_title="Data",
            font=dict(size=13),
            margin=dict(t=40, b=30)
        )
        fig_receita.update_traces(line=dict(width=2), marker=dict(size=6, color="#00BFFF"))
        st.plotly_chart(fig_receita, use_container_width=True)
    else:
        st.info("Não há dados de receita para o período selecionado.")
