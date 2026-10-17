from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st

# =====================================================================
# CONFIGURAÇÃO GERAL
# =====================================================================
st.set_page_config(
    page_title="Weather Station · Telemetry Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

WEATHER_CODES = {
    0: ("Céu Limpo", "☀️"),
    1: ("Predom. Limpo", "🌤️"),
    2: ("Parc. Nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Nevoeiro", "🌫️"),
    48: ("Geada / Nevoeiro", "🌫️"),
    51: ("Garoa Leve", "🌦️"),
    53: ("Garoa Moderada", "🌦️"),
    55: ("Garoa Densa", "🌧️"),
    61: ("Chuva Leve", "🌧️"),
    63: ("Chuva Moderada", "🌧️"),
    65: ("Chuva Forte", "🌧️"),
    71: ("Neve Leve", "🌨️"),
    75: ("Neve Forte", "❄️"),
    80: ("Pancadas Leves", "🌦️"),
    81: ("Pancadas Moderadas", "🌧️"),
    82: ("Pancadas Severas", "⛈️"),
    95: ("Tempestade", "⛈️"),
    96: ("Tempestade c/ Granizo", "⛈️"),
    99: ("Tempestade Severa", "⛈️"),
}

# =====================================================================
# SERVIÇOS DE DADOS
# =====================================================================
@st.cache_data(ttl=3600)
def search_city(query: str):
    """Procura cidades ordenando por população decrescente."""
    if not query or len(query.strip()) < 2:
        return []
    
    q = query.strip()
    if q.lower() == "tokio":
        q = "Tokyo"

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": q, "count": 8, "language": "pt", "format": "json"}
    
    try:
        res = requests.get(url, params=params, timeout=5).json()
        results = []
        itens = sorted(res.get("results", []), key=lambda x: x.get("population", 0), reverse=True)
        
        for item in itens:
            regiao = item.get("admin1", "")
            pais = item.get("country", item.get("country_code", "")).upper()
            label = f"{item['name']}" + (f", {regiao}" if regiao else "") + f" - {pais}"
            
            results.append({
                "label": label,
                "name": item["name"],
                "lat": item["latitude"],
                "lon": item["longitude"],
                "country_code": item.get("country_code", "").lower(),
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=600)
def fetch_weather_data(lat: float, lon: float):
    """Obtém dados meteorológicos completos da Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
            "uv_index",
            "visibility",
        ],
        "hourly": ["temperature_2m", "precipitation_probability"],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ],
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        res = requests.get(url, params=params, timeout=8)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Erro ao obter dados meteorológicos: {e}")
        return None


# =====================================================================
# CSS
# =====================================================================
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #07070F; color: #FFFFFF; }
    .stApp, [data-testid="stAppViewContainer"] { background: #07070F; }
    [data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }

    .hero-wrap { 
        background: linear-gradient(135deg, #0D0010 0%, #07070F 55%, #001015 100%); 
        border-bottom: 2px solid #00D2BE; 
        padding: 1.8rem 2rem 1.4rem; 
        margin-bottom: 1.5rem; 
        position: relative; 
        overflow: hidden; 
        border-radius: 0 0 12px 12px;
    }
    .hero-wrap::before { 
        content: "WX-F1"; 
        position: absolute; 
        right: -1rem; 
        top: -2rem; 
        font-family: 'Rajdhani', sans-serif; 
        font-size: 8rem; 
        font-weight: 700; 
        color: rgba(0, 210, 190, 0.04); 
        pointer-events: none; 
    }
    .hero-title { 
        font-family: 'Rajdhani', sans-serif !important; 
        font-size: 2.8rem !important; 
        font-weight: 700 !important; 
        color: #FFFFFF !important; 
        line-height: 1 !important; 
        margin: 0 !important; 
    }
    .hero-title .accent { 
        color: #00D2BE !important; 
        text-shadow: 0 0 18px rgba(0, 210, 190, 0.5); 
    }
    .hero-sub { 
        font-size: 0.72rem; 
        font-weight: 600; 
        letter-spacing: 0.25em; 
        text-transform: uppercase; 
        color: #CBD5E1; 
        margin: 0 0 0.4rem 0; 
    }

    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        color: #00E676;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #00E676;
        border-radius: 50%;
        box-shadow: 0 0 10px #00E676;
    }

    .section-label { font-family: 'Rajdhani', sans-serif; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.25em; text-transform: uppercase; color: #00D2BE; margin-bottom: 0.2rem; }
    .section-title { font-family: 'Rajdhani', sans-serif; font-size: 1.5rem; font-weight: 700; color: #FFFFFF; margin: 0 0 1rem 0; }
    
    .weather-card { 
        background: #0F0F1C; 
        border: 1px solid #1C1C2E; 
        border-radius: 12px; 
        padding: 1.8rem; 
        position: relative; 
        overflow: hidden; 
    }
    .weather-card::after { 
        content: ""; 
        position: absolute; 
        left: 0; top: 0; bottom: 0; 
        width: 4px; 
        background: linear-gradient(180deg, #00D2BE, #00E676); 
    }
    
    .weather-city { font-family: 'Rajdhani', sans-serif; font-size: 2.2rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 10px; }
    .weather-update { font-size: 0.78rem; color: #CBD5E1; text-transform: uppercase; letter-spacing: 0.08em; margin: 0.3rem 0 1rem; display: block; }
    
    .weather-temp { font-family: 'Rajdhani', sans-serif; font-size: 4.5rem; font-weight: 700; color: #FFFFFF; line-height: 1; margin: 0; text-shadow: 0 0 20px rgba(0, 210, 190, 0.25); }
    .weather-temp span { font-size: 2rem; color: #00D2BE; }
    
    .weather-condition { font-family: 'Rajdhani', sans-serif; font-size: 1.3rem; color: #00E676; font-weight: 600; text-transform: uppercase; margin-top: 0.4rem; }
    
    .weather-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; margin-top: 1.5rem; padding-top: 1.2rem; border-top: 1px solid #222238; }
    .metric-box { display: flex; flex-direction: column; }
    .metric-label { font-size: 0.65rem; color: #CBD5E1; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; }
    .metric-val { font-family: 'Rajdhani', sans-serif; font-size: 1.3rem; font-weight: 700; color: #FFFFFF; }

    .day-card {
        background: #0F0F1C;
        border: 1px solid #1C1C2E;
        border-radius: 8px;
        padding: 0.9rem 0.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .day-name { font-family: 'Rajdhani', sans-serif; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #CBD5E1; }
    .day-icon { font-size: 1.6rem; margin: 0.3rem 0; }
    .day-rain { font-family: 'Rajdhani', sans-serif; font-size: 0.75rem; font-weight: 600; color: #00D2BE; }
    .day-temp { font-family: 'Rajdhani', sans-serif; font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-top: 0.3rem; }
    .day-min { color: #8888AA; font-size: 0.85rem; }

    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { 
        background-color: #0F0F1C !important; 
        border-color: #1C1C2E !important; 
        color: #FFFFFF !important; 
    }
    </style>
    """, unsafe_allow_html=True)


def build_telemetry_chart(hourly_data: dict) -> go.Figure:
    """Gera gráfico duplo (temperatura e probabilidade de chuva)."""
    df = pd.DataFrame(hourly_data).head(24)
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%H:%M")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df["time"],
            y=df["precipitation_probability"],
            name="Chuva (%)",
            marker_color="rgba(0, 168, 255, 0.25)",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["temperature_2m"],
            name="Temp (°C)",
            mode="lines+markers",
            line=dict(color="#00D2BE", width=3),
            marker=dict(size=4, color="#00E676"),
        ),
        secondary_y=False,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0F0F1C",
        margin=dict(l=10, r=10, t=25, b=10),
        height=265,
        font=dict(family="Rajdhani, sans-serif", color="#CBD5E1"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#CBD5E1"),
        ),
        xaxis=dict(showgrid=False, color="#CBD5E1", tickmode="linear", dtick=3),
    )

    fig.update_yaxes(title_text="°C", secondary_y=False, showgrid=True, gridcolor="#18182B", color="#CBD5E1", ticksuffix="°C")
    fig.update_yaxes(title_text="% Chuva", secondary_y=True, showgrid=False, range=[0, 100], color="#00A8FF", ticksuffix="%")

    return fig


