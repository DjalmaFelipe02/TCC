from . serializers import JsonSerializer, XmlSerializer

class SerializerFactory:
    """
    Esse código utiliza o padrão de projeto Factory, 
    que é um padrão de projeto criacional que fornece uma interface para criar objetos sem especificar 
    as classes concretas que serão instanciadas. 
    """
    @staticmethod
    def get_serializer(format):
        if format == 'json':
            return JsonSerializer()
        elif format == 'xml':
            return XmlSerializer()
        raise ValueError(format)    