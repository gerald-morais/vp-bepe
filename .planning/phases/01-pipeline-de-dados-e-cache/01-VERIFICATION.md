---
phase: 01-pipeline-de-dados-e-cache
verified: 2026-05-18T00:00:00Z
status: human_needed
score: 11/11
overrides_applied: 0
human_verification:
  - test: "Processar um diretório ./dados_vps/ real com arquivos .xls e verificar que dados_processados.db é criado com coluna Status preenchida"
    expected: "Banco criado com linhas contendo Status = 'INSIDE' ou 'OUTSIDE'; barra de progresso avança VP a VP no Streamlit"
    why_human: "Requer arquivos .xls reais e ambiente Streamlit em execução. Não é possível verificar comportamento de st.progress() programaticamente sem o servidor rodando."
  - test: "Executar a aplicação pela segunda vez (banco já existente) e confirmar que os .xls não são relidos"
    expected: "Dados carregados diretamente do dados_processados.db, sem percorrer dados_vps/"
    why_human: "Requer rodadas de execução sequenciais no Streamlit para confirmar a branch de cache hit."
  - test: "Com ao menos um arquivo .xls ausente, confirmar que o aviso exibe corretamente o nome da VP e do arquivo esperado sem travar o processamento"
    expected: "st.warning() exibido para a VP com arquivo ausente; demais VPs processadas normalmente"
    why_human: "Requer ambiente Streamlit ativo e dados reais para validar o comportamento visual do aviso."
---

# Fase 1: Pipeline de Dados e Cache — Relatório de Verificação

**Objetivo da Fase:** Motor de processamento completo — ler planilha mestre, limpar telemetria legada, verificar geofencing e cachear no SQLite.
**Verificado:** 2026-05-18
**Status:** HUMAN_NEEDED — todos os artefatos verificados; 3 comportamentos requerem validação com dados reais e Streamlit ativo
**Re-verificação:** Não — verificação inicial

---

## Conquista do Objetivo

### Verdades Observáveis

| #  | Verdade                                                                                                                                        | Status       | Evidência                                                                                                                           |
|----|------------------------------------------------------------------------------------------------------------------------------------------------|--------------|-------------------------------------------------------------------------------------------------------------------------------------|
| 1  | `load_schedule()` retorna DataFrame com VP, CMT, Motorista, Data, Horário, Arquivo — excluindo linhas onde `presente?` == 'sem registro'       | VERIFICADA   | `data_loader.py` linha 28: `return df[["Data", "Horário", "VP", "CMT", "Motorista", "Arquivo"]]`; filtro `str.contains("sem registro")` linha 22 |
| 2  | `load_telemetry(arquivo_num)` retorna DataFrame limpo com colunas Data_Hora, Endereco, Latitude, Longitude — sem cabeçalhos repetidos ou NaN   | VERIFICADA   | Pipeline completo de 7 passos implementado nas linhas 60–77 de `data_loader.py`                                                     |
| 3  | Latitude e Longitude são float64, não strings                                                                                                  | VERIFICADA   | `pd.to_numeric(coords[0], errors="coerce")` e `pd.to_numeric(coords[1], errors="coerce")` — linhas 72–73                           |
| 4  | Se o arquivo .xls não existir, FileNotFoundError é levantado com mensagem contendo o nome do arquivo                                          | VERIFICADA   | `raise FileNotFoundError(f"Arquivo de telemetria não encontrado: {xls_path.name}")` — linhas 56–58                                  |
| 5  | `load_perimeter()` retorna `shapely.geometry.Polygon` carregado de perimetro.kml                                                              | VERIFICADA   | `fastkml.KML().from_string()` + `_extract_polygon()` recursivo; retorna `shapely.geometry.Polygon` — `geo_engine.py` linhas 32–43   |
| 6  | `check_status(lat, lon, polygon)` retorna a string 'INSIDE' ou 'OUTSIDE'                                                                      | VERIFICADA   | `Point(lon, lat)` (ordem correta Shapely); `return "INSIDE" if polygon.contains(point) else "OUTSIDE"` — linhas 79–80               |
| 7  | `apply_geofencing(df, polygon)` retorna DataFrame com coluna 'Status' adicionada, cada valor sendo 'INSIDE' ou 'OUTSIDE'                      | VERIFICADA   | `df["Status"] = df.apply(_row_status, axis=1)` — linha 109; fallback NaN → 'OUTSIDE' via `pd.isna()` — linha 103                   |
| 8  | Se perimetro.kml não existir, FileNotFoundError é levantado com mensagem clara                                                                | VERIFICADA   | `raise FileNotFoundError(f"Arquivo KML não encontrado: {kml_path.name}")` — `geo_engine.py` linhas 26–28                           |
| 9  | `get_or_process_data()` retorna DataFrame consolidado — na 1ª execução processa tudo, nas seguintes lê o SQLite                               | VERIFICADA   | Branch `if DB_PATH.exists(): return _load_from_db()` / `return _process_and_cache()` — `cache_manager.py` linhas 28–31             |
| 10 | DataFrame retornado contém as 10 colunas: VP, CMT, Motorista, Data, Horário, Data_Hora, Endereco, Latitude, Longitude, Status                | VERIFICADA   | `col_order` com as 10 colunas aplicado em `consolidated[col_order]` — linhas 96–100; schema vazio idêntico — linhas 89–92           |
| 11 | `delete_cache()` apaga dados_processados.db do disco                                                                                          | VERIFICADA   | `if DB_PATH.exists(): DB_PATH.unlink()` — linhas 127–128                                                                           |

