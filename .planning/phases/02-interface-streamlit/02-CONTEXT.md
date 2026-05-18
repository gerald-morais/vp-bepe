# Phase 2: Interface Streamlit - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

App Streamlit completo — `app.py` com sidebar de filtros em cascata, mapa Folium interativo (`map_renderer.py`) com polígono KML / rota PolyLine / marcadores coloridos, e tabela de infrações OUTSIDE. Sem lógica de dados — tudo via `cache_manager.get_or_process_data()`.

</domain>

<decisions>
## Implementation Decisions

### Fluxo dos Filtros em Cascata

- **D-01:** Estado inicial do app: mapa vazio centrado no perímetro KML, com instrução na tela — "Selecione uma Data e VP na sidebar para visualizar a rota." Nenhum dado é exibido antes de uma Data e VP serem selecionadas.
- **D-02:** Cascata real: ao selecionar uma Data, o selectbox de VP exibe **apenas as VPs escaladas naquele dia** (filtradas do DataFrame). VP → CMT → Motorista seguem a mesma lógica de restrição progressiva.
- **D-03:** Filtros CMT e Motorista são **opcionais** — o mapa e a tabela aparecem assim que Data + VP estão selecionadas. CMT e Motorista refinam o resultado mas não são pré-requisitos.

### Mapa e Marcadores

- **D-04:** Popup nos marcadores: ao clicar em qualquer marcador, exibir `Data_Hora` e `Endereço`. Popups em ambos os tipos (INSIDE e OUTSIDE).
- **D-05:** PolyLine conecta **todos os pontos** da VP na ordem cronológica de `Data_Hora` (INSIDE e OUTSIDE), mostrando a rota completa do turno.
- **D-06:** Zoom e centro: `fit_bounds()` calculado automaticamente sobre o polígono KML ao inicializar o mapa — sempre mostra o perímetro completo como contexto. Quando uma VP é selecionada, re-aplicar `fit_bounds()` incluindo tanto o perímetro quanto os pontos da rota.

### Tabela de Infrações

- **D-07:** Colunas da tabela: `Data_Hora`, `Endereço`, `Latitude`, `Longitude` — exatamente as 4 colunas do requisito UI-05. Apenas registros com `Status == 'OUTSIDE'`.
- **D-08:** Título dinâmico acima da tabela: `"N registros fora do perímetro"` (ex: "14 registros fora do perímetro"). Contador atualizado a cada mudança de filtro.

### Estados Vazios e Erros

- **D-09:** VP sem nenhum registro OUTSIDE → exibir `st.success("VP XYZ permaneceu dentro do perímetro em todo o turno.")`. Tabela não aparece ou aparece vazia com a mensagem positiva.
- **D-10:** Banco ausente na abertura → processar automaticamente via `get_or_process_data()` com a barra de progresso já embutida no `cache_manager`. Sem tela de boas-vindas ou botão extra.

### Claude's Discretion

- **Cores dos marcadores:** Claude decide os valores exatos — azul ou verde para INSIDE, vermelho para OUTSIDE (per PROJECT.md)
- **Estilo da PolyLine:** espessura, cor, opacidade — escolha do Claude
- **Tile base do mapa:** OpenStreetMap padrão salvo instrução em contrário
- **Layout exato da sidebar:** ordem dos widgets, separadores, help text — escolha do Claude
- **Estrutura interna de `map_renderer.py`:** assinatura da função pública (ex: `render_map(df, polygon)`) — escolha do Claude

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Dados e Módulos Existentes (Phase 1)
- `CLAUDE.md` — engine constraints, streamlit-folium (não plotly), paths relativos
- `.planning/phases/01-pipeline-de-dados-e-cache/01-CONTEXT.md` — decisões D-01 (warning VP ausente), D-02 (cache_manager como único ponto de entrada), D-03 (botão de reload)
- `.planning/phases/01-pipeline-de-dados-e-cache/01-03-SUMMARY.md` — interface exata de `cache_manager.py`, schema de 10 colunas do banco

### Requisitos da Phase 2
- `.planning/REQUIREMENTS.md` — UI-01..05 (filtros cascata, mapa, PolyLine, marcadores, tabela)
- `.planning/ROADMAP.md` — goal da fase e success criteria

### Contexto do Projeto
- `.planning/PROJECT.md` — constraints de portabilidade, tech stack, core value

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cache_manager.get_or_process_data()` — retorna DataFrame com 10 colunas pronto para uso
- `cache_manager.delete_cache()` — para o botão "Recarregar Banco de Dados" (D-03 da Phase 1)
- `geo_engine.load_perimeter()` — retorna `shapely.Polygon` do KML (necessário para desenhar o polígono no mapa e para `fit_bounds()`)

### Established Patterns
- Paths relativos a `Path(__file__).parent` — todos os módulos seguem este padrão
- `BASE_DIR = Path(__file__).parent` no topo de cada módulo
- Sem SQLAlchemy — sqlite3 nativo (não afeta Phase 2 diretamente)

### Integration Points
- `app.py` importa apenas `cache_manager` (D-02 Phase 1) — nunca `data_loader` ou `geo_engine` diretamente
- `map_renderer.py` recebe DataFrame filtrado e `shapely.Polygon` como argumentos; retorna objeto de mapa Folium para `st_folium()`
- Botão "Recarregar Banco de Dados" chama `delete_cache()` + `st.rerun()`

</code_context>

<specifics>
## Specific Ideas

- O mapa deve estar **sempre visível** após Data + VP selecionadas, mesmo quando não há pontos OUTSIDE — apenas o polígono e a rota INSIDE aparecem
- O título dinâmico da tabela deve usar o nome da VP no texto quando possível: ex. "VP-001: 14 registros fora do perímetro"
- `st.success()` para o estado "zero infrações" — caixa verde, visualmente distinta

</specifics>

<deferred>
## Deferred Ideas

- Exportação da tabela para CSV/PDF — v2 (EXPRT-01)
- Filtro por horário de turno — v2 (TURNO-01)
- Paginação ou limite de linhas na tabela — Claude decide se necessário pela quantidade de dados

</deferred>

---

*Phase: 02-interface-streamlit*
*Context gathered: 2026-05-18*
