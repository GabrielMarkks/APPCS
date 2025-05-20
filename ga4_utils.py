import os
import pandas as pd
import streamlit as st  # Adicionado para uso do cache
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric,
    FilterExpression, Filter, FilterExpressionList
)

def get_ga4_client():
    with open("/tmp/service_account.json", "w") as f:
        f.write(st.secrets["GOOGLE_SERVICE_ACCOUNT"])

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/service_account.json"

    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    return BetaAnalyticsDataClient()


def build_customer_filter(customer_root):
    if not customer_root:
        return None
    return FilterExpression(
        filter=Filter(
            field_name="customUser:customer_root",
            string_filter=Filter.StringFilter(value=customer_root)
        )
    )



# === FUNÇÕES ===
@st.cache_data(ttl=3600)
def fetch_ga4_kpis(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[],
        metrics=[
            Metric(name="totalRevenue"),
            Metric(name="conversions"),
            Metric(name="sessionConversionRate"),
            Metric(name="averagePurchaseRevenue")
        ],
        dimension_filter=filtro
    )
    response = client.run_report(request=request)
    row = response.rows[0].metric_values if response.rows else [0]*4
    return {
        "receita_total": float(row[0].value),
        "vendas": int(row[1].value),
        "taxa_conversao": float(row[2].value),
        "ticket_medio": float(row[3].value)
    }

@st.cache_data(ttl=3600)
def fetch_receita_transacoes_por_dia(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="conversions"),
            Metric(name="totalRevenue")
        ],
        limit=1000,
        dimension_filter=filtro
    )
    response = client.run_report(request=request)
    data = []
    for row in response.rows:
        data.append({
            "Data": row.dimension_values[0].value,
            "Conversões": int(row.metric_values[0].value),
            "Receita": float(row.metric_values[1].value)
        })
    df = pd.DataFrame(data)
    df["Data"] = pd.to_datetime(df["Data"])
    return df.sort_values("Data")

@st.cache_data(ttl=3600)
def fetch_origem_conversoes(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="sessionSourceMedium")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="conversions"),
            Metric(name="totalRevenue"),
            Metric(name="sessionConversionRate")
        ],
        limit=50,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)

    data = [
        [row.dimension_values[0].value] + [val.value for val in row.metric_values]
        for row in response.rows
    ]

    df = pd.DataFrame(data, columns=["Origem / Mídia", "Sessões", "Conversões", "Receita", "Taxa de Conversão"])
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    return df

@st.cache_data(ttl=3600)
def fetch_funil_conversao(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)
    eventos = ["session_start", "add_to_cart", "begin_checkout", "purchase"]

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        limit=100,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)
    data = {e: 0 for e in eventos}

    for row in response.rows:
        nome_evento = row.dimension_values[0].value
        if nome_evento in data:
            data[nome_evento] = int(row.metric_values[0].value)

    return {
        "sessao": data["session_start"],
        "carrinho": data["add_to_cart"],
        "checkout": data["begin_checkout"],
        "compra": data["purchase"]
    }


@st.cache_data(ttl=3600)
def fetch_produtos_mais_vendidos(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="itemName")],
        metrics=[
            Metric(name="itemRevenue"),
            Metric(name="itemsPurchased")
        ],
        limit=50,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)

    data = []
    for row in response.rows:
        nome = row.dimension_values[0].value
        receita = float(row.metric_values[0].value)
        quantidade = int(row.metric_values[1].value)
        ticket_medio = receita / quantidade if quantidade > 0 else 0
        data.append([nome, quantidade, receita, ticket_medio])

    df = pd.DataFrame(data, columns=["Produto", "Quantidade Vendida", "Receita (R$)", "Ticket Médio (R$)"])
    return df.sort_values("Receita (R$)", ascending=False)

@st.cache_data(ttl=3600)
def fetch_categorias_mais_vendidas(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="itemCategory")],
        metrics=[
            Metric(name="itemRevenue"),
            Metric(name="itemsPurchased")
        ],
        limit=50,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)

    data = []
    for row in response.rows:
        categoria = row.dimension_values[0].value or "Sem categoria"
        receita = float(row.metric_values[0].value)
        quantidade = int(row.metric_values[1].value)
        ticket_medio = receita / quantidade if quantidade > 0 else 0
        data.append([categoria, quantidade, receita, ticket_medio])

    df = pd.DataFrame(data, columns=["Categoria", "Quantidade Vendida", "Receita (R$)", "Ticket Médio (R$)"])
    return df.sort_values("Receita (R$)", ascending=False)

@st.cache_data(ttl=3600)
def fetch_tecnologia_usuarios(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    req_dispositivos = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name="sessions")],
        limit=10,
        dimension_filter=filtro
    )

    req_sistemas = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="operatingSystem")],
        metrics=[Metric(name="sessions")],
        limit=10,
        dimension_filter=filtro
    )

    res_disp = client.run_report(request=req_dispositivos)
    res_sist = client.run_report(request=req_sistemas)

    df_disp = pd.DataFrame([{
        "Categoria": row.dimension_values[0].value.title(),
        "Sessões": int(row.metric_values[0].value)
    } for row in res_disp.rows])

    df_sist = pd.DataFrame([{
        "Sistema": row.dimension_values[0].value,
        "Sessões": int(row.metric_values[0].value)
    } for row in res_sist.rows])

    return df_disp, df_sist