**Pontuação:** 11/11 verdades verificadas

---

### Critérios de Sucesso do Roadmap

| # | Critério                                                                                                         | Status     | Evidência                                                                                                              |
|---|------------------------------------------------------------------------------------------------------------------|------------|------------------------------------------------------------------------------------------------------------------------|
| 1 | Dado um diretório `./dados_vps/` com .xls reais, processa todos os VPs válidos sem erro                         | HUMANO     | Código implementado corretamente; validação requer arquivos reais e ambiente Streamlit ativo                           |
| 2 | Linhas com `presente? = "sem registro"` ignoradas; campo vazio processado                                        | VERIFICADA | Filtro `str.contains("sem registro", case=False, na=False)` — linhas 21–23 de `data_loader.py`                        |
| 3 | Após processamento, `dados_processados.db` contém coluna `Status` com 'INSIDE' ou 'OUTSIDE' em cada linha       | HUMANO     | Lógica implementada; confirmação requer execução real com banco gerado                                                 |
| 4 | Na segunda execução, o `.db` é lido diretamente sem tocar nos .xls                                               | HUMANO     | Branch `if DB_PATH.exists()` implementada; requer duas execuções sequenciais para confirmar                            |
| 5 | O botão de reload deleta o `.db` e aciona reprocessamento com barra de progresso                                 | VERIFICADA | `delete_cache()` com `DB_PATH.unlink()` + `st.progress()` em `_process_and_cache()` implementados                     |

---

### Artefatos Requeridos

| Artefato           | Fornece                                               | Exporta                                        | Status     | Detalhes                                             |
|--------------------|-------------------------------------------------------|------------------------------------------------|------------|------------------------------------------------------|
| `data_loader.py`   | Leitura de planilha_vp.xlsx e pipeline de limpeza .xls | `load_schedule`, `load_telemetry`             | VERIFICADO | 78 linhas; pipeline completo de 7 passos; sem stubs  |
| `geo_engine.py`    | Carregamento KML e verificação de geofencing          | `load_perimeter`, `check_status`, `apply_geofencing` | VERIFICADO | 111 linhas; traversal recursivo KML; NaN tratado |
| `cache_manager.py` | Ponto de entrada único — orquestra data + geo + SQLite | `get_or_process_data`, `delete_cache`         | VERIFICADO | 136 linhas; cache hit/miss implementado; sqlite3 nativo |

---

### Verificação de Links-Chave (Wiring)

