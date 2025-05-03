class PaymentProcessor:
    def __init__(self, strategy):
        self.strategy = strategy

    def execute_payment(self, amount):
        return self.strategy.pay(amount)


class CreditCardStrategy:
    def pay(self, amount):
        return {"status": "success", "method": "creditcard", "amount": amount}


class PayPalStrategy:
    def pay(self, amount):
        return {"status": "success", "method": "paypal", "amount": amount}