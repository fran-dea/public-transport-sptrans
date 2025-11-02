import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import sys
import os

# sys.path.append(os.path.abspath("../.."))
# =========================
# Carregar os DataFrames
# =========================
passageiros_historico_pivot = pd.read_parquet("dados/passageiros_historico_pivot.parquet").reset_index()
# passageiros_historico_frequencia_ideal = pd.read_parquet("dados/passageiros_historico_frequencia_ideal.parquet")
rotas_historico_categorizado = pd.read_parquet("dados/rotas_historico_categorizado.parquet").drop_duplicates(subset='route_id')
routes_dist_km_historico = pd.read_parquet("dados/routes_dist_km_historico.parquet")
routes_dist_km_percorridos_historico = pd.read_parquet("dados/routes_dist_km_percorridos_historico.parquet")
frequencias_historico = pd.read_parquet(r"dados\frequencies_historico_categorizado.parquet")
frequencia_ideal = pd.read_parquet(r"dados\passageiros_historico_frequencia_ideal.parquet")[['data', 'route_id',
        'dia_da_semana', 'mes', 'ano',
       'horas_operacao', 'veiculos_padron_necessarios',
       'veiculos_articulados_necessarios', 'frequencia_ideal_padron',
       'frequencia_ideal_articulados']]

max_trip=pd.read_parquet(r"dados\trips_more_recent.parquet")[['route_id','direction_id','stop_id','stop_sequence','stop_name','stop_desc']]


rotas_historico_categorizado['horas_operacao']=rotas_historico_categorizado['horas_operacao'].apply(lambda x:round(x,2))

# Rota padrão
DEFAULT_ROUTE = "477P10"

# Lista de rotas disponíveis
rotas_disponiveis = sorted(rotas_historico_categorizado["route_id"].unique())

# =========================
# Inicializando Dash
# =========================
app = dash.Dash(__name__)
app.title = "Dashboard Transporte Público SP"

app.layout = html.Div(
    style={
        'font-family': 'Arial, sans-serif',
        'backgroundColor': '#000000',
        'padding': '20px'
    },
    children=[
        # Cabeçalho
        html.H1("Dashboard GTFS - São Paulo",
                style={'textAlign': 'center', 'color': '#ffffff'}),
        html.Hr(style={'border': '1px solid #ffffff'}),

        # Filtro de rota
        html.Div([
            html.Label("Selecione uma Rota:",
                       style={'fontWeight': 'bold', 'color': '#ffffff'}),
            dcc.Dropdown(
                id="dropdown-route",
                options=[{"label": r, "value": r} for r in rotas_disponiveis],
                value=DEFAULT_ROUTE,
                style={'width': '300px'}
            )
        ], style={'marginBottom': '20px'}),

        # Bloco de tabelas (em cima, full width)
        html.Div(
            id="tabelas-rotas",
            style={
                "width": "100%",
                "backgroundColor": "#000000",
                "padding": "10px",
                'border-radius': '10px',
                'box-shadow': '0 2px 5px rgba(0,0,0,0.1)',
                'marginBottom': '20px'
            }
        ),

        # Linha com 2 colunas: graficos-html (esquerda) e graficos-rota (direita)
        html.Div(
            style={'display': 'flex', 'gap': '10px', 'marginTop': '10px'},
            children=[
                # Coluna esquerda
                html.Div(
                    id="graficos-html",
                    style={
                        "width": "50%",
                        "backgroundColor": "#000000",
                        "padding": "5px",
                        'border-radius': '5px',
                        'box-shadow': '0 2px 5px rgba(0,0,0,0.1)'
                    }
                ),

                # Coluna direita
                html.Div(
                    id="graficos-rota",
                    style={
                        "width": "50%",
                        "backgroundColor": "#000000",
                        "padding": "5px",
                        'border-radius': '5px',
                        'box-shadow': '0 2px 5px rgba(0,0,0,0.1)'
                    }
                )
            ]
        )
    ]
)


# =========================
# Callbacks
# =========================

