# VP-GPS — Rastreador de Viaturas

## Project

Aplicação Python/Streamlit portátil para rastrear viaturas (VPs), cruzar escalas com telemetria legada e identificar deslocamentos fora de um perímetro KML. Cache SQLite local para execução instantânea de pendrive.

## GSD Workflow

This project uses the GSD (Get Shit Done) planning framework.

**Planning artifacts:** `.planning/`
**Current phase:** Phase 1 — Pipeline de Dados e Cache
**Roadmap:** `.planning/ROADMAP.md`
**Requirements:** `.planning/REQUIREMENTS.md`

### Workflow Commands

- `/gsd-plan-phase 1` — Plan Phase 1 (data pipeline + cache engine)
- `/gsd-execute-phase 1` — Execute Phase 1 plans
- `/gsd-progress` — Check current project state

### Phase Sequence

1. **Phase 1: Pipeline de Dados e Cache** — data_loader.py, geo_engine.py, cache_manager.py
2. **Phase 2: Interface Streamlit** — app.py, map_renderer.py, filtros em cascata
3. **Phase 3: Portabilidade e Entrega** — requirements.txt, README, tratamento de erros

## Key Technical Constraints

- **Engine XLS:** Sempre usar `engine='xlrd'` para os arquivos `.xls` legados
- **Engine XLSX:** Usar `openpyxl` para `planilha_vp.xlsx`
- **Paths:** Sempre relativos ao diretório do script (`Path(__file__).parent`) — nunca absolutos
- **Pipeline de limpeza:** `skiprows=4` → drop colunas nulas → renomear por índice → drop "Data/Hora" → drop NaN → split Lat_Long
- **KML:** fastkml para parsing, Shapely para verificação geométrica
- **Mapa:** streamlit-folium (não plotly)
- **DB:** SQLite via SQLAlchemy ou sqlite3 nativo

## File Structure

```
./
├── app.py                  # Entry point Streamlit
├── data_loader.py          # Leitura e limpeza dos dados
├── geo_engine.py           # KML + geofencing Shapely
├── cache_manager.py        # Engine SQLite
├── map_renderer.py         # Renderização Folium
├── requirements.txt
├── planilha_vp.xlsx        # Planilha mestre de escalas
├── perimetro.kml           # Polígono de área de atuação
├── dados_vps/              # Arquivos .xls de telemetria
│   ├── planilha 1.xls
│   └── planilha 2.xls
└── dados_processados.db    # Cache SQLite (gerado automaticamente)
```

## planilha_vp.xlsx — Colunas Conhecidas

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| Data | date | Dia do turno |
| Horário | str | Ex: "07:00 às 16:30" |
| VP | str | Identificador da viatura |
| CMT | str | Comandante |
| Motorista | str | Nome do motorista |
| Arquivo | int | Número do arquivo → "planilha {n}.xls" |
| presente? | str | "sem registro" = ignorar; vazio = processar |
