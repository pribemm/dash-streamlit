import requests

base_url = "https://apisgm.jemison.dev.br"

# LOGIN
login_url = f"{base_url}/api/v1/auth/login"

dados_login = {
    "user": {
        "email": "manager@example.com",
        "password": "password123"
    }
}


res_login = requests.post(login_url, json=dados_login)

print("LOGIN STATUS:", res_login.status_code)

data = res_login.json()

# 👇 pega o token certo
token = data["data"]["token"]

# 👇 headers com autenticação
headers = {
    "Authorization": f"Bearer {token}"
}


categories_url = f"{base_url}/api/v1/categories"
res_categories = requests.get(categories_url, headers=headers)

with open("categories.json", "w") as f:
    f.write(res.text)

# Suppliers
suppliers_url = f"{base_url}/api/v1/suppliers"
res_suppliers = requests.get(suppliers_url, headers=headers)

with open("suppliers.json", "w") as f:
    f.write(res_suppliers.text)


# Ingredients
ingredients_url = f"{base_url}/api/v1/ingredients"
res_ingredients = requests.get(ingredients_url, headers=headers)

with open("ingredients.json", "w") as f:
    f.write(res_ingredients.text)


# Stock Movements
stock_movements_url = f"{base_url}/api/v1/stock_movements"
res_stock_movements = requests.get(stock_movements_url, headers=headers)

with open("stock_movements.json", "w") as f:
    f.write(res_stock_movements.text)

# Products
products_url = f"{base_url}/api/v1/products"
res_products = requests.get(products_url, headers=headers)

with open("products.json", "w") as f:
    f.write(res_products.text)

# Recipes
recipes_url = f"{base_url}/api/v1/recipes"
res_recipes = requests.get(recipes_url, headers=headers)

with open("recipes.json", "w") as f:
    f.write(res_recipes.text)

# Menus
menus_url = f"{base_url}/api/v1/menus"
res_menus = requests.get(menus_url, headers=headers)

with open("menus.json", "w") as f:
    f.write(res_menus.text)

# Cash Sessions
cash_sessions_url = f"{base_url}/api/v1/cash_sessions"
res_cash_sessions = requests.get(cash_sessions_url, headers=headers)

with open("cash_sessions.json", "w") as f:
    f.write(res_cash_sessions.text)

# Sales
sales_url = f"{base_url}/api/v1/sales"
res_sales = requests.get(sales_url, headers=headers)    

with open("sales.json", "w") as f:
    f.write(res_sales.text) 

# Financial Entries
financial_entries_url = f"{base_url}/api/v1/financial_entries"
res_financial_entries = requests.get(financial_entries_url, headers=headers)

with open("financial_entries.json", "w") as f:
    f.write(res_financial_entries.text)
