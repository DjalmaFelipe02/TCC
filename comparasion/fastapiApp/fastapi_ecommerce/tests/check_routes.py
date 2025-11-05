#!/usr/bin/env python3
"""
Script para verificar todas as rotas registradas na API
Execute: python check_routes.py
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def check_routes():
    """Verifica as rotas disponíveis via OpenAPI"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code != 200:
            print("❌ Não foi possível acessar /openapi.json")
            return
        
        openapi = response.json()
        paths = openapi.get("paths", {})
        
        print("=" * 80)
        print("🔍 ROTAS REGISTRADAS NA API")
        print("=" * 80)
        
        # Organiza por tag
        routes_by_tag = {}
        
        for path, methods in sorted(paths.items()):
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    tags = details.get("tags", ["Untagged"])
                    tag = tags[0] if tags else "Untagged"
                    
                    if tag not in routes_by_tag:
                        routes_by_tag[tag] = []
                    
                    routes_by_tag[tag].append({
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", "")
                    })
        
        # Exibe rotas organizadas
        for tag, routes in sorted(routes_by_tag.items()):
            print(f"\n📂 {tag.upper()}")
            print("-" * 80)
            for route in routes:
                print(f"   {route['method']:7} {route['path']:50} {route['summary']}")
        
        print("\n" + "=" * 80)
        print(f"Total de rotas: {sum(len(routes) for routes in routes_by_tag.values())}")
        print("=" * 80)
        
        # Verifica rotas problemáticas
        print("\n🔍 VERIFICANDO ROTAS PROBLEMÁTICAS...")
        
        critical_routes = [
            ("GET", "/api/payments/methods", "Listar métodos de pagamento"),
            ("POST", "/api/payments/methods", "Criar método de pagamento"),
            ("POST", "/api/products/", "Criar produto"),
            ("POST", "/api/products/categories", "Criar categoria"),
        ]
        
        for method, path, description in critical_routes:
            exists = any(
                r["method"] == method and r["path"] == path 
                for routes in routes_by_tag.values() 
                for r in routes
            )
            status = "✅" if exists else "❌"
            print(f"{status} {method:7} {path:40} - {description}")
        
        # Testa algumas rotas críticas
        print("\n🧪 TESTANDO ROTAS CRÍTICAS...")
        
        test_routes = [
            ("GET", "/api/users/", 200),
            ("GET", "/api/products/", 200),
            ("GET", "/api/products/categories", 200),
            ("GET", "/api/orders/", 200),
            ("GET", "/api/payments/", 200),
            ("GET", "/api/payments/methods", 200),
        ]
        
        for method, path, expected in test_routes:
            try:
                r = requests.get(f"{BASE_URL}{path}", timeout=2)
                status = "✅" if r.status_code == expected else "❌"
                print(f"{status} {method} {path:40} -> {r.status_code} (esperado: {expected})")
            except Exception as e:
                print(f"❌ {method} {path:40} -> Erro: {e}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor")
        print("💡 Certifique-se de que o FastAPI está rodando em http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Erro ao verificar rotas: {e}")

if __name__ == "__main__":
    check_routes()