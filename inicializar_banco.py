
import sqlite3
import bcrypt

# Conexão com o banco (cria se não existir)
conn = sqlite3.connect("usuarios.db")
cursor = conn.cursor()

# Criação da tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    cliente TEXT,
    tipo TEXT CHECK(tipo IN ('admin', 'comum')) NOT NULL DEFAULT 'comum'
);
""")

# Inserção do admin padrão (gabriel/admin)
admin_nome = "gabriel"
admin_senha = "admin"
admin_tipo = "admin"

# Verifica se já existe
cursor.execute("SELECT * FROM usuarios WHERE nome = ?", (admin_nome,))
if not cursor.fetchone():
    senha_hash = bcrypt.hashpw(admin_senha.encode(), bcrypt.gensalt()).decode()
    cursor.execute("INSERT INTO usuarios (nome, senha_hash, cliente, tipo) VALUES (?, ?, ?, ?)", 
                   (admin_nome, senha_hash, None, admin_tipo))
    conn.commit()

conn.close()
