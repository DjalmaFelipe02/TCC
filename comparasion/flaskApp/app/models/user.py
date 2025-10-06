"""
Modelo de usuário para a aplicação Flask.
"""
from ..core.database import db, BaseModel


class User(BaseModel):
    """Modelo de usuário."""
    
    __tablename__ = "users"
    
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_superuser = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    orders = db.relationship("Order", backref="user", lazy=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """Converte o modelo para dicionário (sem senha)."""
        data = super().to_dict()
        # Remove a senha do dicionário por segurança
        data.pop('hashed_password', None)
        return data
    
    def check_password(self, password: str) -> bool:
        """Verifica se a senha está correta."""
        from ..core.security import security_manager
        return security_manager.verify_password(password, self.hashed_password)
    
    def set_password(self, password: str):
        """Define uma nova senha para o usuário."""
        from ..core.security import security_manager
        self.hashed_password = security_manager.get_password_hash(password)
    
    @classmethod
    def get_by_username(cls, username: str):
        """Busca um usuário pelo nome de usuário."""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_by_email(cls, email: str):
        """Busca um usuário pelo email."""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def create_user(cls, username: str, email: str, full_name: str, password: str, is_superuser: bool = False):
        """Cria um novo usuário."""
        user = cls(
            username=username,
            email=email,
            full_name=full_name,
            is_superuser=is_superuser
        )
        user.set_password(password)
        user.save()
        return user
