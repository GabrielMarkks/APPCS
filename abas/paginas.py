import streamlit as st
import plotly.express as px
from ga4_utils import fetch_paginas_mais_acessadas, fetch_funil_abandono, fetch_produtos_abandonados

def aba_paginas_carrinho(property_id, start_date, end_date, customer_root):
    st.subheader("📄 Páginas mais acessadas com Engajamento")
    paginas = fetch_paginas_mais_acessadas(property_id, start_date, end_date, customer_root)
    st.dataframe(paginas, use_container_width=True)

    st.subheader("🛒 Funil de Carrinho e Checkout")
    funil_abandono = fetch_funil_abandono(property_id, start_date, end_date, customer_root)

    col1, col2, col3 = st.columns(3)
    col1.metric("Adições ao Carrinho", f"{funil_abandono['add_to_cart']:,}")
    col2.metric("Inícios de Checkout", f"{funil_abandono['begin_checkout']:,}")
    col3.metric("Compras", f"{funil_abandono['purchase']:,}")

    col4, col5 = st.columns(2)
    col4.metric("Abandono no Carrinho", f"{funil_abandono['taxa_abandono_carrinho']:.2f}%")
    col5.metric("Abandono no Checkout", f"{funil_abandono['taxa_abandono_checkout']:.2f}%")

    fig_funil = px.bar(
        x=["Adicionou ao Carrinho", "Iniciou Checkout", "Comprou"],
        y=[funil_abandono["add_to_cart"], funil_abandono["begin_checkout"], funil_abandono["purchase"]],
        text_auto=True,
        color=[funil_abandono["add_to_cart"], funil_abandono["begin_checkout"], funil_abandono["purchase"]],
        color_continuous_scale="Oranges",
        template="plotly_dark",
        title="📉 Funil de Conversão",
        labels={"x": "Etapas", "y": "Quantidade de Eventos"},
        height=400
    )
    fig_funil.update_layout(
        font=dict(size=13),
        margin=dict(t=40, b=30),
        coloraxis_showscale=False
    )
    fig_funil.update_traces(marker_line_color="white", marker_line_width=1.2, textfont_size=14)
    st.plotly_chart(fig_funil, use_container_width=True)

    st.subheader("🔎 Produtos mais adicionados ao carrinho")
    df_abandono = fetch_produtos_abandonados(property_id, start_date, end_date, customer_root)
    if not df_abandono.empty:
        st.dataframe(df_abandono.head(10), use_container_width=True)
    else:
        st.info("Nenhum produto adicionado ao carrinho foi identificado no período.")
