import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from data_loader import load_schedule, load_telemetry
from geo_engine import load_perimeter, apply_geofencing

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "dados_processados.db"
TABLE_NAME = "telemetria"


def get_or_process_data() -> pd.DataFrame:
    """Ponto de entrada único para app.py.

    Na primeira execução (banco inexistente): processa todos os VPs da planilha
    mestre, aplica geofencing e salva no SQLite. Exibe st.progress() VP a VP.

    Nas execuções seguintes: lê diretamente do SQLite sem tocar nos .xls.

    Returns:
        DataFrame com colunas:
        VP, CMT, Motorista, Data, Horário,
        Data_Hora, Endereco, Latitude, Longitude, Status
    """
    if DB_PATH.exists():
        return _load_from_db()

    return _process_and_cache()


def _load_from_db() -> pd.DataFrame:
    """Lê o DataFrame consolidado do SQLite."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    finally:
        conn.close()
    return df


def _process_and_cache() -> pd.DataFrame:
    """Processa todos os VPs, aplica geofencing e salva no SQLite.

    Exibe barra de progresso por VP (CACHE-03).
    VPs com arquivo .xls ausente recebem st.warning() e são puladas (D-01).
    """
    schedule = load_schedule()
    polygon = load_perimeter()

    total_vps = len(schedule)
    progress_bar = st.progress(0, text="Iniciando processamento...")

    all_frames = []

    for idx, row in enumerate(schedule.itertuples(index=False), start=1):
        vp_name = row.VP
        arquivo_num = row.Arquivo

        progress_bar.progress(
            idx / total_vps,
            text=f"Processando VP {vp_name} ({idx}/{total_vps})..."
        )

        try:
            telem_df = load_telemetry(arquivo_num)
        except FileNotFoundError:
            st.warning(
                f"VP **{vp_name}**: arquivo `planilha {arquivo_num}.xls` "
                f"não encontrado. Pulando esta viatura."
            )
            continue

        if telem_df.empty:
            st.info(
                f"VP **{vp_name}**: planilha {arquivo_num}.xls sem registros "
                f"('Não foram encontrados resultados.'). Pulando."
            )
            continue

        telem_df = apply_geofencing(telem_df, polygon)

        telem_df["VP"] = vp_name
        telem_df["CMT"] = row.CMT
        telem_df["Motorista"] = row.Motorista
        telem_df["Data"] = str(row.Data)
        telem_df["Horário"] = row.Horário

        all_frames.append(telem_df)

    progress_bar.progress(1.0, text="Processamento concluído. Salvando banco...")

    if not all_frames:
        return pd.DataFrame(columns=[
            "VP", "CMT", "Motorista", "Data", "Horário",
            "Data_Hora", "Endereco", "Latitude", "Longitude", "Status"
        ])

    consolidated = pd.concat(all_frames, ignore_index=True)

    col_order = [
        "VP", "CMT", "Motorista", "Data", "Horário",
        "Data_Hora", "Endereco", "Latitude", "Longitude", "Status"
    ]
    consolidated = consolidated[col_order]

    _save_to_db(consolidated)

    progress_bar.empty()
    return consolidated


def _save_to_db(df: pd.DataFrame) -> None:
    """Salva o DataFrame consolidado no SQLite."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


def delete_cache() -> None:
    """Apaga o banco de dados SQLite para forçar reprocessamento completo.

    Chamada pelo botão "Recarregar Banco de Dados" em app.py (D-03).
    Após esta chamada, a próxima invocação de get_or_process_data()
    reprocessará todos os dados do zero.

    Não levanta erro se o arquivo não existir.
    """
    if DB_PATH.exists():
        DB_PATH.unlink()


if __name__ == "__main__":
    print(f"DB_PATH: {DB_PATH}")
    print(f"DB existe: {DB_PATH.exists()}")
    print("cache_manager.py importado com sucesso.")
    print("Funções exportadas: get_or_process_data, delete_cache")
