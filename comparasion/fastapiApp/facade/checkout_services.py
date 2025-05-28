# checkout_facade.py

from .subsystems import InventoryService, ShippingService, TaxService

class CheckoutFacade:
    """
    A classe CheckoutFacade segue o padrão de projeto Fachada (Facade).
    fornece uma interface simples para o processo de checkout, escondendo a complexidade dos serviços de estoque, envio e imposto.
    """
    def __init__(self):
        self._inventory = InventoryService()
        self._shipping = ShippingService()
        self._tax = TaxService()
    
    def complete_order(self, product_id: str, zip_code: str, subtotal: float):
        if not self._inventory.check_stock(product_id):
            raise ValueError("Produto fora de estoque")
        
        shipping_cost = self._shipping.calculate_shipping(zip_code)
        tax_amount = self._tax.calculate_tax(subtotal)
        
        return {
            "subtotal": subtotal,
            "shipping": shipping_cost,
            "tax": tax_amount,
            "total": subtotal + shipping_cost + tax_amount
        }