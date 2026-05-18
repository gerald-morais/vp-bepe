

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from cache_manager import delete_cache, get_or_process_data
from geo_engine import load_perimeter
from map_renderer import render_heatmap, render_map

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="20Abr26 - 05Maio26 - Monitoramento de viaturas no Pau Comeu", layout="wide")

# ---------------------------------------------------------------------------
# Autenticação simples por senha
# ---------------------------------------------------------------------------
_SENHA = "VPBEPE"

if not st.session_state.get("autenticado", False):
    st.markdown("## 🔒 Acesso Restrito")
    senha = st.text_input("Senha", type="password", placeholder="Digite a senha de acesso")
    if st.button("Entrar", use_container_width=False):
        if senha == _SENHA:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta. Tente novamente.")
    st.stop()



# ---------------------------------------------------------------------------
# Carregamento de dados
# ---------------------------------------------------------------------------
st.title("20Abr26 - 05Maio26 - Monitoramento de viaturas no Pau Comeu")
polygon = load_perimeter()
df = get_or_process_data()

# Migração automática de cache: se o banco estiver desatualizado, recarrega
colunas_esperadas = {"Data", "PEL", "VP", "CMT", "Motorista", "Horário"}
if not df.empty and not colunas_esperadas.issubset(df.columns):
    delete_cache()
    st.rerun()

