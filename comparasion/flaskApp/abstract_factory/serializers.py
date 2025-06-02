import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Dict

# --- Interfaces Abstratas dos Produtos ---

class CompactSerializer(ABC):
    """Interface para serializadores que geram saída compacta."""
    @abstractmethod
    def serialize(self, data: Dict[str, Any]) -> str:
        pass

class ReadableSerializer(ABC):
    """Interface para serializadores que geram saída legível (indentada)."""
    @abstractmethod
    def serialize(self, data: Dict[str, Any]) -> str:
        pass

# --- Produtos Concretos para JSON ---

class CompactJsonSerializer(CompactSerializer):
    """Serializador JSON que gera saída compacta."""
    def serialize(self, data: Dict[str, Any]) -> str:
        try:
            return json.dumps(data, separators=(",", ":"))
        except TypeError as e:
            raise ValueError(f"Erro ao serializar para JSON compacto: {e}")

class ReadableJsonSerializer(ReadableSerializer):
    """Serializador JSON que gera saída legível (indentada)."""
    def serialize(self, data: Dict[str, Any]) -> str:
        try:
            return json.dumps(data, indent=4)
        except TypeError as e:
            raise ValueError(f"Erro ao serializar para JSON legível: {e}")

# --- Produtos Concretos para XML ---

class CompactXmlSerializer(CompactSerializer):
    """Serializador XML que gera saída compacta."""
    def serialize(self, data: Dict[str, Any]) -> str:
        try:
            root_key = next(iter(data)) if data else "data"
            root = ET.Element(root_key)
            self._build_xml(root, data.get(root_key) if len(data) == 1 else data)
            return ET.tostring(root, encoding="unicode", short_empty_elements=True)
        except Exception as e:
            raise ValueError(f"Erro ao serializar para XML compacto: {e}")

    def _build_xml(self, parent: ET.Element, data: Any):
        if isinstance(data, dict):
            for key, value in data.items():
                element = ET.SubElement(parent, key)
                self._build_xml(element, value)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                item_tag = f"{parent.tag}_item" if parent.tag else "item"
                element = ET.SubElement(parent, item_tag, attrib={"index": str(index)})
                self._build_xml(element, item)
        else:
            parent.text = str(data)

class ReadableXmlSerializer(ReadableSerializer):
    """Serializador XML que gera saída legível (indentada)."""
    def serialize(self, data: Dict[str, Any]) -> str:
        try:
            root_key = next(iter(data)) if data else "data"
            root = ET.Element(root_key)
            self._build_xml(root, data.get(root_key) if len(data) == 1 else data)
            ET.indent(root, space="  ", level=0)
            return ET.tostring(root, encoding="unicode")
        except Exception as e:
            raise ValueError(f"Erro ao serializar para XML legível: {e}")

    def _build_xml(self, parent: ET.Element, data: Any):
        if isinstance(data, dict):
            for key, value in data.items():
                element = ET.SubElement(parent, key)
                self._build_xml(element, value)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                item_tag = f"{parent.tag}_item" if parent.tag else "item"
                element = ET.SubElement(parent, item_tag, attrib={"index": str(index)})
                self._build_xml(element, item)
        else:
            parent.text = str(data)