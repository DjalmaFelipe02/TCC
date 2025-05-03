# serializers.py
class JsonSerializer:
    def serialize(self, data: dict) -> str:
        import json
        return json.dumps(data, indent=2)

class XmlSerializer:
    def serialize(self, data: dict) -> str:
        from xml.etree.ElementTree import Element, tostring
        def build_xml(element_name, value):
            elem = Element(element_name)
            if isinstance(value, dict):
                for k, v in value.items():
                    elem.append(build_xml(k, v))
            else:
                elem.text = str(value)
            return elem
        return tostring(build_xml("data", data)).decode()