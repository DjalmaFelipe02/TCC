# factory.py

from . serializers import JsonSerializer, XmlSerializer
class SerializerFactory:
    @staticmethod
    def get_serializer(format):
        if format == 'json':
            return JsonSerializer()
        elif format == 'xml':
            return XmlSerializer()
        raise ValueError(format)    