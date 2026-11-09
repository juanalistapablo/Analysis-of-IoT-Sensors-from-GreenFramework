# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from EDA_Funcions.eda_utils import calcular_potencia_ativa_total
from EDA_Funcions.eda_graficos import preparar_dados_temporais

def carregar_e_preparar_todos(caminhos_dict):
    """
    Lê todos os CSVs, calcula a potência ativa e prepara o índice temporal.
    Retorna um único DataFrame multivariado (Matriz N x 7).
    """
    dfs = []
    for nome_predio, caminho in caminhos_dict.items():
        print(f"Carregando e preparando: {nome_predio}")
        df = pd.read_csv(caminho, low_memory=False)
        df = calcular_potencia_ativa_total(df)
        df = preparar_dados_temporais(df, coluna_tempo='timestamp_leitura_anterior')
        
        # Renomeia a coluna de potência para o nome do prédio (ex: 'CCET', 'BIO')
        df = df[['active_power.total']].rename(columns={'active_power.total': nome_predio})
        dfs.append(df)
        
    # Junta todos os DataFrames pelo índice de tempo (Outer Join para não perder dados)
    df_multivariado = pd.concat(dfs, axis=1)
    df_multivariado = df_multivariado.sort_index()
    return df_multivariado

def plotar_series_sobrepostas(df_multivariado, ano, mes, pasta_destino="graficos_cruzados"):
    """
    Gera um gráfico de linhas sobrepostas para todos os prédios no mês especificado.
    """
    os.makedirs(pasta_destino, exist_ok=True)
    
    # Filtra os dados pelo mês e ano
    dados_mes = df_multivariado[(df_multivariado.index.year == ano) & (df_multivariado.index.month == mes)]
    
    if dados_mes.empty:
        print(f"Sem dados para {mes:02d}/{ano}")
        return None

    # Cria a figura
    fig, ax = plt.subplots(figsize=(20, 8))
    
    # Plota cada prédio com cores diferentes
    sns.lineplot(data=dados_mes, dashes=False, ax=ax, linewidth=1.5, alpha=0.8)
    
    # Ajustes visuais
    ax.set_title(f"Comparação Temporal de Potência Ativa - Todos os Prédios ({mes:02d}/{ano})", fontsize=16)
    ax.set_ylabel("Potência Ativa Total (kW)", fontsize=12)
    ax.set_xlabel("Data", fontsize=12)
    ax.legend(title="Prédios", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    ax.grid(True, linestyle='--', alpha=0.6)

    # Salva o gráfico
    nome_arquivo = f"{pasta_destino}/Sobreposicao_Geral_{ano}_{mes:02d}.png"
    fig.savefig(nome_arquivo, bbox_inches="tight", dpi=150)
    plt.close(fig)
    
    print(f"Gráfico salvo: {nome_arquivo}")
    return fig

def plotar_correlacao_cruzada(df_multivariado, ano, mes, pasta_destino="graficos_cruzados"):
    """
    Gera uma matriz de correlação (Heatmap) entre os prédios.
    Útil para identificar quais prédios sofrem quedas simultâneas.
    """
    os.makedirs(pasta_destino, exist_ok=True)
    dados_mes = df_multivariado[(df_multivariado.index.year == ano) & (df_multivariado.index.month == mes)]
    
    if dados_mes.empty:
        return

    # Calcula a correlação de Pearson
    matriz_corr = dados_mes.corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(matriz_corr, annot=True, cmap="coolwarm", fmt=".2f", vmin=-1, vmax=1, ax=ax)
    ax.set_title(f"Matriz de Correlação de Potência Ativa ({mes:02d}/{ano})", fontsize=14)
    
    nome_arquivo = f"{pasta_destino}/Correlacao_Geral_{ano}_{mes:02d}.png"
    fig.savefig(nome_arquivo, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Matriz de correlação salva: {nome_arquivo}")