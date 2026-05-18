# Phase 1: Pipeline de Dados e Cache - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Motor de processamento completo — lê a planilha mestre (`planilha_vp.xlsx`), limpa os arquivos de telemetria legados (`.xls`), verifica geofencing com KML/Shapely e cacheia o resultado consolidado no SQLite. Entrega três módulos core: `data_loader.py`, `geo_engine.py`, `cache_manager.py`. Sem UI — apenas o pipeline de dados e cache.

</domain>

<decisions>
## Implementation Decisions

### Tratamento de Arquivo Ausente
- **D-01:** VP cadastrada na planilha mestre mas sem arquivo `.xls` correspondente deve exibir `st.warning()` em tempo real durante o processamento (junto com a barra de progresso), identificando o nome da VP e o arquivo esperado. O processamento continua normalmente para as demais VPs.

### Orquestração dos Módulos
- **D-02:** `cache_manager.py` encapsula toda a lógica de pipeline. `app.py` faz uma única chamada (ex: `get_or_process_data()`) e recebe o DataFrame consolidado pronto. Internamente, `cache_manager.py` decide se processa (chamando `data_loader` + `geo_engine`) ou lê diretamente do banco SQLite.
- **D-03:** O botão "Recarregar Banco de Dados" apaga `dados_processados.db` e dispara reprocessamento completo. `st.session_state` é mantido (filtros selecionados permanecem).

### Claude's Discretion
- **Schema do SQLite:** Claude decide quais colunas incluir em cada registro. Recomendação: incluir colunas de escala (VP, CMT, Motorista, Data, Horário) junto aos dados de telemetria (Data_Hora, Endereco, Latitude, Longitude, Status) para permitir filtragem direta do banco sem JOIN com a planilha mestre.
- **sqlite3 vs SQLAlchemy:** Claude decide qual engine usar. `sqlite3` nativo é mais simples e sem dependência extra — preferível para app de pendrive.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Constraints Técnicas e Pipeline
- `CLAUDE.md` — engine constraints (xlrd/openpyxl), pipeline exato de limpeza, paths relativos, estrutura de arquivos

### Requisitos da Fase
- `.planning/REQUIREMENTS.md` — INGST-01..04, CACHE-01..04, GEO-01..03 (11 requisitos mapeados para esta fase)
- `.planning/ROADMAP.md` — goal da fase e success criteria

### Contexto do Projeto
- `.planning/PROJECT.md` — decisões-chave (SQLite, fastkml+Shapely, limpeza por índice), constraints de portabilidade

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Nenhum — projeto greenfield. Todos os módulos serão criados do zero.

### Established Patterns
- Nenhum padrão pré-existente. Os padrões serão estabelecidos nesta fase.

### Integration Points
- `cache_manager.py` é o único ponto de entrada para `app.py` (a ser criado na Phase 2)
- Interface pública de `cache_manager.py`: função única que retorna DataFrame consolidado

</code_context>

<specifics>
## Specific Ideas

- Pipeline de limpeza exato documentado em CLAUDE.md deve ser seguido literalmente: `skiprows=4` → drop colunas 100% nulas → renomear por índice (`0=Data_Hora`, `1=Endereco`, `2=Lat_Long`) → drop linhas onde `Data_Hora == "Data/Hora"` → drop linhas onde `Data_Hora` é NaN → split `Lat_Long` por espaço em `Latitude` (float) e `Longitude` (float)
- Barra de progresso (`st.progress`) avança VP por VP (conforme CACHE-03)
- Arquivo `.xls` lido com `engine='xlrd'`; planilha mestre com `engine='openpyxl'`

</specifics>

<deferred>
## Deferred Ideas

Nenhuma — discussão manteve-se dentro do escopo da fase.

</deferred>

---

*Phase: 01-pipeline-de-dados-e-cache*
*Context gathered: 2026-05-18*
