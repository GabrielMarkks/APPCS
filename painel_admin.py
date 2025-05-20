
import sqlite3
import bcrypt
import streamlit as st
from config import nomes_amigaveis

def conectar():
    return sqlite3.connect("usuarios.db")

def listar_usuarios():
    conn = conectar()
    usuarios = conn.execute("SELECT id, nome, cliente, tipo FROM usuarios").fetchall()
    conn.close()
    return usuarios

def adicionar_usuario(nome, senha, cliente, tipo):
    conn = conectar()
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    try:
        conn.execute("INSERT INTO usuarios (nome, senha_hash, cliente, tipo) VALUES (?, ?, ?, ?)",
                     (nome, senha_hash, cliente, tipo))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Nome de usuário já existe.")
    finally:
        conn.close()

def excluir_usuario(usuario_id):
    conn = conectar()
    conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    st.success("Usuário excluído com sucesso.")

def painel_administrativo():
    st.header("⚙️ Painel Administrativo de Usuários")

    st.subheader("👥 Lista de Usuários")
    usuarios = listar_usuarios()
    for u in usuarios:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
        col1.write(f"👤 {u[1]}")
        col2.write(f"Cliente: `{u[2] or 'TODOS'}`")
        col3.write(f"Tipo: **{u[3]}**")
        if col4.button("🗑️ Excluir", key=f"del_{u[0]}"):
            excluir_usuario(u[0])
            st.rerun()

    st.markdown("---")
    st.subheader("➕ Adicionar Novo Usuário")
    with st.form("form_novo_usuario"):
        nome = st.text_input("Nome de usuário")
        senha = st.text_input("Senha", type="password")
        cliente = st.selectbox("Cliente", options=list(nomes_amigaveis.keys()))
        tipo = st.selectbox("Tipo de usuário", ["comum", "admin"])
        submitted = st.form_submit_button("Adicionar")
        if submitted:
            if not nome or not senha:
                st.warning("Preencha todos os campos obrigatórios.")
            else:
                adicionar_usuario(nome, senha, cliente if cliente else None, tipo)
                st.success(f"Usuário '{nome}' adicionado com sucesso!")
                st.rerun()
