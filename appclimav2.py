import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# =====================================================================
# CONFIGURAÇÕES INICIAIS DO STREAMLIT
# =====================================================================
st.set_page_config(
    page_title="Painel Meteorológico — São Paulo",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS customizada para manter o visual dark e cartões minimalistas
CSS_CUSTOM = """
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .kpi-card {
        background-color: #1e1e1e; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5); text-align: center;
        border: 1px solid #2a2a2a; margin-bottom: 15px;
    }
    .daily-card {
        background-color: #252525; padding: 15px 10px; border-radius: 10px;
        text-align: center; border: 1px solid #333; height: 100%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .metric-value { font-size: 28px; font-weight: bold; margin: 5px 0; }
    .metric-label { color: #a0a0a0; font-size: 14px; margin: 0; font-weight: 500; }
    .day-title { color: #ffffff; font-weight: bold; font-size: 15px; margin-bottom: 5px; }
</style>
"""
st.markdown(CSS_CUSTOM, unsafe_allow_html=True)

# =====================================================================
# FUNÇÕES DE NEGÓCIO E INTEGRAÇÃO DE DADOS
# =====================================================================

def get_weather_emoji(temp: float, rain_prob: float, hour_str: str) -> tuple:
    """Retorna Emojis nativos e cores hexadecimais baseado nas condições."""
    try:
        hour = int(hour_str.split(':')[0])
    except ValueError:
        hour = 12

    is_night = hour < 6 or hour >= 18

    if rain_prob > 50:
        return "🌧️", "#3498db"
    elif rain_prob > 20:
        return "⛅" if not is_night else "☁️", "#f39c12"
    else:
        if is_night:
            return "🌙", "#f1c40f"
        else:
            return ("☀️", "#e74c3c") if temp > 25 else ("🌤️", "#2ecc71")

@st.cache_data(ttl=900) # Cache automático de 15 minutos (900s)
def fetch_weather_data():
    """Consome a API do Open-Meteo e retorna dicionário padronizado."""
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
        response.raise_for_status()
        data = response.json()
        
        current = {
            'temp': data['current']['temperature_2m'],
            'feels_like': data['current']['apparent_temperature'],
            'hum': data['current']['relative_humidity_2m'],
            'wind': data['current']['wind_speed_10m']
        }
        
        hourly_data = data['hourly']
        hours = [datetime.fromisoformat(t).strftime('%H:%M') for t in hourly_data['time'][:24]]
        
        df_hourly = pd.DataFrame({
            'Hora': hours,
            'Temperatura (°C)': hourly_data['temperature_2m'][:24],
            'Chance de Chuva (%)': hourly_data['precipitation_probability'][:24]
        })
        
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
            
            ic, cor = get_weather_emoji(t_max, p_rain, "12:00")
                
            days_list.append({
                'Dia': f"{dia_formatado} ({data_formatada})",
                'Max': t_max, 'Min': t_min, 'Chuva': p_rain, 'UV': uv_max,
                'Emoji': ic, 'Cor': cor
            })
            
        return {'current': current, 'hourly': df_hourly, 'daily': days_list, 'error': False}
        
    except Exception as e:
        return {'error': True, 'msg': str(e)}

# =====================================================================
# LAYOUT PRINCIPAL
# =====================================================================

def main():
    col_hdr1, col_hdr2 = st.columns([0.8, 0.2])
    with col_hdr1:
        st.markdown("<h1 style='margin-bottom: 0px;'>📡 Radar Meteorológico — São Paulo</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #a0a0a0;'>Última sincronização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>", unsafe_allow_html=True)
    with col_hdr2:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("Buscando dados atmosféricos..."):
        weather = fetch_weather_data()

    if weather.get('error'):
        st.error(f"Erro de conexão com a API Meteorológica. Detalhes: {weather.get('msg')}")
        st.stop()

    data_curr = weather['current']
    df_hourly = weather['hourly']
    days_list = weather['daily']
    
    current_hour_str = datetime.now().strftime('%H:00')
    curr_emoji, _ = get_weather_emoji(data_curr['temp'], 10, current_hour_str)

    # 1. KPIs Atuais
    kpi_cols = st.columns(4)
    kpis = [
        {"label": "Temperatura Atual", "val": f"{data_curr['temp']}°C", "icon": curr_emoji, "color": "#ff8787"},
        {"label": "Sensação Térmica", "val": f"{data_curr['feels_like']}°C", "icon": "🌡️", "color": "#fcc419"},
        {"label": "Umidade Relativa", "val": f"{data_curr['hum']}%", "icon": "💧", "color": "#4dabf7"},
        {"label": "Vento", "val": f"{data_curr['wind']} km/h", "icon": "💨", "color": "#69db7c"}
    ]
    
    for col, kpi in zip(kpi_cols, kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <p class="metric-label">{kpi['icon']} {kpi['label']}</p>
                <p class="metric-value" style="color: {kpi['color']};">{kpi['val']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 2. Previsão Semanal
    st.markdown("### 📅 Previsão para os Próximos 7 Dias")
    day_cols = st.columns(7)
    
    for col, day in zip(day_cols, days_list):
        with col:
            st.markdown(f"""
            <div class="daily-card">
                <p class="day-title">{day['Dia']}</p>
                <div style="font-size: 32px; margin: 10px 0;">{day['Emoji']}</div>
                <div style="font-size: 16px; margin-bottom: 5px;">
                    <span style="color: #ff6b6b; font-weight: bold;">{day['Max']}°</span> | 
                    <span style="color: #4dabf7;">{day['Min']}°</span>
                </div>
                <p style="color: #a0a0a0; font-size: 12px; margin: 0;">🌧️ {day['Chuva']}%</p>
                <p style="color: #f1c40f; font-size: 12px; margin: 0;">☀️ UV: {day['UV']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Gráficos 24h
    chart_col1, chart_col2 = st.columns(2)
    BG_CARD, TEXT_MAIN, TEXT_MUTED = '#1e1e1e', '#ffffff', '#a0a0a0'

    with chart_col1:
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
            xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=True, gridcolor='#333333', zeroline=False)
        )
        st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})

    with chart_col2:
        fig_rain = px.bar(
            df_hourly, x='Hora', y='Chance de Chuva (%)', 
            title="Probabilidade de Precipitação (24h)", text_auto=True, template='plotly_dark'
        )
        fig_rain.update_traces(
            marker_color='#4dabf7', marker_line_width=0, opacity=0.8,
            textfont_size=11, textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Chuva: %{y}%<extra></extra>"
        )
        fig_rain.update_layout(
            plot_bgcolor=BG_CARD, paper_bgcolor=BG_CARD, margin=dict(l=20, r=20, t=50, b=20),
            font=dict(color=TEXT_MAIN), title_font=dict(size=16, color=TEXT_MUTED),
            yaxis=dict(range=[0, 110], showgrid=True, gridcolor='#333333'), xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_rain, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    main()
