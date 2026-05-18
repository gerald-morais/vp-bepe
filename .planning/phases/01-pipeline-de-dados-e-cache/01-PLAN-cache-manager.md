---
phase: 01-pipeline-de-dados-e-cache
plan: 03
type: execute
wave: 2
depends_on:
  - 01-PLAN-data-loader
  - 01-PLAN-geo-engine
files_modified:
  - cache_manager.py
autonomous: true
requirements:
  - CACHE-01
  - CACHE-02
  - CACHE-03
  - CACHE-04

must_haves:
  truths:
    - "get_or_process_data() retorna um DataFrame consolidado — na primeira execução processa tudo, nas seguintes lê o SQLite"
    - "O DataFrame retornado contém as colunas: VP, CMT, Motorista, Data, Horário, Data_Hora, Endereco, Latitude, Longitude, Status"
    - "Durante o processamento inicial, st.progress() avança VP por VP"
    - "VP com arquivo .xls ausente exibe st.warning() com nome da VP e arquivo esperado — processamento continua para as demais"
    - "delete_cache() apaga dados_processados.db do disco"
    - "Na segunda execução (dados_processados.db existe), o banco é lido diretamente sem tocar nos .xls"
  artifacts:
    - path: "cache_manager.py"
      provides: "Ponto de entrada único para app.py — orquestra data_loader + geo_engine + SQLite"
      exports: ["get_or_process_data", "delete_cache"]
  key_links:
    - from: "cache_manager.get_or_process_data"
      to: "data_loader.load_schedule"
      via: "chamada direta para obter escalas ativas"
      pattern: "load_schedule()"
    - from: "cache_manager.get_or_process_data"
      to: "data_loader.load_telemetry"
      via: "chamada por VP ativa com arquivo_num"
      pattern: "load_telemetry("
    - from: "cache_manager.get_or_process_data"
      to: "geo_engine.apply_geofencing"
      via: "aplicado ao DataFrame de telemetria de cada VP"
      pattern: "apply_geofencing("
    - from: "cache_manager.get_or_process_data"
      to: "dados_processados.db"
      via: "sqlite3 — escrita na primeira execução, leitura nas seguintes"
      pattern: "sqlite3.connect"
---

<objective>
Criar cache_manager.py — o único ponto de entrada que app.py vai chamar. Orquestra data_loader + geo_engine + SQLite: na primeira execução processa todos os VPs e salva no banco; nas seguintes lê o banco diretamente. Expõe get_or_process_data() e delete_cache().

Purpose: Isola app.py de toda a lógica de processamento. app.py nunca importa data_loader ou geo_engine diretamente — tudo passa por cache_manager (per D-02).
Output: cache_manager.py com get_or_process_data() e delete_cache() funcionando.
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
@.planning/phases/01-pipeline-de-dados-e-cache/01-01-SUMMARY.md
@.planning/phases/01-pipeline-de-dados-e-cache/01-02-SUMMARY.md

<interfaces>
<!-- Contratos dos módulos que cache_manager.py vai importar e orquestrar -->

