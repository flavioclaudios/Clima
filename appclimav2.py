import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import pandas as pd
import requests
from datetime import datetime

# =====================================================================
# CONFIGURAÇÕES INICIAIS E CONSTANTES TEMA (DARK MODE MINIMALISTA)
# =====================================================================

# Inicializa o app Dash utilizando o grid system do Bootstrap (limpa o layout)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "Painel Meteorológico — São Paulo"

# Dicionários de estilo para manter o código do layout limpo e modular
BG_MAIN = '#121212'
BG_CARD = '#1e1e1e'
BG_CARD_HOVER = '#252525'
TEXT_MAIN = '#ffffff'
TEXT_MUTED = '#a0a0a0'

CONTAINER_STYLE = {
    'backgroundColor': BG_CARD,
    'padding': '20px',
    'borderRadius': '12px',
    'boxShadow': '0 4px 12px rgba(0,0,0,0.5)',
    'marginBottom': '20px',
    'border': '1px solid #2a2a2a'
}

# =====================================================================
# FUNÇÕES DE NEGÓCIO E INTEGRAÇÃO DE DADOS
# =====================================================================

def get_weather_icon(temp: float, rain_prob: float, hour_str: str) -> tuple:
    """Mapeia condições climáticas para ícones do DashIconify e cores adequadas."""
    try:
        hour = int(hour_str.split(':')[0])
    except ValueError:
        hour = 12

    # Define período noturno entre 18h e 05h
    is_night = hour < 6 or hour >= 18

    if rain_prob > 50:
        return "lucide:cloud-rain", "#3498db" # Azul (Chuva forte)
    elif rain_prob > 20:
        return "lucide:cloud-sun" if not is_night else "lucide:cloud-moon", "#f39c12" # Laranja (Chuva moderada/nublado)
    else:
        if is_night:
            return "lucide:moon", "#f1c40f" # Amarelo (Noite limpa)
        else:
            return ("lucide:sun", "#e74c3c") if temp > 25 else ("lucide:cloud-sun", "#2ecc71") # Vermelho (Calor) ou Verde (Agradável)

def fetch_weather_data() -> dict:
    """Consome a API do Open-Meteo e retorna dicionário com os dados processados."""
    lat, lon = -23.5505, -46.6333
    tz = "America%2FSao_Paulo"
    
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,apparent_temperature"
        f"&timezone={tz}"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Força exception para HTTP errors (4xx, 5xx)
        data = response.json()
        
        # 1. Dados Atuais
        current = {
            'temp': data['current']['temperature_2m'],
            'feels_like': data['current']['apparent_temperature'],
            'hum': data['current']['relative_humidity_2m'],
            'wind': data['current']['wind_speed_10m']
        }
        
        # 2. Dados Horários (Próximas 24 horas)
        hourly_data = data['hourly']
        hours = [datetime.fromisoformat(t).strftime('%H:%M') for t in hourly_data['time'][:24]]
        temps = hourly_data['temperature_2m'][:24]
        rains = hourly_data['precipitation_probability'][:24]
        
        df_hourly = pd.DataFrame({
            'Hora': hours,
            'Temperatura (°C)': temps,
            'Chance de Chuva (%)': rains
        })
        
        # 3. Dados Diários (Semana)
        daily_data = data['daily']
        days_list = []
        dias_semana_pt = {'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui', 'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'}
        
        for i in range(len(daily_data['time'])):
            dt = datetime.fromisoformat(daily_data['time'][i])
            dia_str = dt.strftime('%a')
            dia_formatado = dias_semana_pt.get(dia_str, dia_str)
            data_formatada = dt.strftime('%d/%m')
            
            t_max = daily_data['temperature_2m_max'][i]
            t_min = daily_data['temperature_2m_min'][i]
            p_rain = daily_data['precipitation_probability_max'][i]
            uv_max = daily_data.get('uv_index_max', [0]*len(daily_data['time']))[i]
            
            if p_rain > 50:
                ic, cor = "lucide:cloud-rain", "#3498db"
            elif p_rain > 20:
                ic, cor = "lucide:cloud-sun", "#f39c12"
            else:
                ic, cor = ("lucide:sun", "#e74c3c") if t_max > 24 else ("lucide:cloud-sun", "#2ecc71")
                
            days_list.append({
                'Dia': f"{dia_formatado} ({data_formatada})",
                'Max': t_max, 'Min': t_min, 'Chuva': p_rain, 'UV': uv_max,
                'Icone': ic, 'Cor': cor
            })
            
        return {'current': current, 'hourly': df_hourly, 'daily': days_list, 'error': False}
        
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados da API: {e}")
        return {'error': True}