@app.callback(
    Output("tabelas-rotas", "children"),
    Output("graficos-html", "children"),
    Output("graficos-rota", "children"),
    Input("dropdown-route", "value")
)
def atualizar_dashboard(route_id):
    # ======================
    # Gráficos HTML da rota
    # ======================
    # path_atual = f"dados/plots_rotas_mais_recente/rota_{route_id}_com_gdf.html"

    # ======================
    # Outras tabelas
    # ======================
    # df_freq = passageiros_historico_frequencia_ideal.query("route_id == @route_id")
    df_cat = rotas_historico_categorizado.query("route_id == @route_id")
    df_dist = routes_dist_km_historico.query("route_id == @route_id")
    df_dist_perc = routes_dist_km_percorridos_historico.query("route_id == @route_id")
    df_freq_his=frequencias_historico[frequencias_historico["trip_id"].str.replace("-","").str.contains(route_id, na=False)]
    df_freq_ideal=frequencia_ideal.query("route_id == @route_id")
    df_max_trip=max_trip.query("route_id == @route_id").sort_values(["direction_id",'stop_sequence']).drop(columns="route_id")

    try:
        cor="#"+df_cat['route_color'].to_list()[0]
        text_cor="#"+df_cat['route_text_color'].to_list()[0]
    except: cor= "#FFFFFF";text_cor="#000000"


    def render_table(df, titulo):
    # Converter listas para string (p.ex. "[201608, 201609]" → "201608, 201609")
        df_fmt = df.copy()
        for col in df_fmt.columns:

            return html.Div([
                html.H3(titulo, style={'textAlign': 'center', 'color':cor}),
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df_fmt.columns],
                    data=df_fmt.to_dict('records'),
                    style_table={
                        'overflowX': 'auto',   # rolagem horizontal
                        'margin-bottom': '20px',
                        'maxWidth': '100%'     # força a tabela a não ultrapassar a largura da tela
                    },
                    style_cell={
                        'textAlign': 'center',
                        'padding': '5px',
                        'whiteSpace': 'normal',   # permite quebra de linha
                        'height': 'auto',         # ajusta altura das linhas automaticamente
                        'maxWidth': '200px',      # ajusta largura máxima da célula
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis' # corta texto que ainda ultrapassar
                    },
                    style_header={
                        'backgroundColor': cor,
                        'color': text_cor,
                        'fontWeight': 'bold',
                        'whiteSpace': 'normal'
                    },
                    style_data={
                        'backgroundColor': 'white',
                        'color': 'black'
                    },
                )
            ], style={'marginBottom': '30px'})

    path_hist = f"dados/plots_rotas_historico/rota_{route_id}_historico.html"
    path_mais_recente=f"dados/plots_rotas_mais_recente/rota_{route_id}_com_gdf.html"

    try:
        graficos_html = [
        # html.H3("Gráfico da Rota Atual", style={'textAlign': 'center', 'color': '#061844'}),
        # html.Iframe(
        #     srcDoc=open(path_atual, "r", encoding="UTF-8").read() if os.path.exists(path_atual) else "<p>Arquivo não encontrado</p>",
        #     style={"width": "100%", "height": "400px", "border": "1px solid #ccc", "border-radius": "5px"}
        # ),
        
        # html.H3("Trajeto mais recente da rota", style={'textAlign': 'center', 'color': cor, 'marginTop': '20px'}),
        html.Iframe(
            srcDoc=open(path_mais_recente, "r", encoding="UTF-8").read() if os.path.exists(path_mais_recente) else "<p>Arquivo não encontrado</p>",
            style={"width": "800px", "height": "420px", "border": "1px solid #ccc", "border-radius": "5px"}
            ),
        html.H3("Histórico da Rota", style={'textAlign': 'center', 'color': cor, 'marginTop': '10px'}),
        html.Iframe(
            srcDoc=open(path_hist, "r", encoding="UTF-8").read() if os.path.exists(path_hist) else "<p>Arquivo não encontrado</p>",
            style={"width": "800px", "height": "420px", "border": "1px solid #ccc", "border-radius": "5px"}
        )
    ]
    except: graficos_html = []

    # ======================
    # Passageiros (formato wide)
    # ======================
    if route_id not in passageiros_historico_pivot.columns:
        return graficos_html, html.P("Rota não encontrada na tabela de passageiros."), []

    df_passageiros = passageiros_historico_pivot[["data", route_id]].rename(columns={route_id: "passageiros"})

    df_passageiros["ano"] = df_passageiros["data"].dt.year
    df_passageiros["mes"] = df_passageiros["data"].dt.to_period("M").astype(str)
    # Agrupar passageiros por ano
    df_ano = df_passageiros.groupby("ano", as_index=False)["passageiros"].sum()

    # Agrupar passageiros por mês (pode precisar de ano também para diferenciar anos)
    df_mes = df_passageiros.groupby(["ano","mes"], as_index=False)["passageiros"].sum()

    # Agrupar passageiros por dia
    df_dia = df_passageiros.groupby("data", as_index=False)["passageiros"].sum()

    fig_passageiros = px.line(
        df_mes,
        x="mes",
        y="passageiros",
        title=f"Quantidade de Passageiros - {route_id}",
    )

    fig_passageiros.update_layout(
    updatemenus=[
        dict(
            buttons=list([
                
                
                dict(label="Por Mês",
                     method="update",
                     args=[{"x": [df_mes["mes"]],
                            "y": [df_mes["passageiros"]]}]),
                dict(label="Por Dia",
                     method="update",
                     args=[{"x": [df_dia["data"]],
                            "y": [df_dia["passageiros"]]}]),
                
                dict(label="Por Ano",
                     method="update",
                     args=[{"x": [df_ano["ano"]],
                            "y": [df_ano["passageiros"]]}])
            ]),
            direction="down",
            showactive=True,
                )
            ],
        font=dict(family="Arial, sans-serif", size=12, color="white"),
        plot_bgcolor="black",
        paper_bgcolor="black",
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="x unified",
        xaxis=dict(showgrid=False, zeroline=False, color='white'),
        yaxis=dict(showgrid=False, zeroline=False, color='white'),
        
        )
    # Estilo das linhas
    fig_passageiros.update_traces(
        line=dict(color=cor, width=2) )


    # graficos_html.append(
    # dcc.Graph(figure=fig_passageiros, style={"height": "400px"})
    # )

    fig_distancia = go.Figure()

    # Trace da distância máxima
    fig_distancia.add_trace(
        go.Scatter(
            x=df_dist["data_referencia"],
            y=df_dist["dist_km"],
            mode="lines",
            name="Distância da rota",
            line=dict(color="white", width=2)  
        )
    )

    # Trace da distância percorrida
    fig_distancia.add_trace(
        go.Scatter(
            x=df_dist_perc["data_referencia"],
            y=df_dist_perc["distancia_km_percorrido"],
            mode="lines",
            name="Distância percorrida pela rota",
            line=dict(color=cor, width=2)  
        )
    )

    # Layout unificado
    fig_distancia.update_layout(
        title=f"Distâncias - {route_id}",
        font=dict(family="Arial, sans-serif", size=12, color="white"),
        plot_bgcolor="black",
        paper_bgcolor="black",
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="x unified",
        xaxis=dict(showgrid=False, zeroline=False, color="white"),
        yaxis=dict(showgrid=False, zeroline=False, color="white"),
    )

    # heatmap frequencia ideal
    df_freq_his=df_freq_his.melt(
    id_vars=["data_referencia", "trip_id"],
    var_name="hora",
    value_name="frequencia"
)

    # --- 2) pivotar agregando por mês/hora (escolha aggfunc: 'sum' ou 'mean') ---
    pivot = df_freq_his.pivot_table(
        index='data_referencia',      # cada linha = um mês
        columns='hora',       # cada coluna = um horário (ex: "00h00 - 00h59")
        values='frequencia',  # valor a pintar
        aggfunc='sum',        # pode trocar para 'mean' ou 'max' se preferir
        fill_value=0
    )

    # --- 3) ordenar colunas por hora (robusto para rótulos como "00h00 - 00h59") ---
    def hour_key(label):
        s = str(label)
        m = re.search(r'(\d{1,2})', s)  # pega a primeira hora encontrada
        return int(m.group(1)) if m else 999

    pivot = pivot.reindex(sorted(pivot.columns, key=hour_key), axis=1)
    pivot = pivot.sort_index()  # ordena meses cronologicamente

    # opcional: reduzir para últimos N meses (ex: 24)
    # pivot = pivot.tail(24)

    # --- 4) criar heatmap com hover mostrando a frequência ---
    fig_heatmap = px.imshow(
        pivot,
        labels=dict(x='Hora do dia', y='Mês-Ano', color='Frequência'),
        aspect='auto',
        # title=f'Frequência programada da rota'
    )

    fig_heatmap.update_traces(
        hovertemplate="<b>Mês:</b> %{y}<br><b>Hora:</b> %{x}<br><b>Frequência:</b> %{z}<extra></extra>"
    )

    fig_heatmap.update_layout(
        xaxis=dict(
        title="Hora do dia",
        tickangle=-45,   # 🔹 deixa os rótulos inclinados (melhor leitura)
        tickmode="array"
        ),
        font=dict(family="Arial, sans-serif", size=12, color="white"),
        plot_bgcolor="black",
        paper_bgcolor="black",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    # --- 5) adicionar ao seu graficos_html (ex: ao final da lista) ---
    graficos_html.extend([
        html.H3("Frequência programada da rota", style={'textAlign': 'center', 'color': cor, 'marginTop': '20px'}),
        dcc.Graph(figure=fig_heatmap, style={"width": "90%", "height": "600px"})
    ])

    
    

    df_freq_ideal["ano"] = df_freq_ideal["data"].dt.year
    df_freq_ideal["mes"] = df_freq_ideal["data"].dt.to_period("M").astype(str)

    df_freq_ideal=df_freq_ideal[df_freq_ideal.frequencia_ideal_padron<1000]

    df_ano = df_freq_ideal.groupby(["ano"], as_index=False)["frequencia_ideal_padron"].median()
    df_mes = df_freq_ideal.groupby(["ano","mes"], as_index=False)["frequencia_ideal_padron"].median()

    # Agrupar passageiros por dia
    df_dia = df_freq_ideal


    fig_freq_ideal = px.line(
        df_mes,
        x="mes",
        y="frequencia_ideal_padron",
        title="Frequência Ideal minutos/ônibus calculada com os dados de passageiros que utilizaram a linha ao longo do tempo"
    )

    fig_freq_ideal.update_layout(
    updatemenus=[
        dict(
            buttons=list([
                
                
                dict(label="Por Mês",
                     method="update",
                     args=[{"x": [df_mes["mes"]],
                            "y": [df_mes["frequencia_ideal_padron"]]}]),
                dict(label="Por Dia",
                     method="update",
                     args=[{"x": [df_dia["data"]],
                            "y": [df_dia["frequencia_ideal_padron"]]}]),
                
                dict(label="Por Ano",
                     method="update",
                     args=[{"x": [df_ano["ano"]],
                            "y": [df_ano["frequencia_ideal_padron"]]}])
            ]),
            direction="down",
            showactive=True,
                )
            ],
        font=dict(family="Arial, sans-serif", size=12, color="white"),
        plot_bgcolor="black",
        paper_bgcolor="black",
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="x unified",
        xaxis=dict(showgrid=False, zeroline=False, color='white'),
        yaxis=dict(showgrid=False, zeroline=False, color='white'),
        
        )
    # Estilo das linhas
    fig_freq_ideal.update_traces(
        line=dict(color=cor, width=2) )
    
    # graficos_html.extend([
    #     html.H3("Frequência Ideal minutos/ônibus calculada com os dados de passageiros que utilizaram a linha ao longo do tempo", style={'textAlign': 'center', 'color': cor, 'marginTop': '20px'}),
    #     dcc.Graph(figure=fig_freq_ideal, style={"width": "90%", "height": "300px"})
    # ])

    tabelas=render_table(df_cat.drop(columns=['estacoes_proximas_existentes','estacoes_proximas','beneficiado_por_nova_estacao','tipo_de_rota_futuro','route_color','route_text_color','estacao_nova_no_bairro','populacoes']), "Dados da rota"),

    graficos_rota = [
        dcc.Graph(figure=fig_passageiros, style={"height": "300px"}),
        dcc.Graph(figure=fig_freq_ideal, style={"height": "300px"}),
        dcc.Graph(figure=fig_distancia, style={"height": "300px"}),
    ]

    graficos_html.append(render_table(df_max_trip, "Paradas da rota"))

    return tabelas, graficos_html, graficos_rota


# =========================
# Run
# =========================
if __name__ == '__main__':
    app.run(debug=True)
