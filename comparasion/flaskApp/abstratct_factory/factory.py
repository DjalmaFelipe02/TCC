# factory.py
from .serializers import JsonSerializer, XmlSerializer

class SerializerFactory:
    @staticmethod
    def create_serializer(format: str):
        if format == "json":
            return JsonSerializer()
        elif format == "xml":
            return XmlSerializer()
        raise ValueError(f"Formato não suportado: {format}")