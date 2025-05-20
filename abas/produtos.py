import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from ga4_utils import fetch_produtos_mais_vendidos, fetch_produtos_abandonados, fetch_categorias_mais_vendidas

def aba_produtos_categorias(property_id, start_date, end_date, customer_root):
    st.subheader("📊 Visão Detalhada por Produto e Categoria")

    # Período atual
    vendidos = fetch_produtos_mais_vendidos(property_id, start_date, end_date, customer_root)
    abandonados = fetch_produtos_abandonados(property_id, start_date, end_date, customer_root)
    vendidos = vendidos.rename(columns={"Produto": "Nome do item"})
    abandonados = abandonados.rename(columns={"Produto": "Nome do item"})
    df = pd.merge(abandonados, vendidos, on="Nome do item", how="outer").fillna(0)

    df["Adições ao Carrinho"] = df["Adições ao Carrinho"].astype(int)
    df["Itens comprados"] = df["Quantidade Vendida"].astype(int)
    df["Receita do item"] = df["Receita (R$)"].astype(float)

    # Período anterior
    inicio_dt = datetime.strptime(start_date, "%Y-%m-%d")
    fim_dt = datetime.strptime(end_date, "%Y-%m-%d")
    dias = (fim_dt - inicio_dt).days + 1
    inicio_ant = (inicio_dt - timedelta(days=dias)).strftime("%Y-%m-%d")
    fim_ant = (inicio_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    vendidos_ant = fetch_produtos_mais_vendidos(property_id, inicio_ant, fim_ant, customer_root)
    vendidos_ant = vendidos_ant.rename(columns={"Produto": "Nome do item"})

    # Variação de receita por produto
    if not vendidos.empty and not vendidos_ant.empty:
        df_var = pd.merge(
            vendidos[["Nome do item", "Receita (R$)"]],
            vendidos_ant[["Nome do item", "Receita (R$)"]],
            on="Nome do item", how="left"
        )
        df_var = df_var.rename(columns={"Receita (R$)_x": "Receita (R$)", "Receita (R$)_y": "Receita (R$)_ant"})
        df_var["Receita (R$)_ant"] = df_var["Receita (R$)_ant"].fillna(0)
        df_var["Variação Receita"] = df_var.apply(
            lambda row: ((row["Receita (R$)"] - row["Receita (R$)_ant"]) / row["Receita (R$)_ant"] * 100)
            if row["Receita (R$)_ant"] != 0 else 0,
            axis=1
        )
        df = pd.merge(df, df_var[["Nome do item", "Variação Receita"]], on="Nome do item", how="left")
    else:
        df["Variação Receita"] = 0

    # Totais
    total_adicoes = df["Adições ao Carrinho"].sum()
    total_compras = df["Itens comprados"].sum()
    total_receita = df["Receita do item"].sum()
    arppu = total_receita / total_compras if total_compras > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Adições ao Carrinho", f"{total_adicoes:,}")
    col2.metric("Compras", f"{total_compras:,}")
    col3.metric("Receita de Compra", f"R$ {total_receita:,.2f}".replace(".", ","))
    col4.metric("ARPPU", f"R$ {arppu:,.2f}".replace(".", ","))

    st.markdown("#### 🏆 Produtos Mais Vendidos")
    colunas_exibir = ["Nome do item", "Adições ao Carrinho", "Itens comprados", "Receita do item", "Variação Receita"]
    df_formatada = df[colunas_exibir].sort_values("Receita do item", ascending=False).copy()
    df_formatada["Receita do item"] = df_formatada["Receita do item"].map(lambda x: f"R$ {x:,.2f}".replace(".", ","))
    df_formatada["Variação Receita"] = df_formatada["Variação Receita"].map(lambda x: f"{x:.2f}%")
    st.dataframe(df_formatada.head(10), use_container_width=True)

    fig = px.bar(
        df.sort_values("Receita do item", ascending=False).head(10),
        x="Receita do item",
        y="Nome do item",
        orientation="h",
        title="Top Produtos por Receita",
        labels={"Receita do item": "Receita (R$)"},
        color="Receita do item",
        color_continuous_scale="Agsunset",
        template="plotly_dark",
        height=400
    )
    fig.update_traces(marker_line_width=1.2, marker_line_color="white", texttemplate='%{x:.2f}', textposition='auto')
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        font=dict(size=13),
        margin=dict(t=40, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 📦 Categorias Mais Vendidas")
    categorias = fetch_categorias_mais_vendidas(property_id, start_date, end_date, customer_root)
    st.dataframe(categorias, use_container_width=True)

    fig_cat = px.bar(
        categorias.sort_values("Receita (R$)", ascending=False).head(10),
        x="Receita (R$)",
        y="Categoria",
        orientation="h",
        title="Top Categorias por Receita",
        text_auto=True,
        template="plotly_dark",
        color="Receita (R$)",
        color_continuous_scale="Blues",
        height=400
    )
    st.plotly_chart(fig_cat, use_container_width=True)
