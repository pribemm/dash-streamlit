import json as json_module
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter

# Configurar estilo dos gráficos
plt.style.use('seaborn-v0_8-darkgrid')

def format_currency(x, p):
    """Formata valores como moeda"""
    return f'R$ {x:,.0f}'.replace(',', '.')

def gerar_grafico_previsao(
    sales_data,
    meses_previstos=3,
    salvar_imagem=None,
    mostrar_grafico=True
):
    """
    Gera gráfico de previsão de vendas usando regressão linear
    
    Args:
        sales_data: dicionário com dados de vendas
        meses_previstos: número de meses para prever
        salvar_imagem: caminho para salvar (ex: "previsao.png")
        mostrar_grafico: se True, exibe o gráfico
    """
    
    # 1 Dados históricos
    
    # Filtrar vendas confirmadas
    vendas = [v for v in sales_data["data"] if v["status"] == "confirmed"]
    
    if not vendas:
        print("Nenhuma venda encontrada!")
        return None
    
    # Agrupar por mês
    vendas_por_mes = defaultdict(float)
    
    for venda in vendas:
        data_str = venda["sold_at"]
        # Converter string para datetime
        if 'Z' in data_str:
            data_str = data_str.replace('Z', '+00:00')
        data = datetime.fromisoformat(data_str)
        # Remover timezone
        if data.tzinfo is not None:
            data = data.replace(tzinfo=None)
        
        mes_key = data.strftime("%Y-%m")
        vendas_por_mes[mes_key] += float(venda["total_amount"])
    
    # Ordenar meses
    meses_ordenados = sorted(vendas_por_mes.keys())
    valores_historicos = [vendas_por_mes[mes] for mes in meses_ordenados]
    
    # Converter datas para objetos datetime
    datas_historicas = [datetime.strptime(mes, "%Y-%m") for mes in meses_ordenados]
   

    # 2 Regressão Linear    
    n = len(valores_historicos)
    
    # Se só tem 1 mês de dado, repetir o mesmo valor
    if n == 1:
        valores_previsao = [valores_historicos[0]] * meses_previstos
        datas_previsao = []
        ultima_data = datas_historicas[0]
        for i in range(1, meses_previstos + 1):
            data_previsao = ultima_data + timedelta(days=32 * i)
            datas_previsao.append(data_previsao)
        
        variacao_percentual = 0
        r_quadrado = 100
        
    else:
        # Cálculo da regressão linear
        x = list(range(n))
        y = valores_historicos
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        # Coeficientes
        b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        a = (sum_y - b * sum_x) / n
        
        # Calcular R²
        y_medio = sum_y / n
        ss_total = sum((y[i] - y_medio) ** 2 for i in range(n))
        ss_residual = sum((y[i] - (a + b * x[i])) ** 2 for i in range(n))
        r_quadrado = (1 - (ss_residual / ss_total)) * 100 if ss_total > 0 else 0
        
        # Preparar dados de previsão
        datas_previsao = []
        valores_previsao = []
        
        ultima_data = datas_historicas[-1]
        for i in range(1, meses_previstos + 1):
            data_previsao = ultima_data + timedelta(days=32 * i)
            datas_previsao.append(data_previsao)
            
            proximo_x = n + i - 1
            previsao = a + b * proximo_x
            valores_previsao.append(max(0, previsao))
        
        # Calcular variação percentual
        if valores_historicos[-1] > 0:
            variacao_percentual = ((valores_previsao[0] - valores_historicos[-1]) / valores_historicos[-1]) * 100
        else:
            variacao_percentual = 0
    
    #Geração do gráfico    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plotar dados históricos
    ax.plot(datas_historicas, valores_historicos, 
            marker='o', linewidth=2.5, markersize=8, 
            color='#2E86AB', label='Histórico Real', zorder=3)
    
    # Plotar previsão
    ax.plot(datas_previsao, valores_previsao, 
            marker='s', linewidth=2.5, markersize=8, 
            color='#F18F01', label='Previsão', zorder=3)
    
    # Conectar histórico com previsão (linha pontilhada)
    if len(datas_historicas) > 0 and len(datas_previsao) > 0:
        ax.plot([datas_historicas[-1], datas_previsao[0]], 
                [valores_historicos[-1], valores_previsao[0]], 
                ':', linewidth=2, color='gray', alpha=0.7, label='Projeção')
    
    # Destacar área de previsão
    if datas_previsao:
        ax.axvspan(datas_previsao[0], datas_previsao[-1], 
                   alpha=0.08, color='#F18F01')
    
    # Configurar gráfico
    titulo = f'Previsão de Vendas - Próximos {meses_previstos} Meses'
    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Período (Meses)', fontsize=12)
    ax.set_ylabel('Receita (R$)', fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Formatar eixo Y como moeda
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'.replace(',', '.')))
    
    # Formatar eixo X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Adicionar anotações com os valores
    for i, (data, valor) in enumerate(zip(datas_historicas[-3:], valores_historicos[-3:])):
        ax.annotate(f'R$ {valor:.0f}', 
                    xy=(data, valor), xytext=(5, 5),
                    textcoords='offset points', fontsize=9, alpha=0.7)
    
    for i, (data, valor) in enumerate(zip(datas_previsao, valores_previsao)):
        ax.annotate(f'R$ {valor:.0f}', 
                    xy=(data, valor), xytext=(5, -15),
                    textcoords='offset points', fontsize=10, fontweight='bold',
                    color='#F18F01')
    
    # Adicionar box com informações
    info_text = f"""
    Estatísticas da Previsão:
    • Variação: {'+' if variacao_percentual > 0 else ''}{variacao_percentual:.1f}%
    • Previsão Total: R$ {sum(valores_previsao):.0f}
    • Média Mensal: R$ {sum(valores_previsao)/len(valores_previsao):.0f}
    """
    
    ax.text(0.98, 0.02, info_text, transform=ax.transAxes,  # 0.02 = próximo ao fundo
        fontsize=9, verticalalignment='bottom',  # alinhar embaixo
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
        ha='right')
    
    # Destacar variação no gráfico
    cor_variacao = 'green' if variacao_percentual > 0 else 'red' if variacao_percentual < 0 else 'gray'
    sinal = '+' if variacao_percentual > 0 else ''
    ax.annotate(f'Variação: {sinal}{variacao_percentual:.1f}%', 
                xy=(0.98, 0.95), xycoords='axes fraction',
                fontsize=11, fontweight='bold', color=cor_variacao,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                ha='right')
    
    plt.tight_layout()
    
    # Salvar imagem
    if salvar_imagem:
        plt.savefig(salvar_imagem, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {salvar_imagem}")
    
    # Mostrar gráfico
    if mostrar_grafico:
        plt.show()
    
    return fig


def gerar_grafico_variacao(
    sales_data,
    meses_previstos=3,
    salvar_imagem=None,
    mostrar_grafico=True
):
    """
    Gera gráfico de variação percentual das vendas
    """
    
    # Preparar dados
    vendas = [v for v in sales_data["data"] if v["status"] == "confirmed"]
    
    if not vendas:
        print("Nenhuma venda encontrada!")
        return None
    
    # Agrupar por mês
    vendas_por_mes = defaultdict(float)
    
    for venda in vendas:
        data_str = venda["sold_at"]
        if 'Z' in data_str:
            data_str = data_str.replace('Z', '+00:00')
        data = datetime.fromisoformat(data_str)
        if data.tzinfo is not None:
            data = data.replace(tzinfo=None)
        
        mes_key = data.strftime("%Y-%m")
        vendas_por_mes[mes_key] += float(venda["total_amount"])
    
    meses_ordenados = sorted(vendas_por_mes.keys())
    valores_historicos = [vendas_por_mes[mes] for mes in meses_ordenados]
    datas_historicas = [datetime.strptime(mes, "%Y-%m") for mes in meses_ordenados]
    
    # Regressão linear
    n = len(valores_historicos)
    
    if n == 1:
        valores_previsao = [valores_historicos[0]] * meses_previstos
        datas_previsao = []
        ultima_data = datas_historicas[0]
        for i in range(1, meses_previstos + 1):
            datas_previsao.append(ultima_data + timedelta(days=32 * i))
    else:
        x = list(range(n))
        y = valores_historicos
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        a = (sum_y - b * sum_x) / n
        
        datas_previsao = []
        valores_previsao = []
        ultima_data = datas_historicas[-1]
        
        for i in range(1, meses_previstos + 1):
            datas_previsao.append(ultima_data + timedelta(days=32 * i))
            proximo_x = n + i - 1
            valores_previsao.append(max(0, a + b * proximo_x))
    
    # Calcular variações
    todos_valores = valores_historicos + valores_previsao
    todas_datas = datas_historicas + datas_previsao
    
    variacoes = []
    for i in range(1, len(todos_valores)):
        if todos_valores[i-1] > 0:
            variacao = ((todos_valores[i] - todos_valores[i-1]) / todos_valores[i-1]) * 100
        else:
            variacao = 0
        variacoes.append(variacao)
    
    # Separar variações
    variacoes_historicas = variacoes[:len(valores_historicos)-1]
    variacoes_previstas = variacoes[len(valores_historicos)-1:]
    datas_variacao_hist = todas_datas[1:len(valores_historicos)]
    datas_variacao_prev = todas_datas[len(valores_historicos):]
    
    # Criar gráfico
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Barras históricas
    cores_hist = ['#2E86AB' if v >= 0 else '#A23B72' for v in variacoes_historicas]
    ax.bar(datas_variacao_hist, variacoes_historicas, 
           color=cores_hist, alpha=0.7, label='Variação Real', width=25)
    
    # Barras previstas
    if variacoes_previstas:
        cores_prev = ['#F18F01' if v >= 0 else '#D32F2F' for v in variacoes_previstas]
        ax.bar(datas_variacao_prev, variacoes_previstas, 
               color=cores_prev, alpha=0.7, label='Variação Prevista', width=25)
    
    # Linha zero
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)
    
    # Configurar
    ax.set_title('Análise de Variação Mensal', fontsize=14, fontweight='bold')
    ax.set_xlabel('Período', fontsize=12)
    ax.set_ylabel('Variação Percentual (%)', fontsize=12)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Formatar eixo X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Adicionar valores nas barras
    for data, variacao in zip(datas_variacao_hist, variacoes_historicas):
        ax.text(data, variacao + (1 if variacao >= 0 else -3), 
                f'{variacao:.1f}%', ha='center', fontsize=9)
    
    for data, variacao in zip(datas_variacao_prev, variacoes_previstas):
        ax.text(data, variacao + (1 if variacao >= 0 else -3), 
                f'{variacao:.1f}%', ha='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    if salvar_imagem:
        plt.savefig(salvar_imagem, dpi=300, bbox_inches='tight')
        print(f"Gráfico de variação salvo em: {salvar_imagem}")
    
    if mostrar_grafico:
        plt.show()
    
    return fig


# Simulação de execução

with open('dados/sales.json') as f:
    sales_data = json_module.load(f)

with open('dados/recipes.json') as f:
    recipe_data = json_module.load(f)

with open('dados/products.json') as f:
    products_data = json_module.load(f)

print("Gerando gráfico de previsão...")
fig1 = gerar_grafico_previsao(
    sales_data, 
    meses_previstos=3,
    salvar_imagem="previsao_vendas.png",
    mostrar_grafico=True
)