@st.cache_data(ttl=3600)
def fetch_regioes_mais_acessadas(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="region"), Dimension(name="city")],
        metrics=[Metric(name="sessions")],
        limit=500,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)

    data = []
    for row in response.rows:
        regiao = row.dimension_values[0].value or "Não definida"
        cidade = row.dimension_values[1].value or "Não definida"
        sessoes = int(row.metric_values[0].value)
        data.append([regiao, cidade, sessoes])

    df = pd.DataFrame(data, columns=["Região", "Cidade", "Acessos"])
    return df.sort_values("Acessos", ascending=False)

@st.cache_data(ttl=3600)
def fetch_engajamento_site(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="newUsers"),
            Metric(name="screenPageViews"),
            Metric(name="engagementRate")
        ],
        limit=1000,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)

    data = []
    for row in response.rows:
        data.append({
            "Data": row.dimension_values[0].value,
            "Acessos Totais": int(row.metric_values[0].value),
            "Usuários Totais": int(row.metric_values[1].value),
            "Novos Usuários": int(row.metric_values[2].value),
            "Visualizações de Página": int(row.metric_values[3].value),
            "Taxa de Engajamento (%)": float(row.metric_values[4].value) * 100
        })

    df = pd.DataFrame(data)
    df["Data"] = pd.to_datetime(df["Data"], format="%Y%m%d")
    return df


@st.cache_data(ttl=3600)
def fetch_paginas_mais_acessadas(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="pagePath")],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="sessions"),
            Metric(name="engagementRate")
        ],
        limit=25,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)

    data = []
    for row in response.rows:
        data.append({
            "Página": row.dimension_values[0].value,
            "Visualizações": int(row.metric_values[0].value),
            "Sessões": int(row.metric_values[1].value),
            "Taxa de Engajamento (%)": float(row.metric_values[2].value) * 100
        })

    return pd.DataFrame(data).sort_values("Visualizações", ascending=False)

@st.cache_data(ttl=3600)
def fetch_conversoes_por_canal(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro = build_customer_filter(customer_root)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="conversions"),
            Metric(name="totalRevenue")
        ],
        limit=25,
        dimension_filter=filtro
    )

    response = client.run_report(request=request)

    data = []
    for row in response.rows:
        canal = row.dimension_values[0].value
        sessoes = int(row.metric_values[0].value)
        conversoes = int(row.metric_values[1].value)
        receita = float(row.metric_values[2].value)
        taxa_conv = (conversoes / sessoes * 100) if sessoes > 0 else 0
        data.append([canal, sessoes, conversoes, receita, taxa_conv])

    return pd.DataFrame(data, columns=["Canal", "Sessões", "Conversões", "Receita (R$)", "Taxa de Conversão (%)"]).sort_values("Receita (R$)", ascending=False)

@st.cache_data(ttl=3600)
def fetch_funil_abandono(property_id, start_date, end_date, customer_root=None):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric,
        FilterExpression, Filter
    )
    import pandas as pd

    client = get_ga4_client()

    def fetch_event_count(event_name):
        filtro_evento = FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value=event_name)
            )
        )

        filtro_final = filtro_evento
        if customer_root:
            filtro_cliente = build_customer_filter(customer_root)
            filtro_final = FilterExpression(
                and_group=FilterExpressionList(expressions=[filtro_evento, filtro_cliente])
            )

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="eventCount")],
            dimension_filter=filtro_final
        )

        response = client.run_report(request=request)
        total = sum(int(row.metric_values[0].value) for row in response.rows) if response.rows else 0
        return total

    add = fetch_event_count("add_to_cart")
    checkout = fetch_event_count("begin_checkout")
    compra = fetch_event_count("purchase")

    taxa_abandono_carrinho = max(min(((add - checkout) / add) * 100, 100), 0) if add else 0
    taxa_abandono_checkout = ((checkout - compra) / checkout * 100) if checkout else 0

    return {
        "add_to_cart": add,
        "begin_checkout": checkout,
        "purchase": compra,
        "taxa_abandono_carrinho": taxa_abandono_carrinho,
        "taxa_abandono_checkout": taxa_abandono_checkout
    }

@st.cache_data(ttl=3600)
def fetch_produtos_abandonados(property_id, start_date, end_date, customer_root=None):
    client = get_ga4_client()
    filtro_evento = FilterExpression(
        filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(
                value="add_to_cart",
                match_type=Filter.StringFilter.MatchType.EXACT
            )
        )
    )

    if customer_root:
        filtro_custom = build_customer_filter(customer_root)
        filtro_final = FilterExpression(
            and_group=FilterExpressionList(
                expressions=[filtro_custom, filtro_evento]
            )
        )
    else:
        filtro_final = filtro_evento

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="itemName")],
        metrics=[Metric(name="itemsAddedToCart")],
        limit=100,
        dimension_filter=filtro_final
    )

    response = client.run_report(request=request)

    dados = []
    for row in response.rows:
        produto = row.dimension_values[0].value
        adicoes = int(row.metric_values[0].value)
        dados.append({"Produto": produto, "Adições ao Carrinho": adicoes})

    return pd.DataFrame(dados).sort_values(by="Adições ao Carrinho", ascending=False)