| De                                  | Para                          | Via                                    | Status     | Detalhes                                                                              |
|-------------------------------------|-------------------------------|----------------------------------------|------------|---------------------------------------------------------------------------------------|
| `data_loader.load_schedule`         | `planilha_vp.xlsx`            | `pd.read_excel(engine="openpyxl")`    | CONECTADO  | Linha 19 de `data_loader.py`; engine correto conforme CLAUDE.md                      |
| `data_loader.load_telemetry`        | `dados_vps/planilha {n}.xls`  | `pd.read_excel(engine="xlrd", skiprows=4)` | CONECTADO | Linha 60 de `data_loader.py`; engine e skiprows corretos                          |
| `geo_engine.load_perimeter`         | `perimetro.kml`               | `fastkml.KML().from_string()`         | CONECTADO  | Linhas 30–35 de `geo_engine.py`; bytes lidos e passados ao parser fastkml            |
| `geo_engine.apply_geofencing`       | DataFrame com Latitude/Longitude | `polygon.contains(Point(lon, lat))`  | CONECTADO  | Linha 105 de `geo_engine.py`; ordem (lon, lat) correta para Shapely                  |
| `cache_manager` → `data_loader`     | `load_schedule()` e `load_telemetry()` | importação direta               | CONECTADO  | Linha 7 de `cache_manager.py`; ambas chamadas em `_process_and_cache()`              |
| `cache_manager` → `geo_engine`      | `load_perimeter()` e `apply_geofencing()` | importação direta            | CONECTADO  | Linha 8 de `cache_manager.py`; ambas chamadas em `_process_and_cache()`              |
| `cache_manager` → `dados_processados.db` | SQLite                  | `sqlite3.connect(DB_PATH)`            | CONECTADO  | Linhas 36 e 110 de `cache_manager.py`; escrita com `to_sql`, leitura com `read_sql_query` |

---

### Rastreamento de Fluxo de Dados (Nível 4)

| Artefato            | Variável de Dados         | Fonte                              | Produz Dados Reais        | Status    |
|---------------------|---------------------------|------------------------------------|---------------------------|-----------|
| `cache_manager.py`  | `consolidated`            | `pd.concat(all_frames)`            | Sim — acumula frames reais de telemetria por VP | FLUINDO |
| `cache_manager.py`  | `df` (cache hit)          | `pd.read_sql_query(..., TABLE_NAME)` | Sim — lê do banco SQLite   | FLUINDO |
| `cache_manager.py`  | `telem_df["Status"]`      | `apply_geofencing(telem_df, polygon)` | Sim — calculado por `polygon.contains()` | FLUINDO |

---

### Verificações Comportamentais (Spot-Checks)

Verificações programáticas sem Streamlit ativo ou dados reais foram omitidas — os três arquivos são módulos Streamlit que dependem de `st.*` e de arquivos de dados externos. Verificação de sintaxe e lógica foi feita por leitura direta do código.

| Comportamento                                            | Verificação                          | Resultado | Status |
|----------------------------------------------------------|--------------------------------------|-----------|--------|
| `data_loader.py` exporta `load_schedule` e `load_telemetry` | Leitura de código + assinaturas     | Confirmado | PASS  |
| `geo_engine.py` exporta 3 funções com assinaturas corretas | Leitura de código + assinaturas     | Confirmado | PASS  |
| `cache_manager.py` não usa SQLAlchemy                    | `grep sqlalchemy cache_manager.py`  | Sem resultado | PASS |
| `cache_manager.py` não usa paths absolutos               | Todos os paths via `BASE_DIR = Path(__file__).parent` | Confirmado | PASS |
| Nenhum anti-padrão de stub (return null/placeholder)     | Varredura completa dos 3 arquivos   | `return None` apenas em `_extract_polygon()` (sentinel legítimo) | PASS |

---

### Cobertura de Requisitos

