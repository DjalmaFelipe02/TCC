#!/usr/bin/env python3
"""
Script de diagnóstico para verificar se a API está funcionando corretamente
Execute: python test_api.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_result(success, message):
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Testa um endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "PATCH":
            response = requests.patch(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, timeout=5)
        else:
            print_result(False, f"Método {method} não suportado")
            return None
        
        success = response.status_code == expected_status
        print_result(
            success,
            f"{method} {endpoint} -> Status {response.status_code} (esperado: {expected_status})"
        )
        
        if not success and response.text:
            try:
                error_detail = response.json()
                print(f"   Detalhes: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Resposta: {response.text[:200]}")
        
        return response if success else None
        
    except requests.exceptions.ConnectionError:
        print_result(False, f"Não foi possível conectar em {url}")
        print("   💡 Certifique-se de que o servidor FastAPI está rodando!")
        print("   💡 Execute: uvicorn main:app --reload")
        return None
    except requests.exceptions.Timeout:
        print_result(False, f"Timeout ao acessar {url}")
        return None
    except Exception as e:
        print_result(False, f"Erro: {str(e)}")
        return None

def main():
    print_header("🔍 DIAGNÓSTICO DA API E-COMMERCE")
    
    # Inicializa variáveis
    user_id = None
    category_id = None
    product_id = None
    order_id = None
    payment_method_id = None
    
    # 1. Verifica se o servidor está online
    print_header("1️⃣ Verificando conectividade")
    response = test_endpoint("GET", "/docs", expected_status=200)
    if not response:
        print("\n❌ A API não está acessível. Verifique se o servidor está rodando.")
        print("\n📝 Para iniciar o servidor, execute:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # 2. Testa CRUD de Usuários
    print_header("2️⃣ Testando CRUD de Usuários")
    
    # Listar usuários
    test_endpoint("GET", "/api/users/")
    
    # Criar usuário
    user_data = {
        "name": "Test User",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "phone": "+5511999999999",
        "birth_date": "1990-01-01",
        "address": "Test Address, 123"
    }
    response = test_endpoint("POST", "/api/users/", data=user_data, expected_status=201)
    if response:
        user_id = response.json()["id"]
        
        # Obter usuário
        test_endpoint("GET", f"/api/users/{user_id}")
        
        # Atualizar usuário
        test_endpoint("PATCH", f"/api/users/{user_id}", data={"name": "Updated User"})
    
    # 3. Testa CRUD de Categorias
    print_header("3️⃣ Testando CRUD de Categorias")
    
    test_endpoint("GET", "/api/products/categories")
    
    category_data = {"name": "Test Category", "description": "Test"}
    response = test_endpoint("POST", "/api/products/categories", data=category_data, expected_status=201)
    if response:
        category_data_response = response.json()
        category_id = category_data_response.get("id")
        print(f"   📌 Category ID criado: {category_id}")
        print(f"   📌 Resposta completa: {json.dumps(category_data_response, indent=2)}")
        
        # Verifica se a categoria realmente foi criada
        verify_response = test_endpoint("GET", f"/api/products/categories/{category_id}", expected_status=200)
        if verify_response:
            print(f"   ✅ Categoria verificada com sucesso!")
        else:
            print(f"   ❌ Categoria não encontrada após criação!")
    
    # 4. Testa CRUD de Produtos
    print_header("4️⃣ Testando CRUD de Produtos")
    
    test_endpoint("GET", "/api/products/")
    
    if category_id:
        product_data = {
            "name": "Test Product",
            "description": "Test product description",
            "price": 99.99,
            "stock": 100,
            "category_id": category_id
        }
        response = test_endpoint("POST", "/api/products/", data=product_data, expected_status=201)
        if response:
            product_id = response.json()["id"]
            test_endpoint("GET", f"/api/products/{product_id}")
    else:
        print("   ⚠️ Pulando teste de produtos (sem categoria)")
    
    # 5. Testa CRUD de Pedidos
    print_header("5️⃣ Testando CRUD de Pedidos")
    
    test_endpoint("GET", "/api/orders/")
    
    if user_id and product_id:
        order_data = {
            "user_id": user_id,
            "items": [{"product_id": product_id, "quantity": 2}],
            "address": "Order Address, 456"
        }
        response = test_endpoint("POST", "/api/orders/", data=order_data, expected_status=201)
        if response:
            order_id = response.json()["id"]
            test_endpoint("GET", f"/api/orders/{order_id}")
    else:
        print("   ⚠️ Pulando teste de pedidos (sem usuário ou produto)")
    
    # 6. Testa CRUD de Métodos de Pagamento
    print_header("6️⃣ Testando CRUD de Métodos de Pagamento")
    
    test_endpoint("GET", "/api/payments/methods")
    
    if user_id:
        payment_method_data = {
            "user_id": user_id,
            "type": "credit_card",
            "name": "Test Card"
        }
        response = test_endpoint("POST", "/api/payments/methods", data=payment_method_data, expected_status=201)
        if response:
            payment_method_id = response.json()["id"]
    else:
        print("   ⚠️ Pulando teste de métodos de pagamento (sem usuário)")
    
    # 7. Testa CRUD de Pagamentos
    print_header("7️⃣ Testando CRUD de Pagamentos")
    
    test_endpoint("GET", "/api/payments/")
    
    if order_id and payment_method_id:
        payment_data = {
            "order_id": order_id,
            "payment_method_id": payment_method_id,
            "amount": 199.98
        }
        response = test_endpoint("POST", "/api/payments/", data=payment_data, expected_status=201)
        if response:
            print("   ✅ Pagamento criado com sucesso!")
    else:
        print("   ⚠️ Pulando teste de pagamentos (sem pedido ou método de pagamento)")
    
    # Resumo
    print_header("📊 RESUMO")
    print("\n✅ Diagnóstico concluído!")
    
    issues = []
    if not category_id:
        issues.append("❌ Problema ao criar categoria")
    if not product_id:
        issues.append("❌ Problema ao criar produto")
    if not order_id:
        issues.append("❌ Problema ao criar pedido")
    if not payment_method_id:
        issues.append("❌ Problema ao criar método de pagamento")
    
    if issues:
        print("\n⚠️ Problemas encontrados:")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Verifique o arquivo main.py e as rotas registradas")
    else:
        print("\n✅ Todos os testes passaram! API funcionando perfeitamente!")
        print("\n✅ Agora você pode executar o Locust:")
        print("\n   locust -f locustfile.py --host=http://127.0.0.1:8000")
        print("\n   Acesse: http://localhost:8089")
        print("\n💡 Recomendações para o teste de carga:")
        print("   • Comece com 10-20 usuários")
        print("   • Taxa de spawn: 5 usuários/segundo")
        print("   • Aumente gradualmente conforme necessário")

if __name__ == "__main__":
    main()