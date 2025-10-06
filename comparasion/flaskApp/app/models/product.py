"""
Modelo de produto para a aplicação Flask.
"""
from ..core.database import db, BaseModel


class Product(BaseModel):
    """Modelo de produto."""
    
    __tablename__ = "products"
    
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(50), unique=True, index=True)
    category = db.Column(db.String(100), index=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"
    
    @property
    def is_in_stock(self) -> bool:
        """Verifica se o produto está em estoque."""
        return self.stock_quantity > 0
    
    def reduce_stock(self, quantity: int) -> bool:
        """Reduz o estoque do produto."""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity: int):
        """Aumenta o estoque do produto."""
        self.stock_quantity += quantity
        self.save()
    
    @classmethod
    def get_by_sku(cls, sku: str):
        """Busca um produto pelo SKU."""
        return cls.query.filter_by(sku=sku).first()
    
    @classmethod
    def get_by_category(cls, category: str):
        """Busca produtos por categoria."""
        return cls.query.filter_by(category=category, is_active=True).all()
    
    @classmethod
    def get_active_products(cls):
        """Retorna todos os produtos ativos."""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def search_products(cls, search_term: str):
        """Busca produtos por nome ou descrição."""
        return cls.query.filter(
            db.or_(
                cls.name.contains(search_term),
                cls.description.contains(search_term)
            ),
            cls.is_active == True
        ).all()
    
    @classmethod
    def create_product(cls, name: str, price: float, description: str = None, 
                      sku: str = None, category: str = None, stock_quantity: int = 0):
        """Cria um novo produto."""
        product = cls(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            sku=sku,
            category=category
        )
        product.save()
        return product
