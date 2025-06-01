from .serializers import JsonSerializer, XmlSerializer

class SerializerFactory:
    """Abstract Factory para criar serializadores (Versão Flask).

    Este padrão permite criar famílias de objetos relacionados (serializers)
    sem especificar suas classes concretas. A implementação é idêntica
    à versão do FastAPI, demonstrando a portabilidade do padrão.
    """
    @staticmethod
    def create_serializer(format: str):
        """Cria uma instância de serializador com base no formato.

        Args:
            format: O formato desejado ("json" ou "xml").

        Returns:
            Uma instância de JsonSerializer ou XmlSerializer.

        Raises:
            ValueError: Se o formato não for suportado.
        """
        if format == "json":
            # Retorna a implementação concreta para JSON
            return JsonSerializer()
        elif format == "xml":
            # Retorna a implementação concreta para XML
            return XmlSerializer()
        # Lança exceção se o formato for inválido
        raise ValueError(f"Formato de serializador não suportado: {format}")

