from altair.datasets import data
import pandas as pd
import json
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Union


# Faturamento Total
with open('dados/sales.json') as f:
    sales_data = json.load(f)

with open('dados/recipes.json') as f:
    recipe_data = json.load(f)

with open('dados/products.json') as f:
    products_data = json.load(f)

with open('dados/ingredients.json') as f:
    ingredients_data = json.load(f)


def analisar_periodo_completo(
    sales_data: dict,
    recipe_data: dict,
    products_data: dict,
    periodo: str = "diario",
    data_referencia: Optional[Union[str, datetime]] = None,
    incluir_detalhes_produtos: bool = False
) -> Dict:
    """
    Função unificada que calcula todas as métricas de um período
    
    Args:
        sales_data: dados do sales.json
        recipe_data: dados do recipe.json
        products_data: dados do products.json
        periodo: "diario", "semanal", "mensal", "trimestral", "semestral" ou"anual"
        data_referencia: data de referência (opcional, usa data atual)
        incluir_detalhes_produtos: se True, inclui análise por produto
    
    Returns:
        dict com todas as métricas do período
    """
    
    # ==========================================
    # 1. Preparação e validação dos dados
    # ==========================================
    
    # Definir data de referência
    if data_referencia is None:
        data_ref = datetime.now()
    elif isinstance(data_referencia, str):
        data_ref = datetime.fromisoformat(data_referencia.replace('Z', '+00:00'))
    else:
        data_ref = data_referencia
    
    # Remover timezone para comparação
    if data_ref.tzinfo is not None:
        data_ref = data_ref.replace(tzinfo=None)
    
    # Filtrar apenas vendas confirmadas
    vendas = [v for v in sales_data["data"] if v["status"] == "confirmed"]
    
    # ==========================================
    # 2. Calcular custos dos produtos
    # ==========================================
    
    precos_ingredientes = {
        "INS-ARROZ": 5.50, "INS-FEIJAO": 6.80, "INS-FRANGO": 12.90,
        "INS-CARNE": 18.50, "INS-SALADA": 4.50, "INS-MACARRAO": 4.20,
        "INS-MOLHO": 3.80, "INS-LEGUMES": 5.20, "INS-LOMBO": 22.90
    }
    
    custos_produtos = {}
    
    for recipe in recipe_data["data"]:
        product_id = recipe["product"]["id"]
        custo_total = 0.0
        
        for item in recipe["recipe_items"]:
            ingredient_code = item["ingredient"]["code"]
            quantidade = float(item["quantity"])
            preco_kg = precos_ingredientes.get(ingredient_code, 0)
            custo_total += quantidade * preco_kg
        
        preco_venda = next((float(p["sale_price"]) for p in products_data["data"] 
                           if p["id"] == product_id), 0)
        
        custo_operacional = custo_total * 0.15
        custo_total_com_op = custo_total + custo_operacional
        
        custos_produtos[product_id] = {
            'custo_total': round(custo_total_com_op, 2),
            'preco_venda': preco_venda,
            'lucro_unitario': round(preco_venda - custo_total_com_op, 2),
            'margem': round(((preco_venda - custo_total_com_op) / preco_venda * 100), 1) if preco_venda > 0 else 0,
            'nome_produto': recipe["product"]["name"]
        }
    
    # ==========================================
    # 3. Filtrar vendas pelo período
    # ==========================================
    
    vendas_periodo = []
    
    for venda in vendas:
        data_venda = datetime.fromisoformat(venda["sold_at"].replace('Z', '+00:00'))
        if data_venda.tzinfo is not None:
            data_venda = data_venda.replace(tzinfo=None)
        
        if _mesmo_periodo_unificado(data_venda, data_ref, periodo):
            vendas_periodo.append(venda)
    
    # ==========================================
    # 4. Calcular métricas consolidadas
    # ==========================================
    
    # Métricas gerais
    receita_total = sum(float(v["total_amount"]) for v in vendas_periodo)
    quantidade_vendas = len(vendas_periodo)
    
    # Calcular custo total
    custo_total = 0.0
    quantidade_itens = 0
    produtos_vendidos = defaultdict(lambda: {
        "quantidade": 0,
        "receita": 0.0,
        "custo": 0.0
    })
    
    for venda in vendas_periodo:
        for item in venda["sale_items"]:
            product_id = item["product"]["id"]
            product_name = item["product"]["name"]
            quantidade = item["quantity"]
            receita_item = float(item["total_price"])
            
            custo_unitario = custos_produtos.get(product_id, {}).get('custo_total', 0)
            custo_item = custo_unitario * quantidade
            
            custo_total += custo_item
            quantidade_itens += quantidade
            
            produtos_vendidos[product_id]["nome"] = product_name
            produtos_vendidos[product_id]["quantidade"] += quantidade
            produtos_vendidos[product_id]["receita"] += receita_item
            produtos_vendidos[product_id]["custo"] += custo_item
    
    lucro_total = receita_total - custo_total
    margem_total = (lucro_total / receita_total * 100) if receita_total > 0 else 0
    ticket_medio = receita_total / quantidade_vendas if quantidade_vendas > 0 else 0
    
    # ==========================================
    # 5. Calcular média diária para projeções
    # ==========================================
    
    dias_no_periodo = _calcular_dias_no_periodo(data_ref, periodo)
    media_diaria_receita = receita_total / dias_no_periodo if dias_no_periodo > 0 else 0
    media_diaria_vendas = quantidade_vendas / dias_no_periodo if dias_no_periodo > 0 else 0
    
    # ==========================================
    # 6. Montar resultado
    # ==========================================
    
    resultado = {
        "periodo": {
            "tipo": periodo,
            "referencia": data_ref.strftime("%Y-%m-%d"),
            "dias_analisados": dias_no_periodo
        },
        "resumo": {
            "receita_total": round(receita_total, 2),
            "custo_total": round(custo_total, 2),
            "lucro_total": round(lucro_total, 2),
            "margem_percentual": round(margem_total, 2),
            "quantidade_vendas": quantidade_vendas,
            "quantidade_itens_vendidos": quantidade_itens,
            "ticket_medio": round(ticket_medio, 2)
        },
        "medias_diarias": {
            "receita_media_diaria": round(media_diaria_receita, 2),
            "vendas_media_diaria": round(media_diaria_vendas, 2),
            "itens_media_diaria": round(quantidade_itens / dias_no_periodo, 2) if dias_no_periodo > 0 else 0
        }
    }
    
    # Incluir análise por produto se solicitado
    if incluir_detalhes_produtos:
        resultado["produtos"] = {}
        for product_id, dados in produtos_vendidos.items():
            lucro_produto = dados["receita"] - dados["custo"]
            margem_produto = (lucro_produto / dados["receita"] * 100) if dados["receita"] > 0 else 0
            
            resultado["produtos"][product_id] = {
                "nome": dados["nome"],
                "quantidade": dados["quantidade"],
                "receita": round(dados["receita"], 2),
                "custo": round(dados["custo"], 2),
                "lucro": round(lucro_produto, 2),
                "margem": round(margem_produto, 2),
                "participacao_receita": round(dados["receita"] / receita_total * 100, 1) if receita_total > 0 else 0
            }
    
    return resultado


