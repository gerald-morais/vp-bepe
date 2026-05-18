# Roadmap: VP-GPS — Rastreador de Viaturas

**Milestone:** v1.0 — MVP Operacional
**Granularity:** Coarse (3 phases)
**Requirements:** 16 v1 requirements | All mapped ✓

---

## Phase 1: Pipeline de Dados e Cache ✓ Complete (2026-05-18)

**Goal:** Motor de processamento completo — ler planilha mestre, limpar arquivos de telemetria legados, verificar geofencing e cachear resultado no SQLite.

**Requirements:**
- INGST-01, INGST-02, INGST-03, INGST-04
- CACHE-01, CACHE-02, CACHE-03, CACHE-04
- GEO-01, GEO-02, GEO-03

**Plans:**
1. `data_loader.py` — leitura da planilha mestre e pipeline de limpeza dos `.xls`
2. `geo_engine.py` — carregamento do KML e verificação de ponto dentro/fora do polígono
3. `cache_manager.py` — engine SQLite: criação, carga, leitura e reload

**Success Criteria:**
1. Dado um diretório `./dados_vps/` com arquivos `.xls` reais, o script processa todos os VPs válidos sem erro
2. Linhas com `presente? = "sem registro"` são ignoradas; linhas com campo vazio são processadas
3. Após processamento, `dados_processados.db` contém coluna `Status` com valores `INSIDE` ou `OUTSIDE` em cada linha
4. Na segunda execução, o `.db` é lido diretamente sem tocar nos `.xls`
5. O botão de reload deleta o `.db` e aciona reprocessamento com barra de progresso

**Dependencies:** None

---

## Phase 2: Interface Streamlit

**Goal:** Interface interativa completa com filtros em cascata, mapa geoespacial e tabela de infrações.

**Requirements:**
- UI-01, UI-02, UI-03, UI-04, UI-05

**Plans:** 3 plans
- [x] 02-01-PLAN.md — map_renderer.py: módulo puro Folium com render_map(), polígono KML, PolyLine, CircleMarkers coloridos ✓ (2026-05-18)
- [x] 02-02-PLAN.md — app.py skeleton: page config, carregamento de dados, sidebar com 4 filtros em cascata ✓ (2026-05-18)
- [ ] 02-03-PLAN.md — integração: wire render_map em app.py, título dinâmico, tabela OUTSIDE, todos os estados

**Success Criteria:**
1. Selecionar uma data na sidebar filtra a lista de VPs para apenas as escaladas naquele dia
2. Selecionar uma VP exibe sua rota completa no mapa como PolyLine
3. Pontos OUTSIDE aparecem como marcadores vermelhos visivelmente distintos dos INSIDE (azul/verde)
4. A tabela abaixo do mapa lista apenas os registros OUTSIDE da VP/filtros selecionados
5. O polígono KML está desenhado no mapa em todas as visualizações

**Dependencies:** Phase 1 (banco de dados e módulos de dados)

---

## Phase 3: Portabilidade e Entrega

**Goal:** Garantir que a aplicação rode de pendrive sem configuração — paths relativos corretos, `requirements.txt` completo e documentação de uso.

**Requirements:** (cross-cutting — garante todos os v1 em produção)

**Plans:**
1. `requirements.txt` — dependências fixadas com versões compatíveis (pandas, openpyxl, xlrd, shapely, fastkml, streamlit, streamlit-folium, sqlalchemy, lxml)
2. `README.md` — instrução de instalação (`pip install -r requirements.txt`) e execução (`streamlit run app.py`)
3. Revisão de paths — todos relativos ao `__file__` ou ao diretório atual; nenhum path hardcoded absoluto
4. Tratamento de erros de borda — arquivo `.xls` ausente, KML malformado, banco corrompido

**Success Criteria:**
1. `pip install -r requirements.txt` instala todas as dependências sem conflito em Python 3.10+
2. `streamlit run app.py` abre a aplicação a partir de qualquer diretório contendo os arquivos de dados
3. Arquivo `.xls` ausente para uma VP exibe aviso na UI sem travar o processamento das demais
4. KML ausente exibe mensagem clara ao usuário antes de tentar carregar o banco

**Dependencies:** Phase 1, Phase 2

---

## Requirement Coverage

| # | Phase | Requirements | Count |
|---|-------|-------------|-------|
| 1 | Pipeline de Dados e Cache | INGST-01..04, CACHE-01..04, GEO-01..03 | 11 |
| 2 | Interface Streamlit | UI-01..05 | 5 |
| 3 | Portabilidade e Entrega | Cross-cutting | — |

**Total v1 requirements mapped:** 16/16 ✓

---
*Roadmap created: 2026-05-18*
*Last updated: 2026-05-18 after Phase 2 planning*
