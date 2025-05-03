# subsystems.py
class InventoryService:
    def check_stock(self, product_id: str) -> bool:
        print(f"Verificando estoque do produto {product_id}")
        return True  # Simulado

class ShippingService:
    def calculate_shipping(self, zip_code: str) -> float:
        print(f"Calculando frete para CEP {zip_code}")
        return 15.99  # Valor fixo

class TaxService:
    def calculate_tax(self, subtotal: float) -> float:
        rate = 0.1  # 10%
        return subtotal * rate