def _mesmo_periodo_unificado(data_venda: datetime, data_ref: datetime, periodo: str) -> bool:
    """Verifica se duas datas estão no mesmo período"""
    
    if periodo == "diario":
        return data_venda.date() == data_ref.date()
    
    elif periodo == "semanal":
        return data_venda.isocalendar()[:2] == data_ref.isocalendar()[:2]
    
    elif periodo == "mensal":
        return (data_venda.year, data_venda.month) == (data_ref.year, data_ref.month)
    
    elif periodo == "trimestral":
        trim_venda = (data_venda.month - 1) // 3
        trim_ref = (data_ref.month - 1) // 3
        return data_venda.year == data_ref.year and trim_venda == trim_ref
    
    elif periodo == "semestral":
        return data_venda.year == data_ref.year and ((data_venda.month - 1) // 6) == ((data_ref.month - 1) // 6)

    elif periodo == "anual":
        return data_venda.year == data_ref.year
    
    return False


def _calcular_dias_no_periodo(data_ref: datetime, periodo: str) -> int:
    """Calcula quantos dias tem o período"""
    
    if periodo == "diario":
        return 1
    
    if periodo == "semestral":
        return 182  # Aproximação (6 meses * 30.4 dias)
    
    elif periodo == "semanal":
        return 7
    
    elif periodo == "mensal":
        # Dias no mês
        if data_ref.month == 2:
            # Fevereiro - considerar ano bissexto
            year = data_ref.year
            return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
        elif data_ref.month in [4, 6, 9, 11]:
            return 30
        else:
            return 31
    
    elif periodo == "trimestral":
        return 90  # Aproximação
    
    elif periodo == "anual":
        year = data_ref.year
        return 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365
    
    return 30  # default


def get_metricas_periodo(
    sales_data: dict,
    recipe_data: dict, 
    products_data: dict,
    periodo: str = "mensal"
) -> Tuple[float, float, float, int, float]:
    """
    Retorna as principais métricas de forma simples
    
    Returns:
        tuple: (receita, custo, lucro, quantidade_vendas, margem_percentual)
    """
    
    analise = analisar_periodo_completo(sales_data, recipe_data, products_data, periodo)
    
    return ({'receita':analise['resumo']['receita_total'],
        'custo': analise['resumo']['custo_total'],
        'lucro': analise['resumo']['lucro_total'],
        'qtd': analise['resumo']['quantidade_vendas'],
        'margem': analise['resumo']['margem_percentual']}
    )

import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple

def gerar_tabela_estoque(
    ingredients_data: dict,
    sales_data: dict,
    recipe_data: dict,
    dias_media: int = 30
) -> List[dict]:
    """
    Gera tabela de status de estoque com previsão de dias restantes.
    
    Args:
        ingredients_data: dados do ingredients.json
        sales_data: dados do sales.json
        recipe_data: dados do recipe.json
        dias_media: número de dias para calcular a média de consumo
    
    Returns:
        Lista de dicionários ordenada conforme prioridades:
        - crítico primeiro
        - validade mais próxima
        - menos dias restantes
    """
    
    # 1- Consumo médio diário por ingrediente
    
    consumo_por_produto = {} 

    for recipe in recipe_data["data"]:
        product_id = recipe["product"]["id"]
        ingredientes = {}
        for item in recipe["recipe_items"]:
            ing_id = item["ingredient"]["id"]
            quantidade = float(item["quantity"])  # kg por unidade do produto
            ingredientes[ing_id] = quantidade
        consumo_por_produto[product_id] = ingredientes
    
    # Agrupar vendas dos últimos 'dias_media' dias
    vendas = [v for v in sales_data["data"] if v["status"] == "confirmed"]
    
    data_limite = datetime.now() - timedelta(days=dias_media)
    
    # Remover timezone para comparação
    if data_limite.tzinfo:
        data_limite = data_limite.replace(tzinfo=None)
    
    # dicionario para acumular consumo total por ingrediente no período
    consumo_total_ingrediente = defaultdict(float)
    
    for venda in vendas:
        # converter data da venda
        data_str = venda["sold_at"]
        if 'Z' in data_str:
            data_str = data_str.replace('Z', '+00:00')
        data_venda = datetime.fromisoformat(data_str)
        if data_venda.tzinfo:
            data_venda = data_venda.replace(tzinfo=None)
        
        if data_venda >= data_limite:
            for item in venda["sale_items"]:
                product_id = item["product"]["id"]
                quantidade_vendida = item["quantity"]
                # Para cada ingrediente do produto, adiciona ao consumo
                ingredientes_produto = consumo_por_produto.get(product_id, {})
                for ing_id, qtd_por_unidade in ingredientes_produto.items():
                    consumo_total_ingrediente[ing_id] += qtd_por_unidade * quantidade_vendida
    
    # consumo total / dias_media
    media_consumo_diario = {
        ing_id: total / dias_media for ing_id, total in consumo_total_ingrediente.items()
    }
    
    # 2- tabela com dados dos ingredientes
    
    tabela = []
    hoje = datetime.now().date()
    
    for ingrediente in ingredients_data["data"]:
        code = ingrediente["code"]
        current_stock = float(ingrediente["current_stock"])
        minimum_stock = float(ingrediente["minimum_stock"])
        expiration_date = datetime.fromisoformat(ingrediente["expiration_date"]).date()
        
        # Status crítico
        if current_stock < minimum_stock:
            status = "crítico"
        elif current_stock < 2*minimum_stock:
            status = "atenção"
        else:
            status = "ok"

        # Dias restantes de estoque (considerando média de consumo)
        ing_id = ingrediente["id"]
        media_diaria = media_consumo_diario.get(ing_id, 0.0)
        
        if media_diaria > 0:
            dias_restantes = current_stock / media_diaria
        else:
            dias_restantes = float('inf')  # Sem consumo, dura indefinidamente
        
        dias_para_vencer = (expiration_date - hoje).days
        
        tabela.append({
            "code": code,
            "validade": expiration_date,
            "dias_para_vencer": dias_para_vencer,
            "estoque_atual": current_stock,
            "estoque_minimo": minimum_stock,
            "status": status,
            "dias_restantes_estoque": dias_restantes,
            "media_consumo_diario": media_diaria
        })
    
    tabela_ordenada = sorted(
        tabela,
        key=lambda x: (
            0 if x["status"] == "crítico" else 1,  # críticos primeiro
            x["dias_para_vencer"],                 # mais próximo primeiro
            x["dias_restantes_estoque"]            # menor dias restantes
        )
    )
    
    return tabela_ordenada

def calcular_dias_estoque_restante(
    sales_data: dict,
    product_id: int,
    estoque_atual: float,
    periodo_media: int = 30  # dias para calcular a média
) -> dict:
    """
    Calcula quantos dias o estoque atual vai durar baseado na média de vendas
    
    Args:
        sales_data: dados de vendas
        product_id: ID do produto
        estoque_atual: quantidade atual em estoque (kg, unidades, etc)
        periodo_media: número de dias para calcular a média de vendas
    
    Returns:
        dict com análise completa
    """
    
    # Filtrar vendas confirmadas
    vendas = [v for v in sales_data["data"] if v["status"] == "confirmed"]
    
    # Coletar vendas do produto específico nos últimos 'periodo_media' dias
    data_limite = datetime.now() - timedelta(days=periodo_media)
    vendas_produto = []
    
    for venda in vendas:
        data_venda = datetime.fromisoformat(venda["sold_at"].replace('Z', '+00:00'))
        data_limite = datetime.now(timezone.utc) - timedelta(days=30)

        if data_venda >= data_limite:
            for item in venda["sale_items"]:
                if item["product"]["id"] == product_id:
                    vendas_produto.append({
                        "data": data_venda,
                        "quantidade": item["quantity"],
                        "venda_id": venda["id"]
                    })
    
    if not vendas_produto:
        return {
            "product_id": product_id,
            "estoque_atual": estoque_atual,
            "media_diaria": 0,
            "dias_restantes": float('inf'),
            "status": "SEM_VENDAS_NO_PERIODO",
            "recomendacao": "Produto sem vendas recentes. Verificar se está ativo."
        }
    
    # Calcular média diária de vendas
    # Agrupar por dia
    vendas_por_dia = defaultdict(float)
    for venda in vendas_produto:
        dia = venda["data"].date()
        vendas_por_dia[dia] += venda["quantidade"]
    
    # Média diária
    dias_com_venda = len(vendas_por_dia)
    total_vendido = sum(vendas_por_dia.values())
    if periodo_media > 0:
        media_diaria = total_vendido / periodo_media
    else:
        media_diaria = 0
   
    # Calcular dias restantes
    if media_diaria > 0:
        dias_restantes = estoque_atual / media_diaria
    else:
        dias_restantes = float('inf')
    
    # Classificar situação do estoque
    if dias_restantes <= 3:
        status = "CRITICO"
        recomendacao = "Estoque muito baixo! Repor URGENTEMENTE."
    elif dias_restantes <= 7:
        status = "ATENCAO"
        recomendacao = "Estoque está acabando. Planejar reposição."
    elif dias_restantes <= 15:
        status = "OK"
        recomendacao = "Estoque adequado. Monitorar vendas."
    else:
        status = "CONFORTAVEL"
        recomendacao = "Estoque confortável. Sem risco de ruptura."
    
    return {
        "product_id": product_id,
        "estoque_atual": round(estoque_atual, 2),
        "media_diaria": round(media_diaria, 2),
        "total_vendido_periodo": round(total_vendido, 2),
        "dias_analisados": periodo_media,
        "dias_restantes": round(dias_restantes, 1),
        "status": status,
        "recomendacao": recomendacao,
        "data_previsao_esgotamento": (datetime.now() + timedelta(days=dias_restantes)).strftime("%Y-%m-%d") if dias_restantes != float('inf') else "N/A"
    }

import pandas as pd
import json
from collections import defaultdict

def analise_abc_por_lucro(sales_data, recipe_data, products_data, ingredients_data,
                          limite_a=0.75, limite_b=0.95):
    """
    Análise ABC dos produtos baseada no LUCRO BRUTO total.
    
    Args:
        sales_data: vendas (sales.json)
        recipe_data: receitas (recipe.json) -> composição de ingredientes
        products_data: produtos (products.json) -> preço de venda
        ingredients_data: ingredientes (ingredients.json) -> preço de compra (custo)
        limite_a: percentual acumulado para classe A
        limite_b: percentual acumulado para classe B
    
    Returns:
        DataFrame com produtos, receita, custo, lucro, percentuais e classe ABC
    """
    
    # ------------------------------
    # 1. Calcular custo unitário de cada produto (com base na receita e preço dos ingredientes)
    # ------------------------------
    # Mapa ingredient_id -> preço de compra por kg
    preco_ingrediente = {}
    for ing in ingredients_data["data"]:
        preco_ingrediente[ing["id"]] = float(ing["purchase_price"])
    
    # Mapa product_id -> custo total por unidade
    custo_unitario_produto = {}
    for recipe in recipe_data["data"]:
        prod_id = recipe["product"]["id"]
        custo_total = 0.0
        for item in recipe["recipe_items"]:
            ing_id = item["ingredient"]["id"]
            qtd = float(item["quantity"])  # kg por unidade do produto
            custo_total += qtd * preco_ingrediente.get(ing_id, 0)
        # Adicionar custos operacionais (opcional, ex.: 15%)
        custo_operacional = custo_total * 0.15
        custo_unitario_produto[prod_id] = custo_total + custo_operacional
    
    # ------------------------------
    # 2. Mapear preço de venda por produto
    # ------------------------------
    preco_venda_produto = {}
    for prod in products_data["data"]:
        preco_venda_produto[prod["id"]] = float(prod["sale_price"])
    
    # ------------------------------
    # 3. Calcular lucro bruto total por produto a partir das vendas
    # ------------------------------
    vendas = [v for v in sales_data["data"] if v["status"] == "confirmed"]
    
    lucro_por_produto = defaultdict(float)
    receita_por_produto = defaultdict(float)
    nome_por_produto = {}
    
    for venda in vendas:
        for item in venda["sale_items"]:
            prod_id = item["product"]["id"]
            nome = item["product"]["name"]
            quantidade = item["quantity"]
            preco_unitario_venda = float(item["unit_price"])
            
            receita_item = preco_unitario_venda * quantidade
            custo_unitario = custo_unitario_produto.get(prod_id, 0)
            lucro_item = (preco_unitario_venda - custo_unitario) * quantidade
            
            receita_por_produto[prod_id] += receita_item
            lucro_por_produto[prod_id] += lucro_item
            nome_por_produto[prod_id] = nome
    
    # ------------------------------
    # 4. Construir DataFrame e classificar
    # ------------------------------
    df = pd.DataFrame([
        {
            "product_id": pid,
            "product_name": nome_por_produto[pid],
            "receita_total": receita_por_produto[pid],
            "lucro_total": lucro_por_produto[pid],
            "margem_percentual": (lucro_por_produto[pid] / receita_por_produto[pid] * 100) if receita_por_produto[pid] > 0 else 0
        }
        for pid in lucro_por_produto
    ])
    
    # Ordenar por lucro total decrescente (base da análise ABC)
    df = df.sort_values("lucro_total", ascending=False).reset_index(drop=True)
    
    # Calcular percentuais acumulados sobre o lucro total
    lucro_total_geral = df["lucro_total"].sum()
    df["percentual_lucro"] = df["lucro_total"] / lucro_total_geral * 100
    df["lucro_acumulado"] = df["lucro_total"].cumsum()
    df["percentual_acumulado"] = df["lucro_acumulado"] / lucro_total_geral * 100
    
    # Classificação A, B, C com base no lucro acumulado
    df["classe"] = "C"
    df.loc[df["percentual_acumulado"] <= limite_a * 100, "classe"] = "A"
    df.loc[(df["percentual_acumulado"] > limite_a * 100) & (df["percentual_acumulado"] <= limite_b * 100), "classe"] = "B"
    
    # Arredondamentos
    df["receita_total"] = df["receita_total"].round(2)
    df["lucro_total"] = df["lucro_total"].round(2)
    df["margem_percentual"] = df["margem_percentual"].round(1)
    df["percentual_lucro"] = df["percentual_lucro"].round(2)
    df["percentual_acumulado"] = df["percentual_acumulado"].round(2)
    tabela = df[["classe", "product_name", "receita_total", "lucro_total", "margem_percentual", "percentual_lucro", "percentual_acumulado"]].to_string(index=False)

    return tabela


def exibir_analise_abc_lucro(df_abc):
    """Exibe resumo e tabela da análise ABC por lucro."""
    print("\n" + "="*80)
    print("📊 ANÁLISE ABC POR LUCRO BRUTO (Curva de Pareto)")
    print("="*80)
    
    # Resumo por classe
    resumo = df_abc.groupby("classe").agg(
        quantidade=("product_id", "count"),
        lucro_total=("lucro_total", "sum"),
        percentual_lucro=("percentual_lucro", "sum")
    ).round(2)
    
    print("\n Resumo por classe (lucro):")
    print(resumo.to_string())
    
    print("\n📋 Tabela completa (ordenada por lucro decrescente):")
    print(df_abc[["classe", "product_name", "receita_total", "lucro_total", "margem_percentual", "percentual_lucro", "percentual_acumulado"]].to_string(index=False))
    
    print("\n" + "="*80)

# Testes

receita, custo, lucro, qtd_vendas, margem = get_metricas_periodo(
    sales_data, recipe_data, products_data, "mensal"
)

# Vendas do anual
analise_anual= get_metricas_periodo(sales_data, recipe_data, products_data, "anual")
analise_semestral= get_metricas_periodo(sales_data, recipe_data, products_data, "semestral")
analise_mensal= get_metricas_periodo(sales_data, recipe_data, products_data, "mensal")
analise_semanal= get_metricas_periodo(sales_data, recipe_data, products_data, "semanal")
analise_hoje= get_metricas_periodo(sales_data, recipe_data, products_data, "diario")

receita_anual= analise_anual['receita']
receita_semestral= analise_semestral['receita']
receita_mensal= analise_mensal['receita']
receita_semanal= analise_semanal['receita']
receita_hoje= analise_hoje['receita']

## Total de vendas realizadas em um período específico.
qtd_vendas_anual= analise_anual['qtd']
qtd_vendas_semestral= analise_semestral['qtd']
qtd_vendas_mensal= analise_mensal['qtd']
qtd_vendas_semanal= analise_semanal['qtd']
qtd_vendas_hoje= analise_hoje['qtd']

# Ticket médio
if qtd_vendas_anual > 0:
    ticket_medio_anual= receita_anual / qtd_vendas_anual
else:       
    ticket_medio_anual= 0

# Lucro Bruto
lucro_bruto_anual= analise_anual['lucro']

## Porcentagem de margem de lucro bruto em relação ao faturamento total.
margem_mensal = analise_mensal['margem']

# Receita média diária
receita_anual/365
receita_semestral/182 #R$ média com relação ao ano
receita_mensal/30
receita_semanal/7 #R$ média com relação ao ano

# Vendas médias diárias
qtd_vendas_anual/365 #qtd média com relação ao ano
qtd_vendas_semestral/182 #qtd média com relação ao ano 
qtd_vendas_mensal/30 #qtd média com relação ao mês
qtd_vendas_semanal/7 #qtd média com relação à semana

# Ticket médio 
if receita_anual > 0:
    ticket_medio_anual= receita_anual / qtd_vendas_anual
else:
    ticket_medio_anual= 0

# Receita diária média
if receita_anual > 0:
    receita_diaria_media= receita_anual/365
else:
    receita_diaria_media= 0

# Dias restantes para esgotar o estoque de um produto específico (Com base na quantidade atual em estoque e na média de vendas diárias.)

tabela = gerar_tabela_estoque(ingredients_data, sales_data, recipe_data, dias_media=30)

# Converter para DataFrame para visualização
df = pd.DataFrame(tabela)
filtrado = df.loc[(df['dias_para_vencer'] < 7) | (df['status'] != 'ok'), 
                  ['code', 'validade', 'dias_para_vencer', 'estoque_atual', 'status', 'dias_restantes_estoque']]
print(f'Code: {filtrado.iloc[0,0]} - Dias para vencer: {filtrado.iloc[0,2]}')

# ## Quantidade atual em estoque
# calcular_dias_estoque_restante(sales_data, produto_id, estoque_atual, dias_para_media)['estoque_atual']


# ## Status do estoque (Crítico, Atenção, OK)
# calcular_dias_estoque_restante(sales_data, produto_id, estoque_atual, dias_para_media)['status']

# ## Data prevista para esgotamento do estoque
filtrado_vencimento = df.loc[(df['dias_para_vencer'] < 7), ['code', 'validade', 'dias_para_vencer', 'estoque_atual']]
print(filtrado_vencimento)
# calcular_dias_estoque_restante(sales_data, produto_id, estoque_atual, dias_para_media)['data_previsao_esgotamento']
filtrado_duracao_estoque = df.loc[(df['status'] != 'ok'),
                  ['code', 'dias_para_vencer', 'estoque_atual', 'dias_restantes_estoque', 'status']]
print(filtrado_duracao_estoque)
# Previsão de vendas para o próximo mês com base em tendências anteriores (fazer para os próximos 3 meses).

# Análise ABC dos produtos (Classificação dos produtos com base em sua contribuição para o faturamento total, onde A representa os produtos mais lucrativos, B os intermediários e C os menos lucrativos.) 
df_abc_lucro = analise_abc_por_lucro(sales_data, recipe_data, products_data, ingredients_data)
print(df_abc_lucro)

# exibir_analise_abc_lucro(df_abc_lucro)