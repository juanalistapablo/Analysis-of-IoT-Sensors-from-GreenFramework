import os
import glob
import pandas as pd
import gc
import shutil

def processar_e_exportar_lotes(arquivos_csv, pasta_temp, tamanho_lote, func_pipeline, func_separar):
    """Lê os ficheiros em blocos, aplica limpeza e guarda como pedaços temporários."""
    print("Fase 1: Processar e separar pedaços temporários...")
    if not os.path.exists(pasta_temp): os.makedirs(pasta_temp)
    
    for arquivo in arquivos_csv:
        nome_arquivo = os.path.basename(arquivo)
        print(f"A processar: {nome_arquivo}")
        
        for i, df_chunk in enumerate(pd.read_csv(arquivo, chunksize=tamanho_lote)):
            df_limpo = func_pipeline(df_chunk)
            tabelas_predios = func_separar(df_limpo, coluna='item_name')
            
            for nome_predio, df_predio in tabelas_predios.items():
                nome_seguro = str(nome_predio).replace(" ", "_")
                nome_temp = f"{nome_seguro}_{nome_arquivo}_lote_{i}.csv"
                df_predio.to_csv(os.path.join(pasta_temp, nome_temp), index=False)
                
            del df_chunk, df_limpo, tabelas_predios
            gc.collect()

def consolidar_csvs_finais(pasta_temp, pasta_destino):
    """Junta todos os pedaços temporários, alinhando as colunas dinâmicas."""
    print("\nFase 2: Alinhar colunas dinâmicas e gerar CSVs finais...")
    if not os.path.exists(pasta_destino): os.makedirs(pasta_destino)
    
    predios_encontrados = set([f.split('_dados_')[0] for f in os.listdir(pasta_temp)])
    
    for predio in predios_encontrados:
        arquivos_do_predio = glob.glob(os.path.join(pasta_temp, f"{predio}_*.csv"))
        lista_dfs = [pd.read_csv(f) for f in arquivos_do_predio]
        
        if lista_dfs:
            df_final_predio = pd.concat(lista_dfs, ignore_index=True)
            caminho_final = os.path.join(pasta_destino, f"{predio}.csv")
            df_final_predio.to_csv(caminho_final, index=False)
            print(f"✅ {predio}.csv salvo de forma segura com {df_final_predio.shape[1]} colunas unificadas!")
            
            del df_final_predio, lista_dfs
            gc.collect()
            
    shutil.rmtree(pasta_temp)
    print("\nProcesso totalmente concluído! Pode iniciar a EDA.")