from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent


def load_schedule() -> pd.DataFrame:
    """Lê planilha_vp.xlsx e retorna escalas ativas.

    Filtra linhas onde a coluna 'presente?' contém a string 'sem registro'
    (comparação case-insensitive via str.contains).
    Converte a coluna 'Arquivo' para int para uso em load_telemetry().

    Returns:
        DataFrame com colunas: Data, Horário, VP, CMT, Motorista, Arquivo
    """
    path = BASE_DIR / "planilha_vp.xlsx"
    df = pd.read_excel(path, engine="openpyxl")

    mask_sem_registro = df["presente?"].astype(str).str.contains(
        "sem registro", case=False, na=False
    )
    df = df[~mask_sem_registro].copy()

    # Extrai o primeiro número inteiro da coluna "Arquivo".
    # Suporta valores simples ('78') e compostos ('78 - 78.1').
    df["Arquivo"] = (
        df["Arquivo"]
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
        .astype(int)
    )

    return df[["Data", "Horário", "VP", "CMT", "Motorista", "Arquivo"]].reset_index(drop=True)


def load_telemetry(arquivo_num: int) -> pd.DataFrame:
    """Lê e limpa arquivo de telemetria legado .xls.

    Estrutura real dos arquivos (descoberta por inspeção):
    - Linha 0: título do relatório
    - Linha 1: Veículo / Usuário
    - Linha 2: Data Início / Data Emissão
    - Linha 3: Data Fim
    - Linha 4 (cabeçalho): Data/Hora | [nan,nan] | Endereço | [nan,nan,nan,nan] | Lat / Long
    - Linha 5+: dados com valores nas colunas 0, 3 e 8

    As colunas úteis após skiprows=4 e header=0 são:
      col 0 → Data_Hora
      col 3 → Endereco
      col 8 → Lat_Long  (formato: '-19.9054 -43.9726')

    Args:
        arquivo_num: Inteiro da coluna 'Arquivo' da planilha mestre.
                     Ex: 1 → 'dados_vps/planilha 1.xls'

    Raises:
        FileNotFoundError: Se o arquivo .xls não existir.
        ValueError: Se a estrutura não tiver colunas suficientes.

    Returns:
        DataFrame com colunas: Data_Hora, Endereco, Latitude, Longitude
    """
    xls_path = BASE_DIR / "dados_vps" / f"planilha {arquivo_num}.xls"

    if not xls_path.exists():
        raise FileNotFoundError(
            f"Arquivo de telemetria não encontrado: {xls_path.name}"
        )

    # --- Detectar linha do cabeçalho dinamicamente ---
    # Lê sem header para encontrar a linha com "Data/Hora"
    raw = pd.read_excel(xls_path, engine="xlrd", header=None, dtype=str)

    # Arquivos sem registros contêm "Não foram encontrados resultados."
    # com células mescladas — se detectado, retorna DataFrame vazio.
    sem_dados = raw.apply(
        lambda row: row.str.contains(
            "Não foram encontrados resultados", case=False, na=False
        ).any(),
        axis=1,
    ).any()
    if sem_dados:
        return pd.DataFrame(columns=["Data_Hora", "Endereco", "Latitude", "Longitude"])

    mask = raw.apply(
        lambda row: row.str.contains("Data/Hora", case=False, na=False).any(), axis=1
    )
    matches = raw.index[mask].tolist()

    if not matches:
        raise ValueError(
            f"Cabeçalho 'Data/Hora' não encontrado em {xls_path.name}. "
            f"Primeiras linhas:\n{raw.head(6).to_string()}"
        )

    header_row = matches[0]  # ex: 4

    # --- Lê o arquivo com cabeçalho correto ---
    df = pd.read_excel(
        xls_path, engine="xlrd", header=header_row, index_col=None
    )

    # Valida número de colunas (ao menos 9 para chegar na col 8 = Lat/Long)
    if df.shape[1] < 9:
        raise ValueError(
            f"Arquivo {xls_path.name}: esperado >=9 colunas, encontrado {df.shape[1]}.\n"
            f"Colunas: {list(df.columns)}"
        )

    # Seleciona apenas as 3 colunas de interesse por posição
    df = df.iloc[:, [0, 3, 8]].copy()
    df.columns = ["Data_Hora", "Endereco", "Lat_Long"]

    # Remove linhas de sub-cabeçalho repetido e linhas vazias
    df = df[df["Data_Hora"].astype(str).str.contains(r"\d{2}/\d{2}/\d{4}", na=False)]
    df = df.dropna(subset=["Data_Hora"]).reset_index(drop=True)

    # --- Processa coordenadas: '-19.9054495 -43.9726066' ---
    coords = df["Lat_Long"].astype(str).str.strip().str.split(r"\s+", n=1, expand=True)
    df["Latitude"] = pd.to_numeric(coords[0], errors="coerce")
    df["Longitude"] = pd.to_numeric(coords[1], errors="coerce")

    df = df.drop(columns=["Lat_Long"])

    return df[["Data_Hora", "Endereco", "Latitude", "Longitude"]].reset_index(drop=True)
