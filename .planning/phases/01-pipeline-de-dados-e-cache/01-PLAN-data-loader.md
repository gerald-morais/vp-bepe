---
phase: 01-pipeline-de-dados-e-cache
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - data_loader.py
autonomous: true
requirements:
  - INGST-01
  - INGST-02
  - INGST-03
  - INGST-04

must_haves:
  truths:
    - "load_schedule() retorna um DataFrame com colunas VP, CMT, Motorista, Data, Horário, Arquivo — excluindo linhas onde presente? == 'sem registro'"
    - "load_telemetry(arquivo_num) retorna um DataFrame limpo com colunas Data_Hora, Endereco, Latitude, Longitude — sem linhas de cabeçalho repetido ou NaN"
    - "Latitude e Longitude são float64, não strings"
    - "Se o arquivo .xls não existir, FileNotFoundError é levantado com mensagem contendo o nome do arquivo esperado"
  artifacts:
    - path: "data_loader.py"
      provides: "Leitura de planilha_vp.xlsx e pipeline de limpeza dos .xls"
      exports: ["load_schedule", "load_telemetry"]
  key_links:
    - from: "data_loader.load_schedule"
      to: "planilha_vp.xlsx"
      via: "pd.read_excel com engine='openpyxl'"
      pattern: "engine=['\"]openpyxl['\"]"
    - from: "data_loader.load_telemetry"
      to: "dados_vps/planilha {n}.xls"
      via: "pd.read_excel com engine='xlrd' e skiprows=4"
      pattern: "engine=['\"]xlrd['\"]"
---

<objective>
Criar data_loader.py com duas funções públicas: load_schedule() lê a planilha mestre de escalas e filtra linhas inativas; load_telemetry(arquivo_num) executa o pipeline exato de limpeza de telemetria legada e retorna um DataFrame com coordenadas numéricas.

Purpose: Fornece os dados brutos limpos para cache_manager.py. Sem este módulo o pipeline inteiro trava.
Output: data_loader.py com funções load_schedule e load_telemetry documentadas e testáveis em isolamento.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/01-pipeline-de-dados-e-cache/01-CONTEXT.md
@CLAUDE.md

<interfaces>
<!-- Contrato público de data_loader.py que cache_manager.py vai consumir -->

```python
# data_loader.py — interface pública

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent

def load_schedule() -> pd.DataFrame:
    """
    Lê planilha_vp.xlsx e retorna DataFrame com colunas:
    Data, Horário, VP, CMT, Motorista, Arquivo
    Filtra linhas onde presente? == "sem registro".
    Arquivo é convertido para int.
    """

def load_telemetry(arquivo_num: int) -> pd.DataFrame:
    """
    Lê dados_vps/planilha {arquivo_num}.xls e executa pipeline exato:
    1. pd.read_excel(..., engine='xlrd', skiprows=4, header=None)
    2. drop colunas 100% nulas (dropna axis=1 how='all')
    3. renomear: {0: 'Data_Hora', 1: 'Endereco', 2: 'Lat_Long'}
    4. drop linhas onde Data_Hora == "Data/Hora"
    5. drop linhas onde Data_Hora é NaN (dropna subset=['Data_Hora'])
    6. split Lat_Long por espaço: Latitude=float, Longitude=float
    7. drop coluna Lat_Long
    Levanta FileNotFoundError se o arquivo não existir.
    Retorna DataFrame com colunas: Data_Hora, Endereco, Latitude, Longitude
    """
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Criar load_schedule() — leitura e filtragem da planilha mestre</name>
  <files>data_loader.py</files>
  <read_first>
    - CLAUDE.md (engine constraints, estrutura de colunas de planilha_vp.xlsx, paths relativos)
    - .planning/REQUIREMENTS.md (INGST-01, INGST-02)
    - .planning/phases/01-pipeline-de-dados-e-cache/01-CONTEXT.md (D-01 sobre arquivo ausente)
  </read_first>
  <action>
Criar data_loader.py do zero com a função load_schedule():

```python
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

    # Filtrar linhas inativas (presente? == "sem registro")
    mask_sem_registro = df["presente?"].astype(str).str.contains(
        "sem registro", case=False, na=False
    )
    df = df[~mask_sem_registro].copy()

    # Garantir que Arquivo seja int (pode vir como float do Excel)
    df["Arquivo"] = df["Arquivo"].astype(int)

    return df[["Data", "Horário", "VP", "CMT", "Motorista", "Arquivo"]].reset_index(drop=True)