# =====================================================================
# EXECUÇÃO PRINCIPAL
# =====================================================================
def main():
    inject_custom_css()

    st.markdown("""
    <div class="hero-wrap">
        <p class="hero-sub">Global Meteorological Telemetry</p>
        <h1 class="hero-title">Weather <span class="accent">Station</span> Hub</h1>
    </div>
    """, unsafe_allow_html=True)

    cidades_padrao = {
        "São Paulo - BR": {"lat": -23.5505, "lon": -46.6333, "flag": "br"},
        "Monza - IT": {"lat": 45.5845, "lon": 9.2744, "flag": "it"},
        "Silverstone - GB": {"lat": 52.0786, "lon": -1.0169, "flag": "gb"},
        "Suzuka - JP": {"lat": 34.8824, "lon": 136.5849, "flag": "jp"},
        "Spa-Francorchamps - BE": {"lat": 50.4372, "lon": 5.9714, "flag": "be"},
        "Austin - US": {"lat": 30.2672, "lon": -97.7431, "flag": "us"},
    }

    col_select, col_search = st.columns([1.5, 2.5])
    with col_select:
        st.markdown('<div class="section-label">Circuitos Pré-Carregados</div>', unsafe_allow_html=True)
        cidade_rapida = st.selectbox("Escolha rápida:", list(cidades_padrao.keys()), label_visibility="collapsed")
        coords = cidades_padrao[cidade_rapida]
        nome_cidade = cidade_rapida.split(" - ")[0]
        flag = coords["flag"]

    with col_search:
        st.markdown('<div class="section-label">Pesquisa Global de Cidades</div>', unsafe_allow_html=True)
        busca = st.text_input("Buscar cidade...", placeholder="Ex: Tóquio, Berlim, Curitiba...", label_visibility="collapsed")
        if busca and len(busca.strip()) >= 2:
            resultados = search_city(busca)
            if resultados:
                escolhido = st.selectbox("Resultados encontrados:", [r["label"] for r in resultados])
                info = next((r for r in resultados if r["label"] == escolhido), None)
                if info:
                    coords = {"lat": info["lat"], "lon": info["lon"]}
                    nome_cidade = info["name"]
                    flag = info["country_code"]

    with st.spinner("A carregar telemetria..."):
        data = fetch_weather_data(coords["lat"], coords["lon"])

    if not data or "current" not in data:
        st.warning("Não foi possível carregar os dados meteorológicos no momento. Tente novamente em instantes.")
        return

    cur = data["current"]
    temp = round(cur.get("temperature_2m", 0), 1)
    feels_like = round(cur.get("apparent_temperature", 0), 1)
    humidity = cur.get("relative_humidity_2m", "--")
    wind_speed = cur.get("wind_speed_10m", "--")
    wind_dir = cur.get("wind_direction_10m", 0)
    pressao = cur.get("surface_pressure", "--")
    uv_index = cur.get("uv_index", 0)
    visibilidade_km = round(cur.get("visibility", 10000) / 1000, 1)

    code = cur.get("weather_code", 0)
    cond_texto, icone = WEATHER_CODES.get(code, ("Desconhecido", "🌤️"))
    hora_local = cur.get("time", "").replace("T", " ")
    flag_url = f"https://flagcdn.com/w40/{flag}.png" if flag else ""

    col_main, col_side = st.columns([1.8, 2.2], gap="large")

    with col_main:
        st.markdown("""
        <div class="live-badge"><div class="live-dot"></div> Live Telemetry Stream</div>
        <div class="section-title">Condições de Pista</div>
        """, unsafe_allow_html=True)

        card_html = f"""<div class="weather-card">
<div class="weather-city">
{nome_cidade}
<img src="{flag_url}" style="height: 18px; border-radius: 2px;">
</div>
<span class="weather-update">Sensor Timestamp: {hora_local}</span>
<div class="weather-temp">{temp}<span>°C</span></div>
<div class="weather-condition">{cond_texto} {icone}</div>
<div class="weather-metrics">
<div class="metric-box">
<span class="metric-label">Sensação Térmica</span>
<span class="metric-val">{feels_like} <span style="font-size:0.8rem; color:#CBD5E1;">°C</span></span>
</div>
<div class="metric-box">
<span class="metric-label">Umidade Relativa</span>
<span class="metric-val">{humidity} <span style="font-size:0.8rem; color:#CBD5E1;">%</span></span>
</div>
<div class="metric-box">
<span class="metric-label">Vento</span>
<span class="metric-val">{wind_speed} <span style="font-size:0.8rem; color:#CBD5E1;">km/h</span></span>
</div>
<div class="metric-box">
<span class="metric-label">Direção & Bússola</span>
<span class="metric-val">{wind_dir}° <span style="display:inline-block; transform: rotate({wind_dir}deg); color:#00D2BE;">↑</span></span>
</div>
<div class="metric-box">
<span class="metric-label">Índice UV</span>
<span class="metric-val">{uv_index} <span style="font-size:0.8rem; color:#CBD5E1;">UV</span></span>
</div>
<div class="metric-box">
<span class="metric-label">Visibilidade</span>
<span class="metric-val">{visibilidade_km} <span style="font-size:0.8rem; color:#CBD5E1;">km</span></span>
</div>
</div>
</div>"""
        st.markdown(card_html, unsafe_allow_html=True)

    with col_side:
        st.markdown("""
        <div class="section-label">Telemetria 24 Horas</div>
        <div class="section-title">Curva de Temperatura & Janela de Chuva</div>
        """, unsafe_allow_html=True)

        if "hourly" in data:
            fig = build_telemetry_chart(data["hourly"])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown(f"""
        <div style="background: #0F0F1C; border: 1px solid #1C1C2E; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; min-height: 48px; padding: 0.6rem 1.2rem; margin-top: 0.4rem;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 4px; height: 18px; background: #FF8000; border-radius: 2px;"></div>
                <span style="font-family: 'Rajdhani', sans-serif; font-size: 0.95rem; font-weight: 600; color: #CBD5E1;">PRESSÃO BAROMÉTRICA: {pressao} hPa</span>
            </div>
            <div style="font-family: 'Rajdhani', sans-serif; font-size: 1rem; font-weight: 700; color: #00D2BE;">
                LAT {coords['lat']} | LON {coords['lon']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="section-label">Previsão Estendida</div>
    <div class="section-title">Próximos 7 Dias de Calendário</div>
    """, unsafe_allow_html=True)

    if "daily" in data:
        daily = data["daily"]
        dias_cols = st.columns(7)

        for i in range(7):
            data_iso = daily["time"][i]
            dt = datetime.strptime(data_iso, "%Y-%m-%d")
            dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            nome_dia = dias_semana[dt.weekday()] if i > 0 else "Hoje"
            data_formatada = dt.strftime("%d/%m")

            code_dia = daily["weather_code"][i]
            _, icon_dia = WEATHER_CODES.get(code_dia, ("Desconhecido", "🌤️"))
            max_t = round(daily["temperature_2m_max"][i])
            min_t = round(daily["temperature_2m_min"][i])
            chuva_prob = daily["precipitation_probability_max"][i]

            with dias_cols[i]:
                st.markdown(f"""
                <div class="day-card">
                    <div class="day-name">{nome_dia} <span style="font-size:0.75rem; color:#888;">{data_formatada}</span></div>
                    <div class="day-icon">{icon_dia}</div>
                    <div class="day-rain">💧 {chuva_prob}%</div>
                    <div class="day-temp">{max_t}° <span class="day-min">{min_t}°</span></div>
                </div>
                """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