| Requisito   | Plano Fonte          | Descrição                                                                                        | Status     | Evidência                                                                                          |
|-------------|----------------------|--------------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------------------------------|
| INGST-01    | 01-PLAN-data-loader  | Lê planilha_vp.xlsx e ignora linhas onde `presente?` contém "sem registro"                       | SATISFEITO | `str.contains("sem registro", case=False, na=False)` — `data_loader.py` linhas 21–23              |
| INGST-02    | 01-PLAN-data-loader  | Localiza arquivo .xls pelo padrão `"planilha {n}.xls"` a partir do valor inteiro na coluna Arquivo | SATISFEITO | `BASE_DIR / "dados_vps" / f"planilha {arquivo_num}.xls"` — linha 53                              |
| INGST-03    | 01-PLAN-data-loader  | Pipeline exato: skiprows=4, drop colunas nulas, renomear por índice, drop "Data/Hora", drop NaN | SATISFEITO | Passos 1–5 implementados explicitamente nas linhas 60–69                                           |
| INGST-04    | 01-PLAN-data-loader  | Lat_Long dividido por espaço em Latitude (float) e Longitude (float)                            | SATISFEITO | `str.split(r"\s+")` + `pd.to_numeric` — linhas 71–73                                              |
| CACHE-01    | 01-PLAN-cache-manager | Na 1ª execução processa e salva em dados_processados.db                                         | SATISFEITO | `_process_and_cache()` com `_save_to_db()` chamado quando `not DB_PATH.exists()`                  |
| CACHE-02    | 01-PLAN-cache-manager | Nas execuções seguintes, carrega diretamente do SQLite                                           | SATISFEITO | `if DB_PATH.exists(): return _load_from_db()` — linha 28                                          |
| CACHE-03    | 01-PLAN-cache-manager | Exibir `st.progress()` durante processamento inicial, VP por VP                                  | SATISFEITO | `st.progress(idx / total_vps, text=f"Processando VP {vp_name}...")` — linhas 62–65                |
| CACHE-04    | 01-PLAN-cache-manager | Botão de reload deleta .db e força reprocessamento                                               | SATISFEITO | `delete_cache()` com `DB_PATH.unlink()` implementada; interface documentada em SUMMARY para Phase 2 |
| GEO-01      | 01-PLAN-geo-engine   | Carregar polígono único de perimetro.kml usando fastkml; extrair para shapely.geometry.Polygon   | SATISFEITO | `fastkml.KML().from_string()` + `_extract_polygon()` recursivo — `geo_engine.py` linhas 32–43     |
| GEO-02      | 01-PLAN-geo-engine   | Para cada ponto verificar INSIDE ou OUTSIDE usando shapely                                       | SATISFEITO | `polygon.contains(Point(lon, lat))` — linha 80; aplicado por `apply_geofencing()` linha 109       |
| GEO-03      | 01-PLAN-geo-engine   | Status INSIDE/OUTSIDE salvo como coluna 'Status' em cada registro no SQLite                      | SATISFEITO | Coluna 'Status' incluída em `col_order` — linhas 96–100; persistida via `df.to_sql()`             |

**Todos os 11 requisitos da Fase 1 satisfeitos pelo código.**

Nota: UI-01 a UI-05 são requisitos da Fase 2 e não são escopo desta verificação.

---

### Anti-Padrões Encontrados

| Arquivo          | Linha | Padrão              | Severidade | Impacto                                                                                          |
|------------------|-------|---------------------|------------|--------------------------------------------------------------------------------------------------|
| `geo_engine.py`  | 61    | `return None`       | INFO       | Sentinel legítimo de `_extract_polygon()` — verificado que não é stub; `load_perimeter()` captura este caso e lança `ValueError` |

Nenhum bloqueador ou aviso encontrado. O único `return None` identificado é a saída esperada do helper de traversal recursivo quando nenhum polígono existe, sendo explicitamente tratado pelo código chamador.

---

### Verificação Humana Necessária

#### 1. Processamento de dados reais com barra de progresso

**Teste:** Executar `streamlit run app.py` (ou `python -c "from cache_manager import get_or_process_data; get_or_process_data()"` sem UI) com arquivos `.xls` reais em `./dados_vps/` e `perimetro.kml` válido na raiz.
**Esperado:** `dados_processados.db` criado; coluna `Status` preenchida com `'INSIDE'` ou `'OUTSIDE'` em todas as linhas; barra de progresso avança VP por VP no Streamlit.
**Por que humano:** Requer arquivos de dados reais e ambiente Streamlit ativo. Não é verificável estaticamente.

#### 2. Comportamento de cache hit (segunda execução)

**Teste:** Com `dados_processados.db` já existente, executar a aplicação novamente e confirmar que nenhum arquivo `.xls` é relido.
**Esperado:** Dados carregados em fração do tempo; sem acesso a `dados_vps/`.
**Por que humano:** Requer duas execuções sequenciais no ambiente Streamlit e não pode ser confirmado sem rodar a aplicação.

#### 3. Aviso para VP com arquivo ausente

**Teste:** Remover um dos arquivos `.xls` de `dados_vps/` e executar a aplicação no Streamlit.
**Esperado:** `st.warning()` exibido com nome da VP e nome do arquivo esperado; demais VPs processadas normalmente; `dados_processados.db` criado sem a VP ausente.
**Por que humano:** Requer ambiente Streamlit ativo para visualizar o componente de warning e verificar que o processamento continua.

---

### Resumo dos Gaps

Nenhum gap técnico encontrado. O código dos três módulos implementa completamente todos os must-haves do plano e todos os 11 requisitos da Fase 1.

O status `human_needed` reflete apenas que 3 comportamentos de runtime (processamento com dados reais, cache hit em segunda execução, e aviso de VP ausente) não podem ser verificados programaticamente sem arquivos de dados e Streamlit ativo. A lógica implementada para todos eles está correta e completa.

---

_Verificado: 2026-05-18_
_Verificador: Claude (gsd-verifier)_
