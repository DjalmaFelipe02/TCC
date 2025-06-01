# payment_processor.py (Flask)

from abc import ABC, abstractmethod

# Interface da Estratégia
class PaymentStrategy(ABC):
    """Interface abstrata para as estratégias de pagamento."""
    @abstractmethod
    def pay(self, amount: float) -> dict:
        """Método abstrato para processar o pagamento."""
        pass

# Estratégias Concretas
class CreditCardStrategy(PaymentStrategy):
    """Estratégia concreta para pagamento com Cartão de Crédito."""
    def pay(self, amount: float) -> dict:
        """Simula o processamento de pagamento com cartão de crédito."""
        print(f"Processando ${amount:.2f} com Cartão de Crédito (Flask)")
        # Lógica real de integração com gateway de cartão de crédito iria aqui
        return {"status": "success", "method": "creditcard", "amount": amount, "framework": "Flask"}

class PayPalStrategy(PaymentStrategy):
    """Estratégia concreta para pagamento com PayPal."""
    def pay(self, amount: float) -> dict:
        """Simula o processamento de pagamento com PayPal."""
        print(f"Processando ${amount:.2f} com PayPal (Flask)")
        # Lógica real de integração com API do PayPal iria aqui
        return {"status": "success", "method": "paypal", "amount": amount, "framework": "Flask"}

# Contexto
class PaymentProcessor:
    """Contexto que utiliza uma estratégia de pagamento (Versão Flask).

    Este padrão (Strategy) define uma família de algoritmos (estratégias de pagamento),
    encapsula cada um deles e os torna intercambiáveis. O PaymentProcessor
    permite que o algoritmo varie independentemente dos clientes que o utilizam.
    A implementação da lógica do padrão é idêntica à versão do FastAPI.
    """
    def __init__(self, strategy: PaymentStrategy):
        """Inicializa o processador com uma estratégia específica."""
        self._strategy = strategy

    def set_strategy(self, strategy: PaymentStrategy):
        """Permite alterar a estratégia em tempo de execução."""
        self._strategy = strategy

    def execute_payment(self, amount: float) -> dict:
        """Executa o pagamento utilizando a estratégia configurada."""
        # Delega a execução para o objeto da estratégia atual
        return self._strategy.pay(amount)

