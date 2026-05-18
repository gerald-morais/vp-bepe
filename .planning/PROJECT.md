# VP-GPS — Rastreador de Viaturas com Análise de Perímetro

## What This Is

Aplicação Python/Streamlit portátil (roda de pendrive) para cruzar escalas de viaturas policiais (VPs) com relatórios de telemetria legados em `.xls`, identificando deslocamentos fora de um perímetro geográfico definido em KML. Os dados processados são cacheados em SQLite local para execução instantânea em campo.

## Core Value

Identificar e visualizar no mapa todos os pontos de telemetria onde uma VP saiu do perímetro autorizado em determinado turno de escala.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Leitura e limpeza do pipeline exato de arquivos `.xls` legados (skiprows=4, remoção de colunas vazias, renomeação por índice, remoção de cabeçalhos repetidos, split de coordenadas)
- [ ] Cruzamento da planilha mestre `planilha_vp.xlsx` com os arquivos de telemetria pelo campo `Arquivo` → `"planilha {n}.xls"`
- [ ] Ignorar linhas com `presente? = "sem registro"` (VP sem GPS)
- [ ] Cache SQLite local: processamento na primeira execução, carga direta nas seguintes
- [ ] Verificação de ponto dentro/fora do polígono KML usando Shapely
- [ ] Botão "Recarregar Banco de Dados" na sidebar para forçar reprocessamento
- [ ] Barra de progresso no Streamlit durante o processamento inicial
- [ ] Filtros em cascata na sidebar: Data → VP → CMT → Motorista
- [ ] Mapa interativo com polígono KML, rota da VP e marcadores coloridos (azul/verde = INSIDE, vermelho = OUTSIDE)
- [ ] Tabela de resultados mostrando apenas registros OUTSIDE (Data_Hora, Endereço, Latitude, Longitude)

### Out of Scope

- Autenticação de usuários — aplicação local de uso interno
- Deploy em servidor/cloud — deve rodar exclusivamente de pendrive
- Suporte a múltiplos polígonos KML — sempre um único perímetro
- Integração em tempo real com sistema de telemetria — apenas leitura de arquivos exportados

## Context

- **Ambiente de execução:** Pendrive USB, sem garantia de internet. Todos os dados e dependências devem ser locais.
- **Dados legados:** Os arquivos `.xls` são exportações de sistema legado com formatação visual quebrada (células mescladas, cabeçalhos repetidos por página). O pipeline de limpeza é fixo e bem definido pelo operador.
- **Planilha mestre (`planilha_vp.xlsx`):** Colunas conhecidas: `Data` (dia do turno), `Horário` (ex: "07:00 às 16:30"), `VP` (identificador da viatura), `CMT` (comandante), `Motorista`, `Arquivo` (inteiro mapeado para nome do .xls), `presente?` (string "sem registro" = ignorar, vazio = processar).
- **KML:** Único polígono representando a área de atuação autorizada.
- **Banco SQLite:** `./dados_processados.db` — cache de todo o DataFrame consolidado e anotado com status INSIDE/OUTSIDE.

## Constraints

- **Tech Stack**: Python + Streamlit + Pandas + Shapely + fastkml + SQLite + streamlit-folium — nenhuma dependência externa de rede
- **Portabilidade**: Paths relativos ao diretório do script; estrutura de arquivos fixa (`./dados_vps/`, `./planilha_vp.xlsx`, `./perimetro.kml`, `./dados_processados.db`)
- **Compatibilidade**: `xlrd` engine para leitura dos `.xls` legados; `openpyxl` para o `.xlsx` da planilha mestre
- **Performance**: Processamento pesado ocorre apenas na primeira execução ou após "Recarregar Banco de Dados"; execução normal deve ser instantânea

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite como cache local | Elimina reprocessamento em cada abertura; crítico para uso em campo sem espera | — Pending |
| fastkml + Shapely para KML | fastkml lê o KML, Shapely faz a verificação geométrica de ponto dentro do polígono | — Pending |
| streamlit-folium para mapa | Suporte nativo a Folium no Streamlit; permite polígonos, rotas e marcadores interativos | — Pending |
| Limpeza por índice de coluna | Arquivos legados têm colunas instáveis; posições fixas são mais confiáveis que nomes | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-18 after initialization*
