# Dashboard GA4 + Diagnóstico com IA

Este projeto é um dashboard analítico com Streamlit que se conecta ao GA4 e gera insights automáticos com IA (via Groq).

## Funcionalidades
- KPIs de Receita, Vendas, Conversão e Ticket Médio
- Funil de Conversão e Abandono (Carrinho/Checkout)
- Produtos e Categorias mais Vendidos/Abandonados
- Canais de Aquisição com Comparativo
- Regiões e Engajamento
- Páginas mais acessadas
- Diagnóstico Estratégico via IA (modelo LLaMA3)
- Exportação de diagnóstico em `.docx`

## Como Rodar
1. Instale as dependências:
```
pip install -r requirements.txt
```
2. Coloque sua chave de API Groq no `.env`:
```
GROQ_API_KEY=sua_chave_aqui
```
3. Configure as credenciais GA4 no caminho:
```
credentials/service_account.json
```
4. Execute o app:
```
streamlit run app.py
```

---
© Projeto Santri Web - Web Analytics + CX
