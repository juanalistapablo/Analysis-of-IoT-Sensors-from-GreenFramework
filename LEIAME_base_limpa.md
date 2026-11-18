# Base limpa + camada de regras

    python rodar_base_limpa.py "<pasta com dados_AAAA_MM.csv>" saida/

Gera em `saida/`:
- `leituras_dedup.pkl` — leituras brutas sem duplicatas, com `ts` = timestamp_leitura e `dt_min` recalculado
- `base_5min.pkl` — grade comum de 5 min para os 7 prédios (`tem_dado`, médias por fase, totais, `v_min`, `deseq_i`, `tipo_dia`, `noite`, hora cíclica)
- `calendario.csv` — classificação dos dias (calendários UFMA 2025 e 2026)
- `eventos_regras.csv` — eventos detectados por regra (categoria A–D, escopo LOCAL/SISTEMICO/INDETERMINADO)

Módulos em `tcc_pipeline/`: carregamento, calendario, reamostragem, regras.
