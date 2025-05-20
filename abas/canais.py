import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from ga4_utils import fetch_conversoes_por_canal

def aba_canais_aquisicao(property_id, start_date, end_date, customer_root):
    st.subheader("📣 Canais de Aquisição")

    st.markdown("""
### Como interpretar:

- **Canais de aquisição** mostram por onde os visitantes chegaram ao site (ex: direto, redes sociais, Google, etc).
- Acompanhe os resultados por canal em termos de **sessões, conversões, receita e taxa de conversão**.
- Compare o desempenho com o período anterior e avalie onde investir melhor.
""")

    # Período atual
    df_canais = fetch_conversoes_por_canal(property_id, start_date, end_date, customer_root)

    # Período anterior
    inicio_dt = datetime.strptime(start_date, "%Y-%m-%d")
    fim_dt = datetime.strptime(end_date, "%Y-%m-%d")
    dias = (fim_dt - inicio_dt).days + 1
    inicio_ant = (inicio_dt - timedelta(days=dias)).strftime("%Y-%m-%d")
    fim_ant = (inicio_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    df_ant = fetch_conversoes_por_canal(property_id, inicio_ant, fim_ant, customer_root)

    # Cálculo de variação por canal
    if not df_canais.empty and not df_ant.empty:
        df_merged = df_canais.merge(df_ant, on="Canal", suffixes=("", "_ant"))
        for col in ["Sessões", "Conversões", "Receita (R$)", "Taxa de Conversão (%)"]:
            df_merged[f"Variação {col}"] = ((df_merged[col] - df_merged[f"{col}_ant"]) / df_merged[f"{col}_ant"]) * 100
            df_merged[f"Variação {col}"] = df_merged[f"Variação {col}"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "n/d")
        df_exibir = df_merged[["Canal", "Sessões", "Variação Sessões", "Conversões", "Variação Conversões",
                               "Receita (R$)", "Variação Receita (R$)", "Taxa de Conversão (%)", "Variação Taxa de Conversão (%)"]]
        st.dataframe(df_exibir, use_container_width=True)
    else:
        st.dataframe(df_canais.style.format({
            "Receita (R$)": "R$ {:.2f}",
            "Taxa de Conversão (%)": "{:.2f}%"
        }), use_container_width=True)

    # Gráficos
    fig1 = px.bar(df_canais.sort_values("Receita (R$)", ascending=False), x="Receita (R$)", y="Canal",
                  orientation="h", color="Canal", title="💰 Receita por Canal de Aquisição",
                  template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(df_canais.sort_values("Taxa de Conversão (%)", ascending=False), x="Taxa de Conversão (%)", y="Canal",
                  orientation="h", color="Canal", title="📈 Taxa de Conversão por Canal",
                  template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 📊 Comparativo: Pago vs Orgânico")
    df_canais["Grupo"] = df_canais["Canal"].apply(lambda x: "Pago" if any(p in x.lower() for p in ["paid", "ads", "cpc"]) else "Orgânico")
    grupo = df_canais.groupby("Grupo")[["Receita (R$)", "Conversões"]].sum().reset_index()
    st.dataframe(grupo)

    fig3 = px.pie(grupo, names="Grupo", values="Receita (R$)", title="Distribuição de Receita: Pago vs Orgânico", hole=0.4,
                  color_discrete_sequence=px.colors.sequential.Blues, template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
