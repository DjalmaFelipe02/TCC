# checkout_services.py (FastAPI)

from .subsystems import InventoryService, ShippingService, TaxService

class CheckoutFacade:
    """Facade para simplificar o processo de checkout.

    Este padrão fornece uma interface unificada para um conjunto de interfaces
    em um subsistema (Inventory, Shipping, Tax). Facade define uma interface
    de nível superior que torna o subsistema mais fácil de usar.
    """
    def __init__(self):
        """Inicializa os subsistemas necessários."""
        self._inventory = InventoryService()
        self._shipping = ShippingService()
        self._tax = TaxService()

    def complete_order(self, product_id: int, zip_code: str, subtotal: float) -> dict:
        """Processa um pedido de checkout completo.

        Coordena as chamadas aos subsistemas de inventário, frete e impostos.

        Args:
            product_id: ID do produto.
            zip_code: CEP para cálculo do frete.
            subtotal: Valor subtotal do pedido.

        Returns:
            Um dicionário com os detalhes do custo total do pedido.

        Raises:
            ValueError: Se o produto estiver fora de estoque.
        """
        # 1. Verifica o estoque
        if not self._inventory.check_stock(product_id):
            raise ValueError("Produto fora de estoque")

        # 2. Calcula o frete
        shipping_cost = self._shipping.calculate_shipping(zip_code)

        # 3. Calcula os impostos
        tax_amount = self._tax.calculate_tax(subtotal)

        # 4. Calcula o total e retorna o resultado
        total = subtotal + shipping_cost + tax_amount
        return {
            "message": "Pedido processado com sucesso!",
            "details": {
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "tax_amount": tax_amount,
                "total_amount": total
            }
        }

