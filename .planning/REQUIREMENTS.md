# Requirements: VP-GPS — Rastreador de Viaturas

**Defined:** 2026-05-18
**Core Value:** Identificar e visualizar no mapa todos os pontos de telemetria onde uma VP saiu do perímetro autorizado em determinado turno de escala.

## v1 Requirements

### Ingestão de Dados

- [ ] **INGST-01**: Sistema lê `planilha_vp.xlsx` e ignora linhas onde `presente?` contém "sem registro"
- [ ] **INGST-02**: Sistema localiza o arquivo `.xls` de telemetria pelo padrão `"planilha {n}.xls"` a partir do valor inteiro na coluna `Arquivo`
- [ ] **INGST-03**: Pipeline de limpeza exato: `skiprows=4`, remoção de colunas 100% nulas, renomeação das colunas por índice (`0=Data_Hora`, `1=Endereco`, `2=Lat_Long`), remoção de linhas onde `Data_Hora == "Data/Hora"`, remoção de linhas onde `Data_Hora` é NaN
- [ ] **INGST-04**: Coluna `Lat_Long` é dividida por espaço em duas colunas numéricas: `Latitude` (float) e `Longitude` (float)

### Cache Local

- [ ] **CACHE-01**: Na primeira execução (`.db` inexistente), processar todos os dados e salvar o DataFrame consolidado no SQLite `dados_processados.db`
- [ ] **CACHE-02**: Nas execuções seguintes, carregar dados diretamente do SQLite sem reprocessamento
- [ ] **CACHE-03**: Exibir barra de progresso (`st.progress`) no Streamlit durante o processamento inicial, VP por VP
- [ ] **CACHE-04**: Botão "Recarregar Banco de Dados" na sidebar que deleta o `.db` e força reprocessamento completo

### Geofencing

- [ ] **GEO-01**: Carregar polígono único de `perimetro.kml` usando `fastkml`; extrair coordenadas para objeto `shapely.geometry.Polygon`
- [ ] **GEO-02**: Para cada ponto de telemetria, verificar se está `INSIDE` ou `OUTSIDE` do polígono usando `shapely`
- [ ] **GEO-03**: Status `INSIDE`/`OUTSIDE` salvo como coluna `Status` em cada registro no SQLite

### Interface Streamlit

- [ ] **UI-01**: Filtros em cascata na sidebar: Data → VP → CMT → Motorista (cada filtro restringe as opções do seguinte com base nos dados carregados)
- [ ] **UI-02**: Mapa interativo (`streamlit-folium`) com o polígono KML desenhado em overlay
- [ ] **UI-03**: Rota da VP selecionada desenhada como `PolyLine` no mapa
- [ ] **UI-04**: Pontos `INSIDE` exibidos como marcadores azul/verde; pontos `OUTSIDE` como marcadores vermelhos em destaque
- [ ] **UI-05**: Tabela abaixo do mapa exibindo apenas registros `OUTSIDE` com colunas: Data_Hora, Endereco, Latitude, Longitude

## v2 Requirements

### Funcionalidades Futuras

- **EXPRT-01**: Exportar tabela de infrações (OUTSIDE) para CSV ou PDF
- **MULTI-01**: Suporte a múltiplos polígonos KML (múltiplas zonas de atuação)
- **TURNO-01**: Filtro por horário de turno para cruzar ponto de telemetria com janela de `Horário` da escala
- **HIST-01**: Histórico de sessões — comparar análises de datas diferentes

## Out of Scope

| Feature | Reason |
|---------|--------|
| Autenticação de usuários | Aplicação local de uso interno; sem acesso externo |
| Deploy em servidor/cloud | Deve rodar exclusivamente de pendrive sem dependência de rede |
| Integração em tempo real com telemetria | Apenas leitura de arquivos exportados do sistema legado |
| Suporte a múltiplos polígonos KML | Sempre um único perímetro; múltiplos na v2 |
| Aplicativo mobile | Web local via Streamlit é suficiente |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGST-01 | Phase 1 | Pending |
| INGST-02 | Phase 1 | Pending |
| INGST-03 | Phase 1 | Pending |
| INGST-04 | Phase 1 | Pending |
| CACHE-01 | Phase 1 | Pending |
| CACHE-02 | Phase 1 | Pending |
| CACHE-03 | Phase 1 | Pending |
| CACHE-04 | Phase 1 | Pending |
| GEO-01 | Phase 1 | Pending |
| GEO-02 | Phase 1 | Pending |
| GEO-03 | Phase 1 | Pending |
| UI-01 | Phase 2 | Pending |
| UI-02 | Phase 2 | Pending |
| UI-03 | Phase 2 | Pending |
| UI-04 | Phase 2 | Pending |
| UI-05 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-18*
*Last updated: 2026-05-18 after initial definition*
