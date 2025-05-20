import streamlit as st
from diagnostico_utils import coletar_dados_dashboard, gerar_prompt, chamar_ia, exportar_docx

def aba_diagnostico_ia(property_id, start_date, end_date, customer_root):
    st.subheader("📋 Diagnóstico IA - Inteligência Aplicada aos Dados")

    with st.spinner("Analisando dados e gerando diagnóstico com IA..."):
        dados = coletar_dados_dashboard(property_id, start_date, end_date, customer_root)

        # Adiciona resumo interpretável para refinar o prompt
        kpis = dados.get("kpis", {})
        funil = dados.get("funil", {})
        abandono = dados.get("abandono", {})
        dispositivo = dados.get("dispositivo_destaque", "n/d")
        cidade = dados.get("cidade_top", "n/d")
        produto_top = dados.get("ponto_forte", {})
        produto_nome = produto_top.get("Produto", "n/d") if produto_top else "n/d"
        receita = produto_top.get("Receita (R$)", 0.0)

        contexto_extra = f"""
---
📊 Contexto adicional:
- Dispositivo com mais sessões: {dispositivo}
- Cidade com mais acessos: {cidade}
- Produto de maior receita: {produto_nome} (R$ {receita:.2f})
- Abandono no carrinho: {max(abandono.get("taxa_abandono_carrinho", 0), 0):.2f}%
- Abandono no checkout: {max(abandono.get("taxa_abandono_checkout", 0), 0):.2f}%
- Funil de conversão: {funil.get("sessao", 0)} sessões > {funil.get("carrinho", 0)} carrinhos > {funil.get("checkout", 0)} checkouts > {funil.get("compra", 0)} compras
"""

        prompt = gerar_prompt(dados, customer_root or "Todos", start_date, end_date) + contexto_extra
        resposta = chamar_ia(prompt)

    st.markdown("""
### 🤖 Diagnóstico Estratégico com IA
Abaixo está uma análise gerada automaticamente com base nos dados do dashboard.
Ela é feita por um agente inteligente especializado em performance de e-commerce.

**Este diagnóstico considera:**
- KPIs gerais (receita, conversão, vendas, ticket médio)
- Funil de conversão e abandono (carrinho e checkout)
- Produtos mais vendidos e mais abandonados
- Canais de aquisição com destaque ou queda
- Regiões, dispositivos e páginas com engajamento relevante

**A IA entrega:**
- Pontos de atenção reais com base nos dados atuais
- Recomendações práticas por canal ou produto
- Perguntas estratégicas que ajudam a tomar decisões
""")

    st.text_area("Resposta da IA:", resposta, height=400)

    st.markdown("""
### 💡 Perguntas que você pode explorar com a IA:
- Quais produtos com bom engajamento ainda não convertem?
- Qual canal teve maior queda de receita?
- Como reduzir o abandono no checkout?
- Quais campanhas eu deveria pausar ou escalar?
- Vale a pena criar uma oferta para o produto mais visualizado?
""")

    docx_path = exportar_docx(resposta)
    with open(docx_path, "rb") as f:
        st.download_button("📥 Baixar Diagnóstico em .docx", f, file_name="diagnostico-estrategico.docx")

    with st.expander("💬 Gerar nova pergunta para a IA sobre esse período"):
        nova_pergunta = st.text_input("Digite sua pergunta:")
        if st.button("Perguntar para IA") and nova_pergunta:
            pergunta_prompt = prompt + f"\n\n🧠 Pergunta adicional do cliente:\n{nova_pergunta}"
            nova_resposta = chamar_ia(pergunta_prompt)
            st.text_area("Resposta da IA:", nova_resposta, height=300)