```python
# De data_loader.py (Plan 01):
from data_loader import load_schedule, load_telemetry

# load_schedule() -> pd.DataFrame
#   Colunas: Data, Horário, VP, CMT, Motorista, Arquivo (int)
#   Já filtrado: sem linhas "sem registro"

# load_telemetry(arquivo_num: int) -> pd.DataFrame
#   Colunas: Data_Hora, Endereco, Latitude (float), Longitude (float)
#   Levanta FileNotFoundError se arquivo não existir

# De geo_engine.py (Plan 02):
from geo_engine import load_perimeter, apply_geofencing

# load_perimeter() -> shapely.geometry.Polygon
#   Levanta FileNotFoundError se perimetro.kml não existir

# apply_geofencing(df: pd.DataFrame, polygon: Polygon) -> pd.DataFrame
#   Adiciona coluna 'Status' com 'INSIDE' ou 'OUTSIDE'
#   df deve ter colunas Latitude e Longitude

# Interface pública de cache_manager.py que app.py vai chamar:
def get_or_process_data() -> pd.DataFrame:
    """
    Se dados_processados.db existe → lê e retorna DataFrame.
    Se não existe → processa todos os VPs, salva no banco, retorna DataFrame.
    DataFrame tem colunas: VP, CMT, Motorista, Data, Horário,
                           Data_Hora, Endereco, Latitude, Longitude, Status
    """

def delete_cache() -> None:
    """
    Apaga dados_processados.db se existir.
    Não levanta erro se o arquivo não existir.
    """
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Criar get_or_process_data() — orquestração completa com cache SQLite</name>
  <files>cache_manager.py</files>
  <read_first>
    - CLAUDE.md (sqlite3 nativo, paths relativos, estrutura esperada do banco)
    - .planning/REQUIREMENTS.md (CACHE-01, CACHE-02, CACHE-03)
    - .planning/phases/01-pipeline-de-dados-e-cache/01-CONTEXT.md (D-01: st.warning para VP ausente; D-02: única função pública; D-03: botão de reload)
    - .planning/phases/01-pipeline-de-dados-e-cache/01-01-SUMMARY.md (interface de data_loader)
    - .planning/phases/01-pipeline-de-dados-e-cache/01-02-SUMMARY.md (interface de geo_engine)
  </read_first>
  <action>
Criar cache_manager.py do zero com get_or_process_data():

```python
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
            # D-01: exibir aviso e continuar para próxima VP
            st.warning(
                f"VP **{vp_name}**: arquivo `planilha {arquivo_num}.xls` "
                f"não encontrado. Pulando esta viatura."
            )
            continue

        # Aplicar geofencing (adiciona coluna 'Status')
        telem_df = apply_geofencing(telem_df, polygon)

        # Enriquecer com dados da escala para permitir filtragem sem JOIN
        telem_df["VP"] = vp_name
        telem_df["CMT"] = row.CMT
        telem_df["Motorista"] = row.Motorista
        telem_df["Data"] = str(row.Data)
        telem_df["Horário"] = row.Horário

        all_frames.append(telem_df)

    progress_bar.progress(1.0, text="Processamento concluído. Salvando banco...")

    if not all_frames:
        # Retornar DataFrame vazio com schema correto se nenhum arquivo foi encontrado
        return pd.DataFrame(columns=[
            "VP", "CMT", "Motorista", "Data", "Horário",
            "Data_Hora", "Endereco", "Latitude", "Longitude", "Status"
        ])

    consolidated = pd.concat(all_frames, ignore_index=True)

    # Reordenar colunas: identificadores de escala primeiro, telemetria depois
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
```
  </action>
  <verify>
    python -c "from cache_manager import get_or_process_data; print('get_or_process_data importada OK')"
  </verify>
  <acceptance_criteria>
    - cache_manager.py existe em C:\Users\hdusa\Documents\Github\vp-gps\cache_manager.py
    - Contém: `import sqlite3` — sem SQLAlchemy
    - Contém: `BASE_DIR = Path(__file__).parent`
    - Contém: `DB_PATH = BASE_DIR / "dados_processados.db"`
    - Contém: `from data_loader import load_schedule, load_telemetry`
    - Contém: `from geo_engine import load_perimeter, apply_geofencing`
    - Contém: `if DB_PATH.exists():` — branch de cache hit
    - Contém: `st.progress(` — barra de progresso VP a VP
    - Contém: `st.warning(` — aviso para arquivo ausente (D-01)
    - Contém: `except FileNotFoundError:` — captura erro de arquivo ausente
    - Contém: `apply_geofencing(telem_df, polygon)` — geofencing aplicado
    - Contém: `telem_df["VP"] = vp_name` — enriquecimento com dados de escala
    - Contém: colunas ["VP", "CMT", "Motorista", "Data", "Horário", "Data_Hora", "Endereco", "Latitude", "Longitude", "Status"]
    - Contém: `pd.concat(all_frames, ignore_index=True)` — consolidação
    - Contém: `df.to_sql(TABLE_NAME, conn, if_exists="replace"` — persistência
    - Importação sem erro: python -c "from cache_manager import get_or_process_data; print('OK')"
  </acceptance_criteria>
  <done>get_or_process_data() criada. Verifica existência do banco; se ausente processa com progresso VP a VP, avisa VPs sem arquivo, aplica geofencing, enriquece com dados de escala e persiste no SQLite. Se banco existe, lê direto.</done>
</task>

<task type="auto">
  <name>Task 2: Criar delete_cache() — suporte ao botão "Recarregar Banco de Dados"</name>
  <files>cache_manager.py</files>
  <read_first>
    - cache_manager.py (estado atual após Task 1 — para não sobrescrever get_or_process_data)
    - .planning/REQUIREMENTS.md (CACHE-04)
    - .planning/phases/01-pipeline-de-dados-e-cache/01-CONTEXT.md (D-03: botão apaga .db e força reprocessamento)
  </read_first>
  <action>
Adicionar delete_cache() ao final de cache_manager.py existente:

```python
def delete_cache() -> None:
    """Apaga o banco de dados SQLite para forçar reprocessamento completo.

    Chamada pelo botão "Recarregar Banco de Dados" em app.py (D-03).
    Após esta chamada, a próxima invocação de get_or_process_data()
    reprocessará todos os dados do zero.

    Não levanta erro se o arquivo não existir.
    """
    if DB_PATH.exists():
        DB_PATH.unlink()
```

Acrescentar ao final do arquivo (não substituir as funções da Task 1).

Também adicionar um bloco de verificação rápida no final do arquivo (guard `__main__`) para facilitar testes manuais:

```python
if __name__ == "__main__":
    # Teste rápido sem Streamlit: verificar imports e schema
    import sys
    print(f"DB_PATH: {DB_PATH}")
    print(f"DB existe: {DB_PATH.exists()}")
    print("cache_manager.py importado com sucesso.")
    print("Funções exportadas: get_or_process_data, delete_cache")
```
  </action>
  <verify>
    python -c "from cache_manager import get_or_process_data, delete_cache; print('cache_manager completo OK')"
  </verify>
  <acceptance_criteria>
    - cache_manager.py contém as duas funções públicas: get_or_process_data e delete_cache
    - Contém: `def delete_cache() -> None:`
    - Contém: `DB_PATH.unlink()` — apaga o arquivo
    - Contém: `if DB_PATH.exists():` antes de unlink — sem erro se banco não existe
    - Contém: bloco `if __name__ == "__main__":` para teste manual
    - Importação completa sem erro:
      python -c "from cache_manager import get_or_process_data, delete_cache; print('OK')"
    - Execução direta sem Streamlit não lança erro de import:
      python cache_manager.py
      (pode lançar erro de streamlit não rodando, mas não ImportError)
  </acceptance_criteria>
  <done>delete_cache() adicionada. Apaga dados_processados.db sem erro se inexistente. Bloco __main__ para teste manual presente. cache_manager.py completo como único ponto de entrada para app.py.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| data_loader → cache_manager | DataFrames de schedules e telemetria podem ter dados inesperados |
| cache_manager → SQLite | Escrita e leitura do banco local — pode ficar corrompido |
| app.py → cache_manager | Chamada única; app.py não tem acesso aos módulos internos |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-03-01 | Denial of Service | _process_and_cache — todos os arquivos ausentes | mitigate | Retorna DataFrame vazio com schema correto se nenhum arquivo encontrado; app.py pode exibir mensagem adequada |
| T-03-02 | Tampering | dados_processados.db | accept | App de uso interno em pendrive; sem acesso de rede; usuário tem acesso físico ao dispositivo |
| T-03-03 | Denial of Service | delete_cache() invocada acidentalmente | accept | Comportamento esperado: D-03 especifica que o botão apaga o banco; st.session_state preserva filtros |
| T-03-04 | Information Disclosure | SQLite em texto claro | accept | Dados de telemetria operacional sem PII crítico; pendrive com acesso físico controlado |
</threat_model>

<verification>
1. python -c "from cache_manager import get_or_process_data, delete_cache; print('Imports OK')"
2. Verificar que cache_manager.py contém `import sqlite3` e NÃO contém `sqlalchemy`
3. Verificar que cache_manager.py contém `from data_loader import` e `from geo_engine import`
4. Verificar coluna 'Status' presente no schema: grep -n "Status" cache_manager.py
5. Verificar fluxo de cache hit: grep -n "DB_PATH.exists()" cache_manager.py — deve ter 2 ocorrências (get_or_process_data + delete_cache)
</verification>

<success_criteria>
- cache_manager.py existe com get_or_process_data() e delete_cache() exportadas
- get_or_process_data() verifica existência do banco: se existe → lê SQLite; se não → processa
- Processamento: load_schedule() → para cada VP: load_telemetry() + apply_geofencing() + enriquece com VP/CMT/Motorista/Data/Horário
- FileNotFoundError capturado → st.warning() com nome da VP e arquivo esperado (D-01)
- st.progress() avança VP por VP (CACHE-03)
- Banco tem todas as 10 colunas: VP, CMT, Motorista, Data, Horário, Data_Hora, Endereco, Latitude, Longitude, Status
- delete_cache() apaga dados_processados.db sem erro se inexistente (CACHE-04 / D-03)
- sqlite3 nativo usado — sem SQLAlchemy
- Todos os paths relativos a Path(__file__).parent
</success_criteria>

<output>
Após conclusão, criar `.planning/phases/01-pipeline-de-dados-e-cache/01-03-SUMMARY.md` com:
- Arquivos criados: cache_manager.py
- Funções exportadas: get_or_process_data, delete_cache
- Schema SQLite documentado (10 colunas)
- Decisões: sqlite3 nativo, função única para app.py, enriquecimento de telemetria com dados de escala
- Interface que app.py deve usar na Phase 2
</output>
