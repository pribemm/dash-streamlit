# report_visaoGeral.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scripts.cards import (
    get_metricas_periodo,
    sales_data,
    recipe_data,
    products_data
)

from scripts.charts import (get_dados_agregados_periodo, 
                            get_top_produtos_mais_vendidos)
# Configuração da página
st.set_page_config(
    page_title="Dashboard Visão Geral",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS (mantenha seus estilos existentes)
st.html("""
<style>
.meu-card-customizado {
    background-color: #ffffff;
    border: 1.5px solid #a3a3a3;
    border-radius: 16px;
    padding: 12px 8px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 90px;
    width: 100%;
    box-sizing: border-box;
    transition: transform 0.2s, box-shadow 0.2s;
}
.meu-card-customizado:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.card-icone-espaco {
    width: 25px;
    height: 25px;
    border: 0.5px solid #a3a3a3;
    border-radius: 10px;
    flex-shrink: 0;
}
.card-conteudo-texto {
    display: flex;
    flex-direction: column;
    justify-content: center;
    flex: 1;
}
.card-titulo {
    font-size: 0.7rem;
    color: #94a3b8;
    font-weight: 400;
    margin-bottom: 2px;
}
.card-valor {
    font-size: 1.2rem;
    font-weight: 600;
    color: #0f172a;
    line-height: 1.2;
}
.card-delta {
    font-size: 0.7rem;
    color: #94a3b8;
    margin-top: 4px;
}
</style>
""")


col_title, col_filter = st.columns([3, 1])

with col_title:
    st.title(" Visão Geral")

with col_filter:
    st.markdown("<br>", unsafe_allow_html=True)  # Pequeno espaçamento para alinhar
    periodo = st.selectbox(
        "Selecione o período:",
        options=["Anual", "Semestral", "Trimestral", "Mensal", "Semanal"],
        index=0,
        label_visibility="collapsed"  # Esconde o label do selectbox
    )
    top_n = st.slider(
    "Número de produtos no ranking:",
    min_value=3,
    max_value=10,
    value=5,
    help="Selecione quantos produtos deseja visualizar no gráfico"
)


st.markdown("---")
    
st.caption(f"📅 Última atualização: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")

# Mapeamento de períodos
periodo_map = {
    "Anual": "anual",
    "Semestral": "semestral",
    "Trimestral": "trimestral",
    "Mensal": "mensal",
    "Semanal": "semanal"
}

periodo_key = periodo_map[periodo]

# Carregar métricas e dados agregados
@st.cache_data(ttl=300)
def load_metrics(periodo_key):
    metricas = get_metricas_periodo(sales_data, recipe_data, products_data, periodo_key)
    dados_agregados = get_dados_agregados_periodo(sales_data, recipe_data, products_data, periodo_key)
    top_produtos = get_top_produtos_mais_vendidos(sales_data, recipe_data, products_data, periodo_key, top_n=5)
    return metricas, dados_agregados, top_produtos

metricas, dados_agregados, top_produtos = load_metrics(periodo_key)

# Se o usuário mudar o número de produtos, recarregar
if top_n != 5:
    top_produtos = get_top_produtos_mais_vendidos(sales_data, recipe_data, products_data, periodo_key, top_n=top_n)

# Primeira linha de cards
col1, col2, col3, col4 = st.columns(4, gap="small")

with col1:
    st.html(f"""
    <div class="meu-card-customizado">
        <div class="card-icone-espaco">💰</div>
        <div class="card-conteudo-texto">
            <div class="card-titulo">Faturamento Total</div>
            <div class="card-valor">R$ {metricas['receita']:,.2f}</div>
            <div class="card-delta">{metricas['qtd_vendas']} vendas no período</div>
        </div>
    </div>
    """)

with col2:
    st.html(f"""
    <div class="meu-card-customizado">
        <div class="card-icone-espaco">🎫</div>
        <div class="card-conteudo-texto">
            <div class="card-titulo">Ticket Médio</div>
            <div class="card-valor">R$ {metricas['ticket_medio']:,.2f}</div>
            <div class="card-delta">Valor médio por venda - {periodo}</div>
        </div>
    </div>
    """)

with col3:
    st.html(f"""
    <div class="meu-card-customizado">
        <div class="card-icone-espaco">📈</div>
        <div class="card-conteudo-texto">
            <div class="card-titulo">Lucro Bruto</div>
            <div class="card-valor">R$ {metricas['lucro']:,.2f}</div>
            <div class="card-delta">{metricas['margem']:.1f}% de margem</div>
        </div>
    </div>
    """)

with col4:
    st.html(f"""
    <div class="meu-card-customizado">
        <div class="card-icone-espaco">📅</div>
        <div class="card-conteudo-texto">
            <div class="card-titulo">Faturamento médio diário</div>
            <div class="card-valor">R$ {metricas['faturamento_medio_diario']:,.2f}</div>
            <div class="card-delta">Média diária no período</div>
        </div>
    </div>
    """)

st.markdown("---")

# Segunda linha - Gráficos de evolução temporal
st.subheader("Evolução Temporal")

if dados_agregados and len(dados_agregados['rotulos']) > 0:
    
    titulos = {
        "diario": "Diário",
        "semanal": "Semanal",
        "mensal": "Mensal"
    }
    granularidade_label = titulos.get(dados_agregados['granularidade'], dados_agregados['granularidade'])
    
    col21, col22 = st.columns(2)
    
    with col21:
        
        fig_itens = go.Figure()
        fig_itens.add_trace(go.Bar(
            x=dados_agregados['rotulos'],
            y=dados_agregados['quantidade_itens'],
            marker_color='#667eea',
            text=dados_agregados['quantidade_itens'],
            textposition='auto',
            name='Itens Vendidos'
        ))
        
        fig_itens.update_layout(
            title=f"Quantidade de Itens Vendidos ({granularidade_label})",
            xaxis_title="Período",
            yaxis_title="Quantidade de Itens",
            template="plotly_white",
            height=400,
            showlegend=False,
            hovermode='x unified'
        )
        
        fig_itens.update_xaxes(tickangle=45)
        st.plotly_chart(fig_itens, use_container_width=True)
        
        if dados_agregados['quantidade_itens']:
            media_itens = sum(dados_agregados['quantidade_itens']) / len(dados_agregados['quantidade_itens'])
            st.caption(f"📊 Média de itens por {dados_agregados['granularidade']}: {media_itens:.1f} itens")
    
    with col22:
    
        fig_faturamento = go.Figure()
        fig_faturamento.add_trace(go.Scatter(
            x=dados_agregados['rotulos'],
            y=dados_agregados['faturamento'],
            mode='lines+markers',
            line=dict(color='#10b981', width=3),
            marker=dict(size=8, color='#059669'),
            name='Faturamento',
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        
        fig_faturamento.update_layout(
            title=f"Faturamento Total ({granularidade_label})",
            xaxis_title="Período",
            yaxis_title="Faturamento (R$)",
            template="plotly_white",
            height=400,
            hovermode='x unified'
        )
        
        fig_faturamento.update_xaxes(tickangle=45)
        fig_faturamento.update_yaxes(tickprefix="R$ ", tickformat=',.2f')
        
        st.plotly_chart(fig_faturamento, use_container_width=True)
        
        if dados_agregados['faturamento']:
            media_faturamento = sum(dados_agregados['faturamento']) / len(dados_agregados['faturamento'])
            st.caption(f"📊 Média de faturamento por {dados_agregados['granularidade']}: R$ {media_faturamento:,.2f}")

st.markdown("---")

# Terceira linha - Top Produtos
st.markdown(f"###  Top Produtos Mais Vendidos")

if top_produtos and len(top_produtos['produtos']) > 0:
    # Gráfico de barras horizontal
    fig_top_produtos = go.Figure()
    
    # Adicionar barras horizontais
    fig_top_produtos.add_trace(go.Bar(
        y=top_produtos['produtos'],  # Eixo Y (vertical) - nomes dos produtos
        x=top_produtos['quantidades'],  # Eixo X (horizontal) - quantidades
        orientation='h',  # Horizontal
        marker=dict(
            color=top_produtos['cores'],
            line=dict(color='rgba(0,0,0,0.2)', width=1)
        ),
        text=top_produtos['quantidades'],
        textposition='outside',
        name='Quantidade Vendida',
        hovertemplate='<b>%{y}</b><br>' +
                        'Quantidade: %{x} unidades<br>' +
                        'Faturamento: R$ %{customdata:,.2f}<extra></extra>',
        customdata=top_produtos['faturamentos']
    ))
    
    # Atualizar layout
    fig_top_produtos.update_layout(
        title={
            'text': f"Top {len(top_produtos['produtos'])} Produtos Mais Vendidos",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Quantidade Vendida (unidades)",
        yaxis_title="Produto",
        template="plotly_white",
        height=500,
        showlegend=False,
        hovermode='y unified',
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    # Ajustar layout do eixo Y para mostrar nomes completos
    fig_top_produtos.update_yaxes(
        automargin=True,
        tickfont=dict(size=11)
    )
    
    # Ajustar layout do eixo X
    fig_top_produtos.update_xaxes(
        gridcolor='#e5e7eb',
        gridwidth=1,
        showgrid=True
    )
    
    st.plotly_chart(fig_top_produtos, use_container_width=True)
    
else:
    st.warning("⚠️ Não há dados de produtos para o período selecionado.")


        
 
# Rodapé
st.markdown("---")
st.caption(f"📊 Dados atualizados com base no período: {periodo} | Ranking baseado na quantidade de unidades vendidas")