```

Salvar apenas este bloco em data_loader.py por agora (Task 2 vai adicionar load_telemetry).
  </action>
  <verify>
    python -c "from data_loader import load_schedule; print('load_schedule importada com sucesso')"
  </verify>
  <acceptance_criteria>
    - data_loader.py existe em C:\Users\hdusa\Documents\Github\vp-gps\data_loader.py
    - Contém a linha: `from pathlib import Path`
    - Contém a linha: `BASE_DIR = Path(__file__).parent`
    - Contém: `engine="openpyxl"` na chamada pd.read_excel para planilha_vp.xlsx
    - Contém: `str.contains("sem registro"` para filtrar linhas inativas
    - Contém: `df["Arquivo"].astype(int)` para conversão de tipo
    - Contém: `return df[["Data", "Horário", "VP", "CMT", "Motorista", "Arquivo"]]`
    - A função load_schedule é importável sem erro de sintaxe
  </acceptance_criteria>
  <done>load_schedule() definida em data_loader.py, importável, com filtragem por "sem registro" e conversão de Arquivo para int.</done>
</task>

<task type="auto">
  <name>Task 2: Criar load_telemetry() — pipeline exato de limpeza dos .xls</name>
  <files>data_loader.py</files>
  <read_first>
    - data_loader.py (estado atual após Task 1 — para não sobrescrever load_schedule)
    - CLAUDE.md (pipeline exato: skiprows=4, drop colunas nulas, renomear por índice, drop "Data/Hora", drop NaN, split Lat_Long)
    - .planning/REQUIREMENTS.md (INGST-03, INGST-04)
  </read_first>
  <action>
Adicionar a função load_telemetry() ao final de data_loader.py existente:

```python
def load_telemetry(arquivo_num: int) -> pd.DataFrame:
    """Lê e limpa arquivo de telemetria legado .xls.

    Pipeline exato (per CLAUDE.md + INGST-03, INGST-04):
    1. Ler com engine='xlrd', skiprows=4, header=None (colunas anônimas 0,1,2,...)
    2. Drop colunas 100% nulas
    3. Renomear: coluna 0 → 'Data_Hora', coluna 1 → 'Endereco', coluna 2 → 'Lat_Long'
    4. Drop linhas onde Data_Hora == "Data/Hora" (linhas de cabeçalho repetido)
    5. Drop linhas onde Data_Hora é NaN
    6. Split Lat_Long por espaço em Latitude (float) e Longitude (float)
    7. Drop coluna Lat_Long original

    Args:
        arquivo_num: Inteiro da coluna 'Arquivo' da planilha mestre.
                     Ex: 1 → 'dados_vps/planilha 1.xls'

    Raises:
        FileNotFoundError: Se o arquivo .xls não existir.

    Returns:
        DataFrame com colunas: Data_Hora, Endereco, Latitude, Longitude
    """
    xls_path = BASE_DIR / "dados_vps" / f"planilha {arquivo_num}.xls"

    if not xls_path.exists():
        raise FileNotFoundError(
            f"Arquivo de telemetria não encontrado: {xls_path.name}"
        )

    # Passo 1: Ler com skiprows=4 e sem header (colunas ficam como inteiros 0, 1, 2...)
    df = pd.read_excel(xls_path, engine="xlrd", skiprows=4, header=None)

    # Passo 2: Drop colunas 100% nulas
    df = df.dropna(axis=1, how="all")

    # Passo 3: Renomear as três primeiras colunas por índice posicional
    rename_map = {df.columns[0]: "Data_Hora", df.columns[1]: "Endereco", df.columns[2]: "Lat_Long"}
    df = df.rename(columns=rename_map)

    # Passo 4: Drop linhas de cabeçalho repetido (quando Data_Hora contém o texto "Data/Hora")
    df = df[df["Data_Hora"] != "Data/Hora"]

    # Passo 5: Drop linhas onde Data_Hora é NaN
    df = df.dropna(subset=["Data_Hora"])

    # Passo 6: Split Lat_Long → Latitude, Longitude (float)
    coords = df["Lat_Long"].astype(str).str.strip().str.split(r"\s+", n=1, expand=True)
    df["Latitude"] = pd.to_numeric(coords[0], errors="coerce")
    df["Longitude"] = pd.to_numeric(coords[1], errors="coerce")

    # Passo 7: Drop coluna original Lat_Long
    df = df.drop(columns=["Lat_Long"])

    return df[["Data_Hora", "Endereco", "Latitude", "Longitude"]].reset_index(drop=True)
```

Acrescentar ao final do arquivo (não substituir Task 1).
  </action>
  <verify>
    python -c "from data_loader import load_telemetry; print('load_telemetry importada com sucesso')"
  </verify>
  <acceptance_criteria>
    - data_loader.py contém ambas as funções: load_schedule e load_telemetry
    - Contém: `engine="xlrd"` na chamada pd.read_excel para o .xls
    - Contém: `skiprows=4, header=None` na chamada pd.read_excel
    - Contém: `df.dropna(axis=1, how="all")` para drop de colunas nulas
    - Contém: renomeação das colunas 0, 1, 2 para Data_Hora, Endereco, Lat_Long
    - Contém: `df[df["Data_Hora"] != "Data/Hora"]` para drop de cabeçalhos repetidos
    - Contém: `dropna(subset=["Data_Hora"])` para drop de linhas NaN
    - Contém: `str.split` ou `str.strip().str.split` para split de Lat_Long
    - Contém: `pd.to_numeric` para conversão de Latitude e Longitude
    - Contém: `FileNotFoundError` com mensagem incluindo o nome do arquivo
    - Contém: `return df[["Data_Hora", "Endereco", "Latitude", "Longitude"]]`
    - Ambas as funções são importáveis sem erro de sintaxe:
      python -c "from data_loader import load_schedule, load_telemetry; print('OK')"
  </acceptance_criteria>
  <done>load_telemetry() adicionada a data_loader.py. Pipeline completo: skiprows=4, drop nulos, renomear por índice, drop cabeçalhos, drop NaN, split coords, Latitude/Longitude como float.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem → Python | Arquivos .xls e .xlsx lidos do disco — podem estar corrompidos ou malformados |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-01 | Tampering | load_telemetry — leitura de .xls | accept | App de uso interno em pendrive; arquivos são exports do sistema legado, não input de usuário externo |
| T-01-02 | Denial of Service | load_telemetry — arquivo ausente | mitigate | FileNotFoundError levantado com nome do arquivo; cache_manager captura e emite st.warning() per D-01 |
| T-01-03 | Information Disclosure | BASE_DIR path | accept | Path relativo ao __file__; não expõe informação sensível |
</threat_model>

<verification>
1. python -c "from data_loader import load_schedule, load_telemetry; print('Imports OK')"
2. Verificar que data_loader.py contém `engine="openpyxl"` para .xlsx e `engine="xlrd"` para .xls
3. Verificar que data_loader.py contém `BASE_DIR = Path(__file__).parent`
4. Verificar que FileNotFoundError é levantado para arquivo inexistente:
   python -c "from data_loader import load_telemetry; load_telemetry(999)"
   — deve imprimir FileNotFoundError, não outro erro
</verification>

<success_criteria>
- data_loader.py existe com load_schedule() e load_telemetry() exportadas
- load_schedule() usa engine='openpyxl', filtra "sem registro", retorna 6 colunas
- load_telemetry() usa engine='xlrd', skiprows=4, header=None, executa pipeline exato de 7 passos
- Latitude e Longitude são float (pd.to_numeric), não strings
- FileNotFoundError levantado com nome do arquivo quando .xls ausente
- Todos os paths são relativos a Path(__file__).parent
</success_criteria>

<output>
Após conclusão, criar `.planning/phases/01-pipeline-de-dados-e-cache/01-01-SUMMARY.md` com:
- Arquivos criados: data_loader.py
- Funções exportadas: load_schedule, load_telemetry
- Decisões tomadas (engine, pipeline)
- Padrões estabelecidos para os próximos planos
</output>