# =====================================================================
# COMPONENTES DE UI (MODULARIZAÇÃO DO LAYOUT)
# =====================================================================

def create_kpi_card(title: str, value: str, icon: str, icon_color: str, value_color: str) -> dbc.Col:
    """Gera um card de indicador chave de performance (KPI) padronizado."""
    return dbc.Col(
        html.Div([
            html.Div([
                DashIconify(icon=icon, width=28, color=icon_color),
                html.H5(title, style={'color': TEXT_MUTED, 'margin': '0', 'fontSize': '14px', 'fontWeight': '500'})
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px', 'marginBottom': '12px'}),
            html.H2(value, style={'color': value_color, 'margin': '0', 'fontWeight': '700'})
        ], style=CONTAINER_STYLE | {'textAlign': 'center', 'height': '100%', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center'}),
        width=12, sm=6, md=3, style={'marginBottom': '15px'}
    )

def create_daily_card(day_data: dict) -> html.Div:
    """Gera o mini-card vertical para a previsão diária."""
    return html.Div([
        html.P(day_data['Dia'], style={'fontWeight': 'bold', 'color': TEXT_MAIN, 'margin': '0 0 10px 0', 'fontSize': '14px'}),
        DashIconify(icon=day_data['Icone'], width=38, color=day_data['Cor']),
        html.Div([
            html.Span(f"{day_data['Max']}°", style={'color': '#ff6b6b', 'fontWeight': 'bold', 'marginRight': '8px'}),
            html.Span(f"{day_data['Min']}°", style={'color': '#4dabf7'})
        ], style={'marginTop': '10px', 'fontSize': '16px'}),
        html.Div([
            html.P(f"🌧️ {day_data['Chuva']}%", style={'color': TEXT_MUTED, 'fontSize': '12px', 'margin': '8px 0 2px 0'}),
            html.P(f"☀️ UV: {day_data['UV']}", style={'color': '#f1c40f', 'fontSize': '12px', 'margin': '0'})
        ])
    ], style={
        'flex': '1', 'minWidth': '120px', 'backgroundColor': BG_CARD_HOVER, 
        'padding': '15px', 'borderRadius': '10px', 'textAlign': 'center',
        'border': '1px solid #333', 'boxShadow': '0 2px 5px rgba(0,0,0,0.2)'
    })

# =====================================================================
# LAYOUT PRINCIPAL
# =====================================================================

app.layout = dbc.Container([
    
    # Timer para auto-refresh (15 minutos = 15 * 60 * 1000 ms)
    dcc.Interval(id='auto-refresh', interval=900000, n_intervals=0),
    
    # Cabeçalho
    html.Div([
        html.Div([
            DashIconify(icon="lucide:radar", width=36, color="#4dabf7"),
            html.H1("Radar Meteorológico — São Paulo", style={'color': TEXT_MAIN, 'margin': '0', 'fontSize': '26px', 'fontWeight': 'bold'})
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '15px'}),
        html.Div(id='last-update-text', style={'color': TEXT_MUTED, 'fontSize': '13px', 'marginTop': '8px'})
    ], style=CONTAINER_STYLE | {'marginTop': '20px'}),
    
    # Container para mensagens de Erro
    html.Div(id='error-alert', style={'display': 'none'}),
    
    # Cards de KPIs Atuais (Grid system)
    dbc.Row(id='kpi-row', className="g-3"),
    
    # Previsão Semanal
    html.Div([
        html.H3([DashIconify(icon="lucide:calendar-days", width=22, style={'marginRight': '10px'}), "Previsão para os Próximos 7 Dias"], 
                style={'color': TEXT_MAIN, 'fontSize': '18px', 'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center'}),
        html.Div(id='weekly-container', style={'display': 'flex', 'gap': '15px', 'overflowX': 'auto', 'paddingBottom': '10px'})
    ], style=CONTAINER_STYLE),
    
    # Gráficos (Próximas 24h)
    dbc.Row([
        dbc.Col(
            html.Div(dcc.Graph(id='temp-graph', config={'displayModeBar': False}), style=CONTAINER_STYLE), 
            width=12, lg=6
        ),
        dbc.Col(
            html.Div(dcc.Graph(id='rain-graph', config={'displayModeBar': False}), style=CONTAINER_STYLE), 
            width=12, lg=6
        )
    ])
    
], fluid=True, style={'backgroundColor': BG_MAIN, 'minHeight': '100vh', 'fontFamily': 'Inter, Arial, sans-serif'})

# =====================================================================
# CALLBACKS (LÓGICA DE ATUALIZAÇÃO DINÂMICA)
# =====================================================================

@app.callback(
    [Output('kpi-row', 'children'),
     Output('weekly-container', 'children'),
     Output('temp-graph', 'figure'),
     Output('rain-graph', 'figure'),
     Output('last-update-text', 'children'),
     Output('error-alert', 'children'),
     Output('error-alert', 'style')],
    [Input('auto-refresh', 'n_intervals')]
)
def update_dashboard(n):
    # 1. Busca de Dados
    weather = fetch_weather_data()
    timestamp = f"Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} (Auto-refresh a cada 15 min)"
    
    # Tratamento de erro na API
    if weather.get('error'):
        error_msg = dbc.Alert("Erro de conexão com a API Meteorológica. Tentando novamente no próximo ciclo...", color="danger")
        empty_fig = px.line(template='plotly_dark').update_layout(plot_bgcolor=BG_CARD, paper_bgcolor=BG_CARD)
        return [], [], empty_fig, empty_fig, timestamp, error_msg, {'display': 'block'}

    data_curr = weather['current']
    df_hourly = weather['hourly']
    days_list = weather['daily']
    
    # 2. Renderização dos KPIs Atuais
    current_hour_str = datetime.now().strftime('%H:00')
    curr_icon, curr_color = get_weather_icon(data_curr['temp'], 10, current_hour_str)
    
    kpis = [
        create_kpi_card("Temperatura Atual", f"{data_curr['temp']}°C", curr_icon, curr_color, "#ff8787"),
        create_kpi_card("Sensação Térmica", f"{data_curr['feels_like']}°C", "lucide:thermometer-sun", "#f39c12", "#fcc419"),
        create_kpi_card("Umidade Relativa", f"{data_curr['hum']}%", "lucide:droplets", "#3498db", "#4dabf7"),
        create_kpi_card("Vento", f"{data_curr['wind']} km/h", "lucide:wind", "#2ecc71", "#69db7c")
    ]
    
    # 3. Renderização da Previsão Semanal
    weekly_cards = [create_daily_card(day) for day in days_list]
    
    # 4. Construção de Gráficos (Layout mais limpo e tooltips modernos)
    fig_temp = px.line(
        df_hourly, x='Hora', y='Temperatura (°C)', 
        title="Evolução Térmica (24h)", markers=True, template='plotly_dark'
    )
    fig_temp.update_traces(
        line=dict(color='#ff8787', width=3, shape='spline'), 
        marker=dict(size=8, color='#ff8787', line=dict(width=2, color=BG_CARD)),
        hovertemplate="<b>%{x}</b><br>Temperatura: %{y}°C<extra></extra>"
    )
    fig_temp.update_layout(
        plot_bgcolor=BG_CARD, paper_bgcolor=BG_CARD, margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color=TEXT_MAIN), title_font=dict(size=16, color=TEXT_MUTED),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#333333', zeroline=False)
    )
    
    fig_rain = px.bar(
        df_hourly, x='Hora', y='Chance de Chuva (%)', 
        title="Probabilidade de Precipitação (24h)", text_auto=True, template='plotly_dark'
    )
    fig_rain.update_traces(
        marker_color='#4dabf7', marker_line_width=0, opacity=0.8,
        textfont_size=10, textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Chuva: %{y}%<extra></extra>"
    )
    fig_rain.update_layout(
        plot_bgcolor=BG_CARD, paper_bgcolor=BG_CARD, margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color=TEXT_MAIN), title_font=dict(size=16, color=TEXT_MUTED),
        yaxis=dict(range=[0, 110], showgrid=True, gridcolor='#333333'),
        xaxis=dict(showgrid=False)
    )
    
    return kpis, weekly_cards, fig_temp, fig_rain, timestamp, "", {'display': 'none'}

# =====================================================================
# INICIALIZAÇÃO DO SERVIDOR
# =====================================================================

if __name__ == '__main__':
    print("🚀 Dashboard Meteorológico Inicializado com Sucesso.")
    print("🔗 Acesse no seu navegador: http://127.0.0.1:8050/")
    # Usando app.run() no lugar do descontinuado app.run_server()
    app.run(debug=True, host='127.0.0.1', port=8050)