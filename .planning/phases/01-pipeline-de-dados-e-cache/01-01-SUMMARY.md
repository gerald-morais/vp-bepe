---
plan: 01-01
phase: 01-pipeline-de-dados-e-cache
status: complete
---

# Summary: Plan 01-01 — Data Loader

## What Was Built

`data_loader.py` com duas funções públicas que formam a base do pipeline de ingestão.

## Files Created

- `data_loader.py`

## Functions Exported

- `load_schedule()` — lê `planilha_vp.xlsx` com `engine="openpyxl"`, filtra linhas onde `presente?` contém "sem registro" (case-insensitive), converte coluna `Arquivo` para int, retorna 6 colunas: Data, Horário, VP, CMT, Motorista, Arquivo
- `load_telemetry(arquivo_num)` — lê `dados_vps/planilha {n}.xls` com `engine="xlrd"` e `skiprows=4, header=None`, executa pipeline de 7 passos (drop nulos → renomear por índice → drop cabeçalhos repetidos → drop NaN → split Lat_Long → float), levanta `FileNotFoundError` com nome do arquivo se ausente

## Decisions Made

- `engine="openpyxl"` para .xlsx; `engine="xlrd"` para .xls legado — constraint obrigatória per CLAUDE.md
- `BASE_DIR = Path(__file__).parent` para todos os paths — portabilidade de pendrive
- Renomeação de colunas por índice posicional (não por nome) — robusto a variações de header no .xls
- `pd.to_numeric(..., errors="coerce")` para Latitude/Longitude — coordenadas inválidas viram NaN ao invés de crashar

## Patterns Established for Next Plans

- Todos os paths relativos a `BASE_DIR = Path(__file__).parent`
- `FileNotFoundError` com `xls_path.name` no message (não path completo)
- Interface do DataFrame de telemetria: colunas `Data_Hora, Endereco, Latitude (float64), Longitude (float64)`

## Self-Check: PASSED

- `from data_loader import load_schedule, load_telemetry` — importa sem erro
- `engine="openpyxl"` presente para .xlsx
- `engine="xlrd"` + `skiprows=4, header=None` presente para .xls
- `FileNotFoundError` com nome do arquivo presente
- Latitude/Longitude como float via `pd.to_numeric`
