#!/usr/bin/env python3
"""
Script para diagnosticar problemas de banco de dados
Execute: python db_diagnostic.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_transaction_issue():
    """Testa se há problema de transação entre requisições"""
    
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE TRANSAÇÃO DO BANCO DE DADOS")
    print("=" * 80)
    
    # 1. Cria um usuário
    print("\n1️⃣ Criando usuário...")
    user_data = {
        "name": "Transaction Test User",
        "email": f"txtest_{datetime.now().timestamp()}@example.com",
        "phone": "+5511999999999",
        "birth_date": "1990-01-01",
        "address": "Test Address"
    }
    
    r = requests.post(f"{BASE_URL}/api/users/", json=user_data)
    if r.status_code != 201:
        print(f"❌ Falha ao criar usuário: {r.status_code}")
        print(f"   Resposta: {r.text}")
        return
    
    user = r.json()
    user_id = user["id"]
    print(f"✅ Usuário criado: {user_id}")
    print(f"   Dados: {json.dumps(user, indent=2)}")
    
    # 2. Imediatamente tenta buscar o usuário
    print(f"\n2️⃣ Buscando usuário recém-criado...")
    r = requests.get(f"{BASE_URL}/api/users/{user_id}")
    if r.status_code != 200:
        print(f"❌ Usuário não encontrado: {r.status_code}")
        print(f"   Resposta: {r.text}")
        return
    print(f"✅ Usuário encontrado na busca direta")
    
    # 3. Lista todos os usuários
    print(f"\n3️⃣ Listando todos os usuários...")
    r = requests.get(f"{BASE_URL}/api/users/")
    if r.status_code != 200:
        print(f"❌ Falha ao listar usuários: {r.status_code}")
        return
    
    users = r.json()
    user_ids = [u["id"] for u in users]
    if user_id in user_ids:
        print(f"✅ Usuário encontrado na listagem ({len(users)} usuários no total)")
    else:
        print(f"❌ Usuário NÃO encontrado na listagem!")
        print(f"   Total de usuários: {len(users)}")
        print(f"   IDs disponíveis: {user_ids[:5]}...")
    
    # 4. Cria uma categoria
    print(f"\n4️⃣ Criando categoria...")
    cat_data = {"name": f"TxTest Cat {datetime.now().timestamp()}", "description": "Test"}
    r = requests.post(f"{BASE_URL}/api/products/categories", json=cat_data)
    if r.status_code != 201:
        print(f"❌ Falha ao criar categoria: {r.status_code}")
        print(f"   Resposta: {r.text}")
        return
    
    category = r.json()
    category_id = category["id"]
    print(f"✅ Categoria criada: {category_id}")
    print(f"   Dados: {json.dumps(category, indent=2)}")
    
    # 5. Imediatamente busca a categoria
    print(f"\n5️⃣ Buscando categoria recém-criada...")
    r = requests.get(f"{BASE_URL}/api/products/categories/{category_id}")
    if r.status_code != 200:
        print(f"❌ Categoria não encontrada: {r.status_code}")
        print(f"   Resposta: {r.text}")
    else:
        print(f"✅ Categoria encontrada na busca direta")
    
    # 6. Lista todas as categorias
    print(f"\n6️⃣ Listando todas as categorias...")
    r = requests.get(f"{BASE_URL}/api/products/categories")
    if r.status_code != 200:
        print(f"❌ Falha ao listar categorias: {r.status_code}")
        return
    
    categories = r.json()
    category_ids = [c["id"] for c in categories]
    if category_id in category_ids:
        print(f"✅ Categoria encontrada na listagem ({len(categories)} categorias no total)")
    else:
        print(f"❌ Categoria NÃO encontrada na listagem!")
        print(f"   Total de categorias: {len(categories)}")
        print(f"   IDs disponíveis: {category_ids}")
    
    # 7. Tenta criar produto com a categoria
    print(f"\n7️⃣ Tentando criar produto com category_id={category_id}...")
    product_data = {
        "name": "Transaction Test Product",
        "description": "Test product",
        "price": 99.99,
        "stock": 100,
        "category_id": category_id
    }
    
    r = requests.post(f"{BASE_URL}/api/products/", json=product_data)
    if r.status_code != 201:
        print(f"❌ Falha ao criar produto: {r.status_code}")
        print(f"   Resposta: {r.text}")
        
        # Debug adicional
        print(f"\n🔍 Debug adicional:")
        print(f"   category_id enviado: {category_id}")
        print(f"   Tipo: {type(category_id)}")
        
        # Tenta buscar a categoria novamente
        print(f"\n   Tentando buscar categoria novamente...")
        r2 = requests.get(f"{BASE_URL}/api/products/categories/{category_id}")
        print(f"   Status: {r2.status_code}")
        if r2.status_code == 200:
            print(f"   ✅ Categoria EXISTE no banco!")
            print(f"   Dados: {json.dumps(r2.json(), indent=2)}")
        else:
            print(f"   ❌ Categoria não encontrada!")
    else:
        product = r.json()
        print(f"✅ Produto criado com sucesso: {product['id']}")
        print(f"   Dados: {json.dumps(product, indent=2)}")
    
    # 8. Tenta criar método de pagamento
    print(f"\n8️⃣ Tentando criar método de pagamento com user_id={user_id}...")
    payment_method_data = {
        "user_id": user_id,
        "type": "credit_card",
        "name": "Test Card"
    }
    
    r = requests.post(f"{BASE_URL}/api/payments/methods", json=payment_method_data)
    if r.status_code != 201:
        print(f"❌ Falha ao criar método de pagamento: {r.status_code}")
        print(f"   Resposta: {r.text}")
        
        # Debug adicional
        print(f"\n🔍 Debug adicional:")
        print(f"   user_id enviado: {user_id}")
        print(f"   Tipo: {type(user_id)}")
        
        # Tenta buscar o usuário novamente
        print(f"\n   Tentando buscar usuário novamente...")
        r2 = requests.get(f"{BASE_URL}/api/users/{user_id}")
        print(f"   Status: {r2.status_code}")
        if r2.status_code == 200:
            print(f"   ✅ Usuário EXISTE no banco!")
            print(f"   Dados: {json.dumps(r2.json(), indent=2)}")
        else:
            print(f"   ❌ Usuário não encontrado!")
    else:
        payment_method = r.json()
        print(f"✅ Método de pagamento criado com sucesso: {payment_method['id']}")
        print(f"   Dados: {json.dumps(payment_method, indent=2)}")
    
    print("\n" + "=" * 80)
    print("📊 CONCLUSÃO")
    print("=" * 80)
    print("""
Se você vê erros de "not found" acima mesmo após confirmar que o registro
existe, o problema é com o isolamento de sessão do banco de dados.

Possíveis causas:
1. get_db() está criando sessões separadas que não veem os commits
2. Problema de autoflush/autocommit no SQLAlchemy
3. Transações não estão sendo finalizadas corretamente

Verifique o arquivo database.py e certifique-se de que está usando:
- autocommit=False
- autoflush=False
- expire_on_commit=False (recomendado)
    """)

if __name__ == "__main__":
    try:
        test_transaction_issue()
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor")
        print("💡 Certifique-se de que o FastAPI está rodando em http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()