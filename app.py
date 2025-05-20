
import os
import datetime
import sqlite3
import streamlit as st
import pandas as pd
import bcrypt
from dotenv import load_dotenv
from config import nomes_amigaveis
from painel_admin import painel_administrativo

# IMPORTAÇÕES DE UTILITÁRIOS
from diagnostico_utils import (
    coletar_dados_dashboard,
    gerar_prompt,
    chamar_ia,
    exportar_txt,
    exportar_docx
)
from ga4_utils import *
from abas.vendas import aba_vendas_receita
from abas.produtos import aba_produtos_categorias
from abas.canais import aba_canais_aquisicao
from abas.engajamento import aba_engajamento_regioes
from abas.paginas import aba_paginas_carrinho
from abas.diagnostico import aba_diagnostico_ia
from abas.resumo import aba_resumo_executivo

# === CONFIGURAÇÃO ===
load_dotenv()
st.set_page_config(page_title="Dashboard GA4 + IA", layout="wide")

# === CONTROLE DE SESSÃO ===
if "logado" not in st.session_state:
    st.session_state["logado"] = False

def validar_login(usuario, senha):
    conn = sqlite3.connect("usuarios.db")
    c = conn.cursor()
    c.execute("SELECT senha_hash, cliente, tipo FROM usuarios WHERE nome = ?", (usuario,))
    row = c.fetchone()
    conn.close()
    if row and bcrypt.checkpw(senha.encode(), row[0].encode()):
        return {
            "cliente": row[1],
            "tipo": row[2]
        }
    return None

def tela_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Acesso ao Dashboard GA4</h2>", unsafe_allow_html=True)
    with st.form("form_login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        if submit:
            dados = validar_login(usuario, senha)
            if dados:
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["cliente"] = dados["cliente"]
                st.session_state["tipo"] = dados["tipo"]
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")

if not st.session_state["logado"]:
    tela_login()
    st.stop()

st.title("📊 Visão Geral de Performance - GA4")

# === SIDEBAR ===
st.sidebar.header("📅 Período")
hoje = datetime.date.today()
atalhos = {
    "Hoje": (hoje, hoje),
    "Ontem": (hoje - datetime.timedelta(days=1), hoje - datetime.timedelta(days=1)),
    "Últimos 7 dias": (hoje - datetime.timedelta(days=6), hoje),
    "Últimos 30 dias": (hoje - datetime.timedelta(days=29), hoje),
    "Este mês": (hoje.replace(day=1), hoje),
    "Mês anterior": ((hoje.replace(day=1) - datetime.timedelta(days=1)).replace(day=1), hoje.replace(day=1) - datetime.timedelta(days=1))
}
opcao_intervalo = st.sidebar.selectbox("Selecione um intervalo:", list(atalhos.keys()) + ["Personalizado"], index=2)
if opcao_intervalo == "Personalizado":
    col1, col2 = st.sidebar.columns(2)
    data_inicio = col1.date_input("Início", hoje - datetime.timedelta(days=30))
    data_fim = col2.date_input("Fim", hoje)
else:
    data_inicio, data_fim = atalhos[opcao_intervalo]
st.sidebar.write(f"📅 Período: **{data_inicio.strftime('%d/%m/%Y')}** a **{data_fim.strftime('%d/%m/%Y')}**")

st.sidebar.header("🏪 Cliente")

if st.session_state.get("cliente"):  # Usuário comum
    cliente_selecionado = nomes_amigaveis[st.session_state["cliente"]]
    st.sidebar.write(f"Cliente: **{cliente_selecionado}**")
    CUSTOMER_ROOT = st.session_state["cliente"]
else:  # Admin
    cliente_selecionado = st.sidebar.selectbox("Selecionar cliente", ["Todos os clientes"] + list(nomes_amigaveis.values()))
    CUSTOMER_ROOT = None if cliente_selecionado == "Todos os clientes" else [k for k, v in nomes_amigaveis.items() if v == cliente_selecionado][0]


st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair"):
    for chave in ["logado", "usuario", "cliente", "tipo"]:
        if chave in st.session_state:
            del st.session_state[chave]
    st.rerun()


PROPERTY_ID = "378239992"
def filtros():
    return PROPERTY_ID, str(data_inicio), str(data_fim), CUSTOMER_ROOT

# === ABAS ===
aba_labels = [
    "📌 Resumo Executivo",
    "Vendas e Receita",
    "Produtos e Categorias",
    "Canais de Aquisição",
    "Engajamento e Regiões",
    "Páginas e Carrinho",
    "📋 Diagnóstico IA"
]

if st.session_state.get("cliente") is None:
    aba_labels.append("⚙️ Administração")

abas = st.tabs(aba_labels)

with abas[0]: aba_resumo_executivo(*filtros())
with abas[1]: aba_vendas_receita(*filtros())
with abas[2]: aba_produtos_categorias(*filtros())
with abas[3]: aba_canais_aquisicao(*filtros())
with abas[4]: aba_engajamento_regioes(*filtros())
with abas[5]: aba_paginas_carrinho(*filtros())
with abas[6]: aba_diagnostico_ia(*filtros())

if len(aba_labels) > 7:
    with abas[7]:
        painel_administrativo()
