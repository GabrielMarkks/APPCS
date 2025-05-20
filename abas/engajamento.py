import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from ga4_utils import fetch_regioes_mais_acessadas, fetch_engajamento_site

def aba_engajamento_regioes(property_id, start_date, end_date, customer_root):
    st.subheader("📍 Cidades com Mais Acessos e Engajamento do Site")

    regioes = fetch_regioes_mais_acessadas(property_id, start_date, end_date, customer_root)
    engajamento = fetch_engajamento_site(property_id, start_date, end_date, customer_root)

    if not engajamento.empty:
        ultimos = engajamento.iloc[-1]
        if len(engajamento) >= 2:
            variacoes = ((engajamento.iloc[-1][1:] - engajamento.iloc[-2][1:]) / engajamento.iloc[-2][1:] * 100).round(2)
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Acessos Totais", f"{ultimos['Acessos Totais']:,}", f"{variacoes['Acessos Totais']:+.2f}%")
            col2.metric("Usuários Totais", f"{ultimos['Usuários Totais']:,}", f"{variacoes['Usuários Totais']:+.2f}%")
            col3.metric("Novos Usuários", f"{ultimos['Novos Usuários']:,}", f"{variacoes['Novos Usuários']:+.2f}%")
            col4.metric("Visualizações de Página", f"{ultimos['Visualizações de Página']:,}", f"{variacoes['Visualizações de Página']:+.2f}%")
            col5.metric("Taxa de Engajamento", f"{ultimos['Taxa de Engajamento (%)']:.2f}%", f"{variacoes['Taxa de Engajamento (%)']:+.2f}%")
        else:
            st.warning("Não há dados suficientes para calcular variação de engajamento no período selecionado.")

        

    st.dataframe(regioes.head(20), use_container_width=True)

    df_estado = regioes.groupby("Região")["Acessos"].sum().reset_index()
    df_estado["Estado_Nome"] = df_estado["Região"].str.replace("State of ", "").str.replace("Federal District", "Distrito Federal")

    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    fig_mapa = px.choropleth(
        df_estado,
        geojson=geojson_url,
        locations="Estado_Nome",
        featureidkey="properties.name",
        color="Acessos",
        hover_name="Estado_Nome",
        color_continuous_scale=px.colors.sequential.Oranges,
        template="plotly_dark",
        height=400
    )
    fig_mapa.update_geos(fitbounds="locations", visible=False)
    fig_mapa.update_layout(margin=dict(l=0, r=0, t=40, b=20))
    st.plotly_chart(fig_mapa, use_container_width=True)

    engajamento["Data"] = pd.to_datetime(engajamento["Data"])
    engajamento["Dia da Semana"] = engajamento["Data"].dt.day_name()
    df_dia = engajamento.groupby("Dia da Semana")["Acessos Totais"].mean().reindex([
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

    nomes_dias = {
        "Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira",
        "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
    df_dia.index = df_dia.index.map(nomes_dias)

    chart = alt.Chart(df_dia.reset_index()).mark_bar(color="#E15737").encode(
        x=alt.X("Dia da Semana", sort=list(df_dia.index)),
        y=alt.Y("Acessos Totais"),
        tooltip=["Dia da Semana", "Acessos Totais"]
    ).properties(
        title="📈 Pico de Acessos por Dia da Semana",
        width="container",
        height=300
    )
    st.altair_chart(chart, use_container_width=True)
