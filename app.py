from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from cache_manager import delete_cache, get_or_process_data
from geo_engine import load_perimeter
from map_renderer import render_map

# Page config DEVE ser a primeira chamada st.* executável
st.set_page_config(page_title="VP-GPS — Rastreador de Viaturas", layout="wide")

st.title("Rastreador de Viaturas — VP-GPS")

# Carregamento de polígono e dados
# load_perimeter() propaga FileNotFoundError / ValueError nativamente (T-02-04)
polygon = load_perimeter()
df = get_or_process_data()

# Guard: DataFrame vazio — evita crash em df["Data"].unique() com df vazio (Pitfall 3)
if df.empty:
    st.warning(
        "Nenhum dado processado. Verifique os arquivos em `dados_vps/` "
        "e clique em **Recarregar Banco de Dados**."
    )
    st.stop()

# Sidebar com filtros em cascata (UI-01, D-02, D-03)
with st.sidebar:
    st.header("Filtros")

    if st.button("Recarregar Banco de Dados", use_container_width=True):
        delete_cache()
        st.rerun()

    st.divider()

    # Nível 1: Data
    available_dates = sorted(df["Data"].unique())
    selected_date = st.selectbox("Data", options=available_dates)

    # Nível 2: VP — apenas VPs escaladas na data selecionada (D-02)
    df_by_date = df[df["Data"] == selected_date]
    available_vps = sorted(df_by_date["VP"].unique().tolist())
    selected_vp = st.selectbox("VP", options=available_vps)

    # Nível 3: CMT — opcional (D-03), restrito à VP selecionada
    df_by_vp = df_by_date[df_by_date["VP"] == selected_vp]
    available_cmts = sorted(df_by_vp["CMT"].unique().tolist())
    selected_cmt = st.selectbox("CMT (opcional)", options=["Todos"] + available_cmts)

    # Nível 4: Motorista — opcional, restrito ao CMT selecionado
    if selected_cmt == "Todos":
        df_by_cmt = df_by_vp
    else:
        df_by_cmt = df_by_vp[df_by_vp["CMT"] == selected_cmt]

    available_motoristas = sorted(df_by_cmt["Motorista"].unique().tolist())
    selected_motorista = st.selectbox(
        "Motorista (opcional)", options=["Todos"] + available_motoristas
    )

    if selected_motorista == "Todos":
        df_by_motorista = df_by_cmt
    else:
        df_by_motorista = df_by_cmt[df_by_cmt["Motorista"] == selected_motorista]

    # Nível 5: Faixa de Horário — opcional, baseada nos turnos disponíveis
    # A coluna "Horário" contém a faixa do turno da escala (ex: "07:00 - 16:30")
    available_turnos = sorted(df_by_motorista["Horário"].unique().tolist())
    selected_turno = st.selectbox(
        "Faixa de Horário (opcional)", options=["Todos"] + available_turnos
    )

    if selected_turno == "Todos":
        filtered_df = df_by_motorista
    else:
        filtered_df = df_by_motorista[df_by_motorista["Horário"] == selected_turno]

# --- Main area ---
if selected_date and selected_vp:
    # Renderizar mapa com rota e marcadores (UI-02, UI-03, UI-04, D-06)
    m = render_map(filtered_df, polygon)
    st_folium(
        m,
        use_container_width=True,
        height=500,
        returned_objects=[],    # evita re-run ao rolar/dar zoom (Pitfall 1 RESEARCH.md)
        key="main_map",         # stable key — evita white flash
    )

    # Tabela de infrações OUTSIDE (UI-05, D-07, D-08, D-09)
    outside_df = filtered_df[filtered_df["Status"] == "OUTSIDE"]

    # Título dinâmico com nome da VP, turno selecionado e contagem (D-08)
    turno_label = f" | Turno {selected_turno}" if selected_turno != "Todos" else ""
    st.subheader(f"VP-{selected_vp}{turno_label}: {len(outside_df)} registros fora do perímetro")

    if outside_df.empty:
        # VP sem infrações (D-09)
        st.success(
            f"VP {selected_vp} permaneceu dentro do perímetro em todo o turno."
        )
    else:
        # Tabela com exatamente 4 colunas (D-07)
        st.dataframe(
            outside_df[["Data_Hora", "Endereco", "Latitude", "Longitude"]],
            use_container_width=True,
        )
else:
    # Estado inicial: mapa centrado no perímetro + instrução (D-01, D-06)
    m = render_map(pd.DataFrame(), polygon)
    st_folium(
        m,
        use_container_width=True,
        height=500,
        returned_objects=[],
        key="main_map",
    )
    st.info("Selecione uma Data e VP na sidebar para visualizar a rota.")
