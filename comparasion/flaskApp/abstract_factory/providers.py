from abc import ABC, abstractmethod
from .serializers import CompactSerializer, ReadableSerializer, CompactJsonSerializer, ReadableJsonSerializer, CompactXmlSerializer, ReadableXmlSerializer

# --- Interface da Abstract Factory ---

class SerializerProvider(ABC):
    """Interface da Abstract Factory (Abstract Factory).

    Define métodos para criar os diferentes tipos de produtos abstratos
    (serializadores compactos e legíveis).
    """
    @abstractmethod
    def create_compact_serializer(self) -> CompactSerializer:
        """Cria um serializador compacto."""
        pass

    @abstractmethod
    def create_readable_serializer(self) -> ReadableSerializer:
        """Cria um serializador legível."""
        pass

# --- Fábricas Concretas ---

class JsonProvider(SerializerProvider):
    """Fábrica Concreta para criar serializadores JSON.

    Implementa os métodos da SerializerProvider para retornar
    instâncias específicas de serializadores JSON.
    """
    def create_compact_serializer(self) -> CompactSerializer:
        return CompactJsonSerializer()

    def create_readable_serializer(self) -> ReadableSerializer:
        return ReadableJsonSerializer()

class XmlProvider(SerializerProvider):
    """Fábrica Concreta para criar serializadores XML.

    Implementa os métodos da SerializerProvider para retornar
    instâncias específicas de serializadores XML.
    """
    def create_compact_serializer(self) -> CompactSerializer:
        return CompactXmlSerializer()

    def create_readable_serializer(self) -> ReadableSerializer:
        return ReadableXmlSerializer()

# --- Função auxiliar para obter a fábrica concreta ---

def get_provider(format: str) -> SerializerProvider:
    """Retorna a fábrica concreta apropriada com base no formato."""
    if format == 'json':
        return JsonProvider()
    elif format == 'xml':
        return XmlProvider()
    else:
        raise ValueError(f"Formato de provedor não suportado: {format}")