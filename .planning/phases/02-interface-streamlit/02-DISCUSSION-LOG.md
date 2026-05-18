# Phase 2: Interface Streamlit - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-18
**Phase:** 02-interface-streamlit
**Areas discussed:** Fluxo dos filtros, Mapa e marcadores, Tabela de infrações, Estados vazios e erros

---

## Fluxo dos Filtros

| Option | Description | Selected |
|--------|-------------|----------|
| Exigir Data + VP antes de mostrar o mapa | Sidebar guia o usuário passo a passo | |
| Mostrar todos os dados no mapa desde o início | Mapa exibe todos os pontos ao abrir | |
| Mostrar mapa vazio com instrução | Mapa aparece centrado no perímetro, sem pontos, com texto orientador | ✓ |

**User's choice:** Mapa vazio com instrução "Selecione uma Data e VP na sidebar para visualizar a rota"

---

| Option | Description | Selected |
|--------|-------------|----------|
| Opcionais — CMT e Motorista refinem mas não são necessários | Mapa aparece com Data + VP | ✓ |
| Todos obrigatórios antes de mostrar o mapa | Exige Data, VP, CMT e Motorista | |

**User's choice:** CMT e Motorista são opcionais

---

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas VPs escaladas na data selecionada | Cascata real | ✓ |
| Todas as VPs sempre visíveis | Filtros independentes | |

**User's choice:** Cascata real — VP restrita à data selecionada

---

## Mapa e Marcadores

| Option | Description | Selected |
|--------|-------------|----------|
| Popup com Data_Hora e Endereço | Informativo e conciso | ✓ |
| Popup com todas as colunas | Muito verboso | |
| Sem popup | Sem clique | |

**User's choice:** Popup com Data_Hora e Endereço

---

| Option | Description | Selected |
|--------|-------------|----------|
| Todos os pontos ligados em ordem de Data_Hora | Rota completa do turno | ✓ |
| Apenas pontos OUTSIDE ligados | Foco nas infrações | |
| Sem PolyLine | Apenas marcadores | |

**User's choice:** Todos os pontos em ordem cronológica (rota completa)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Centralizar no perímetro KML automaticamente | fit_bounds() no polígono | ✓ |
| Centralizar na rota da VP selecionada | fit_bounds() nos pontos da VP | |
| Zoom e centro fixos no código | Constantes hardcoded | |

**User's choice:** fit_bounds() centralizado no perímetro KML

---

## Tabela de Infrações

| Option | Description | Selected |
|--------|-------------|----------|
| Data_Hora, Endereço, Latitude, Longitude | Per requisito UI-05 | ✓ |
| Adicionar VP e CMT | 6 colunas | |
| Claude decide | Flexível | |

**User's choice:** 4 colunas per UI-05

---

| Option | Description | Selected |
|--------|-------------|----------|
| Sim — contador dinâmico acima da tabela | "N registros fora do perímetro" | ✓ |
| Não — tabela sem título separado | | |

**User's choice:** Título com contador dinâmico

---

## Estados Vazios e Erros

| Option | Description | Selected |
|--------|-------------|----------|
| Mensagem positiva com st.success() | "VP XYZ permaneceu dentro do perímetro" | ✓ |
| Tabela vazia sem mensagem | Silencioso | |

**User's choice:** st.success() com mensagem positiva

---

| Option | Description | Selected |
|--------|-------------|----------|
| Processar automaticamente ao abrir | Sem interação extra | ✓ |
| Exibir botão 'Processar dados' | Tela de boas-vindas | |

**User's choice:** Processamento automático na abertura

---

## Claude's Discretion

- Cores exatas dos marcadores (azul/verde = INSIDE, vermelho = OUTSIDE)
- Estilo da PolyLine (espessura, cor, opacidade)
- Tile base do mapa
- Layout exato da sidebar
- Assinatura da função pública de `map_renderer.py`

## Deferred Ideas

- Exportação CSV/PDF — v2 (EXPRT-01)
- Filtro por horário de turno — v2 (TURNO-01)
