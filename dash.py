import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scripts.evolucao_mensal import gerar_grafico_mensal, gerar_grafico_semanal
# =========================================================
# 2. Dados
# =========================================================

faturamento_total =65.00
vendas_periodo = 321
ticket_medio = 25.32
lucro_bruto = 4441.09
margem_lucro = 60.3
vendas_medias_diarias = 41


# =========================================================
# 2. CONFIGURAÇÃO ESTÉTICA GLOBAL
# =========================================================

st.html(
    """
    <style>
    /* Estilo do Card Principal */
    .meu-card-customizado {
        background-color: #ffffff;
        border: 1.5px solid #a3a3a3;      /* Borda fina cinza escuro conforme o print */
        border-radius: 16px;             /* Cantos bem arredondados */
        padding: 12px 8px;              /* Espaçamento interno generoso */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        display: flex;                   /* Alinha o ícone e os textos lado a lado */
        align-items: center;             /* Centraliza verticalmente o ícone com o bloco de texto */
        gap: 8px;                       /* Espaço entre o quadrado do ícone e o texto */
        min-height: 90px;               /* Garante que todos os cards tenham a mesma altura */
        width: 100%;                    /* Faz o card ocupar toda a largura da coluna */}
        box-sizing: border-box;           /* Inclui a borda e o padding no cálculo da largura total */
    }
    
    /* O Quadrado do Ícone (Placeholder) */
    .card-icone-espaco {
        width: 25px;
        height: 25px;
        border: 0.5px solid #a3a3a3;
        border-radius: 10px;             /* Cantos do ícone levemente arredondados */
        flex-shrink: 0;                  /* Impede o quadrado de esmagar se faltar espaço */
    }
    
    /* Bloco que segura os textos */
    .card-conteudo-texto {
        display: flex;
        flex-direction: column;          /* Empilha Título, Valor e Delta */
        justify-content: center;
    }
    
    /* Título (Faturamento Total, Ticket Médio, etc.) */
    .card-titulo {
        font-size: 0.7rem; 
        color: #94a3b8;                  /* Cinza mais claro/suave do print */
        font-weight: 400;
        margin-bottom: 2px;
    }
    
    /* Valor Principal (O destaque numérico) */
    .card-valor {
        font-size: 1.2rem;              /* Tamanho perfeito para não estourar nas 4 colunas */
        font-weight: 300;                /* Semi-bold */
        color: #0f172a;                  /* Azul escuro/Preto asfalto */
        line-height: 1.2;
        align-self: center;          /* Alinha o valor à esquerda do bloco de texto */
    }
    
    /* Subtexto / Delta (321 vendas no período, etc.) */
    .card-delta {
        font-size: 0.7rem; 
        color: #94a3b8;                  /* Mesma cor discreta do título */
        margin-top: 4px;
    }
    </style>
    """
)

# Cabeçalho
st.title("Visão Geral")

# ==========================================
# PRIMEIRA LINHA COM OS QUATRO CARTÕES
# ==========================================
card_11, card_12, card_13, card_14 = st.columns(4, gap="small")

with card_11:
    st.html(
        """
        <div class="meu-card-customizado">
            <div class="card-icone-espaco"></div>
            <div class="card-conteudo-texto">
                <div class="card-titulo">Faturamento Total</div>
                <div class="card-valor">""" + "R$ " + str(faturamento_total) + """</div>
                <div class="card-delta">""" + str(vendas_periodo) + """ vendas no período</div>
            </div>
        </div>
        """
    )

with card_12:
    st.html(
        """
        <div class="meu-card-customizado">
            <div class="card-icone-espaco"></div>
            <div class="card-conteudo-texto">
                <div class="card-titulo">Ticket Médio</div>
                <div class="card-valor">""" + "R$ " + str(ticket_medio) + """</div>
                <div class="card-delta">Valor médio por venda</div>
            </div>
        </div>
        """
    )

with card_13:
    st.html(
        """
        <div class="meu-card-customizado">
            <div class="card-icone-espaco"></div>
            <div class="card-conteudo-texto">
                <div class="card-titulo">Lucro Bruto</div>
                <div class="card-valor">R$ 4.441,09</div>
                <div class="card-delta">60,3% de margem</div>
            </div>
        </div>
        """
    )

with card_14:
    st.html(
        """
        <div class="meu-card-customizado">
            <div class="card-icone-espaco"></div>
            <div class="card-conteudo-texto">
                <div class="card-titulo">Vendas médias diárias</div>
                <div class="card-valor">41</div>
                <div class="card-delta">3690 vendas no período</div>
            </div>
        </div>
        """
    )

st.markdown("---")

card_21, card_22 = st.columns(2)

with card_21:
    with st.container(border=True):
        st.write("### Evolução Semanal")
        
        # 1. Chama a função do outro script que gera o gráfico
        figura_semanal = gerar_grafico_semanal()
        
        # 2. Exibe a figura gerada dentro do container do Streamlit
        st.pyplot(figura_semanal)

with card_22:
    with st.container(border=True):
        st.write("### Evolução Mensal")
        
        # 1. Chama a função do outro script que gera o gráfico
        figura_mensal = gerar_grafico_mensal()
        
        # 2. Exibe a figura gerada dentro do container do Streamlit
        st.pyplot(figura_mensal)

# Terceira linha de graficos