if df.empty:
    st.warning(
        "Nenhum dado processado. Verifique os arquivos em `dados_vps/` "
        "e clique em **Recarregar Banco de Dados**."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Constantes de filtro
# ---------------------------------------------------------------------------
TODOS = "Todos"

FILTER_DEFAULTS: dict = {
    "sel_data": TODOS,
    "sel_pel": TODOS,
    "sel_vp": TODOS,
    "sel_cmt": TODOS,
    "sel_motorista": TODOS,
    "sel_horario": TODOS,
    "show_heatmap": False,
}

# Inicializa session_state
for k, v in FILTER_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Helper: aplica filtros ao df global (exclui um filtro para cross-filter)
# ---------------------------------------------------------------------------
def _apply(
    data=None,
    vp=None,
    pel=None,
    cmt=None,
    motorista=None,
    horario=None,
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    if data and data != TODOS:
        mask &= df["Data"] == data
    if vp and vp != TODOS:
        mask &= df["VP"] == vp
    if pel and pel != TODOS:
        mask &= df["PEL"] == pel
    if cmt and cmt != TODOS:
        mask &= df["CMT"] == cmt
    if motorista and motorista != TODOS:
        mask &= df["Motorista"] == motorista
    if horario and horario != TODOS:
        mask &= df["Horário"] == horario

    return df[mask]


def _cur(k):
    return st.session_state.get(k, FILTER_DEFAULTS[k])


# Opções de cada filtro: aplicar TODOS os outros filtros (cross-filter bidirecional)
def _opts_data():
    tmp = _apply(vp=_cur("sel_vp"), pel=_cur("sel_pel"), cmt=_cur("sel_cmt"),
                 motorista=_cur("sel_motorista"), horario=_cur("sel_horario"))
    return sorted(tmp["Data"].unique().tolist())


def _opts_vp():
    tmp = _apply(data=_cur("sel_data"), pel=_cur("sel_pel"), cmt=_cur("sel_cmt"),
                 motorista=_cur("sel_motorista"), horario=_cur("sel_horario"))
    return sorted(tmp["VP"].unique().tolist())


def _opts_pel():
    tmp = _apply(data=_cur("sel_data"), vp=_cur("sel_vp"), cmt=_cur("sel_cmt"),
                 motorista=_cur("sel_motorista"), horario=_cur("sel_horario"))
    return sorted(tmp["PEL"].dropna().unique().tolist())


def _opts_cmt():
    tmp = _apply(data=_cur("sel_data"), vp=_cur("sel_vp"), pel=_cur("sel_pel"),
                 motorista=_cur("sel_motorista"), horario=_cur("sel_horario"))
    return sorted(tmp["CMT"].unique().tolist())


def _opts_motorista():
    tmp = _apply(data=_cur("sel_data"), vp=_cur("sel_vp"), pel=_cur("sel_pel"),
                 cmt=_cur("sel_cmt"), horario=_cur("sel_horario"))
    return sorted(tmp["Motorista"].unique().tolist())


def _opts_horario():
    tmp = _apply(data=_cur("sel_data"), vp=_cur("sel_vp"), pel=_cur("sel_pel"),
                 cmt=_cur("sel_cmt"), motorista=_cur("sel_motorista"))
    return sorted(tmp["Horário"].unique().tolist())


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Recarregar Dados", use_container_width=True):
            delete_cache()
            st.rerun()
    with col2:
        if st.button("🗑 Limpar Filtros", use_container_width=True):
            for k, v in FILTER_DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

    st.divider()

    # --- Data ---
    data_opts = _opts_data()
    if _cur("sel_data") not in data_opts:
        st.session_state["sel_data"] = TODOS
        
    def format_data(d):
        if d == TODOS:
            return d
        if _cur("sel_cmt") != TODOS or _cur("sel_motorista") != TODOS or _cur("sel_vp") != TODOS:
            mask = (df["Data"] == d) & (df["Status"] == "VIATURA SEM GPS")
            if _cur("sel_vp") != TODOS: mask &= df["VP"] == _cur("sel_vp")
            if _cur("sel_cmt") != TODOS: mask &= df["CMT"] == _cur("sel_cmt")
            if _cur("sel_motorista") != TODOS: mask &= df["Motorista"] == _cur("sel_motorista")
            if not df[mask].empty:
                return f"{d} (Sem GPS)"
        return d

    st.selectbox("📅 Data", [TODOS] + data_opts, key="sel_data", format_func=format_data)

    # --- PEL ---
    pel_opts = _opts_pel()
    if _cur("sel_pel") not in pel_opts:
        st.session_state["sel_pel"] = TODOS
    st.selectbox("🏢 PEL", [TODOS] + pel_opts, key="sel_pel")

    # --- VP ---
    vp_opts = _opts_vp()
    if _cur("sel_vp") not in vp_opts:
        st.session_state["sel_vp"] = TODOS
    st.selectbox("🚗 VP", [TODOS] + vp_opts, key="sel_vp")

    # --- CMT ---
    cmt_opts = _opts_cmt()
    if _cur("sel_cmt") not in cmt_opts:
        st.session_state["sel_cmt"] = TODOS
    st.selectbox("👮 CMT", [TODOS] + cmt_opts, key="sel_cmt")

    # --- Motorista ---
    motorista_opts = _opts_motorista()
    if _cur("sel_motorista") not in motorista_opts:
        st.session_state["sel_motorista"] = TODOS
    st.selectbox("🧑‍✈️ Motorista", [TODOS] + motorista_opts, key="sel_motorista")

    # --- Turno ---
    horario_opts = _opts_horario()
    if _cur("sel_horario") not in horario_opts:
        st.session_state["sel_horario"] = TODOS
    st.selectbox("🕐 Turno", [TODOS] + horario_opts, key="sel_horario")

    st.divider()

    # --- Modo de visualização ---
    st.markdown("**🗺 Visualização**")
    map_mode = st.radio(
        "Modo", ["Rota", "Mapa de Calor"], horizontal=True, label_visibility="collapsed"
    )

    if map_mode == "Mapa de Calor":
        only_outside = st.checkbox("Somente pontos fora do perímetro", value=False)

# ---------------------------------------------------------------------------
# Filtro final aplicado
# ---------------------------------------------------------------------------
filtered_df = _apply(
    data=_cur("sel_data"),
    vp=_cur("sel_vp"),
    pel=_cur("sel_pel"),
    cmt=_cur("sel_cmt"),
    motorista=_cur("sel_motorista"),
    horario=_cur("sel_horario"),
)

# Verifica se algum filtro está ativo
has_filter = (
    _cur("sel_data") != TODOS
    or _cur("sel_vp") != TODOS
    or _cur("sel_pel") != TODOS
    or _cur("sel_cmt") != TODOS
    or _cur("sel_motorista") != TODOS
    or _cur("sel_horario") != TODOS
)

# ---------------------------------------------------------------------------
# Área principal
# ---------------------------------------------------------------------------
if not has_filter:
    # Estado inicial — polígono apenas, instrução ao usuário
    m = render_map(pd.DataFrame(), polygon)
    st_folium(
        m, use_container_width=True, height=500,
        returned_objects=[], key="main_map",
    )
    st.info("Selecione ao menos um filtro na sidebar para visualizar os dados.")

else:
    # --- Resumo de Empenhos ---
    empenhos_df = filtered_df[["Data", "VP", "Horário"]].drop_duplicates()
    total_empenhos = len(empenhos_df)
    
    sem_gps_df = filtered_df[filtered_df["Status"] == "VIATURA SEM GPS"]
    n_semgps = len(sem_gps_df)
    
    texto_resumo = f"**Resumo:** 🔹 **{total_empenhos}** empenhos filtrados | ⚠️ **{n_semgps}** empenhos sem GPS"
    
    # Se houver empenhos sem GPS e um filtro específico de militar ou VP estiver ativo, mostra as datas
    if n_semgps > 0 and (_cur("sel_cmt") != TODOS or _cur("sel_motorista") != TODOS or _cur("sel_vp") != TODOS):
        datas_sem_gps = ", ".join(sorted(sem_gps_df["Data"].unique()))
        texto_resumo += f" *(Datas: {datas_sem_gps})*"
        
    st.markdown(texto_resumo)

    # --- Métricas resumidas ---
    gps_df = filtered_df[filtered_df["Status"] != "VIATURA SEM GPS"]
    total_pontos = len(gps_df)
    outside_df = gps_df[gps_df["Status"] == "OUTSIDE"].reset_index(drop=True)
    desl_df = gps_df[gps_df["Status"] == "DESLOCAMENTO"]
    n_outside = len(outside_df)
    n_desl = len(desl_df)
    n_inside = total_pontos - n_outside - n_desl

    # Verifica seleção na tabela de infrações
    selected_rows = None
    if "tabela_fora" in st.session_state:
        sel = st.session_state["tabela_fora"].get("selection", {}).get("rows", [])
        if sel:
            selected_rows = outside_df.iloc[sel]

    # --- Mapa ---
    if map_mode == "Rota":
        m = render_map(filtered_df, polygon, highlight_rows=selected_rows)
    else:
        m = render_heatmap(filtered_df, polygon, only_outside=only_outside, highlight_rows=selected_rows)

    st_folium(
        m, use_container_width=True, height=520,
        returned_objects=[], key="main_map",
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de pontos", total_pontos)
    m2.metric("🟢 Dentro", n_inside)
    m3.metric("🟠 Deslocamento", n_desl)
    m4.metric("🔴 Fora", n_outside)

    # --- Tabela de infrações ---
    vp_label = _cur("sel_vp") if _cur("sel_vp") != TODOS else "todas as VPs"
    st.subheader(f"{vp_label}: {n_outside} registros fora do perímetro")

    if outside_df.empty:
        st.success("Nenhum registro fora do perímetro para os filtros selecionados.")
    else:
        st.dataframe(
            outside_df[["Data_Hora", "VP", "CMT", "Motorista", "Endereco", "Latitude", "Longitude"]],
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="tabela_fora",
            hide_index=True
        )
