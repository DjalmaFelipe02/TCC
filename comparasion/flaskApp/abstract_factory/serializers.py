import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Dict

# Interface/Classe Base Abstrata para Serializers
class Serializer(ABC):
    """Interface abstrata para serializadores de dados."""
    @abstractmethod
    def serialize(self, data: Dict[str, Any]) -> str:
        """Método abstrato para serializar dados em uma string."""
        pass

# Serializador Concreto para JSON
class JsonSerializer(Serializer):
    """Serializador concreto para o formato JSON."""
    def serialize(self, data: Dict[str, Any]) -> str:
        """Serializa um dicionário Python para uma string JSON formatada."""
        try:
            # Usa indent=4 para uma saída JSON mais legível
            return json.dumps(data, indent=4)
        except TypeError as e:
            # Captura erros comuns de serialização JSON
            raise ValueError(f"Erro ao serializar para JSON: {e}")

# Serializador Concreto para XML
class XmlSerializer(Serializer):
    """Serializador concreto para o formato XML (simplificado)."""
    def serialize(self, data: Dict[str, Any]) -> str:
        """Serializa um dicionário Python para uma string XML simples."""
        try:
            # Cria o elemento raiz (usando a primeira chave ou 'data' como fallback)
            root_key = next(iter(data)) if data else 'data'
            root = ET.Element(root_key)
            # Constrói a árvore XML a partir do dicionário
            self._build_xml(root, data.get(root_key) if len(data) == 1 else data)

            # Converte a árvore ElementTree para uma string XML formatada
            ET.indent(root, space="  ", level=0)
            return ET.tostring(root, encoding='unicode')
        except Exception as e:
            # Captura erros durante a construção ou serialização XML
            raise ValueError(f"Erro ao serializar para XML: {e}")

    def _build_xml(self, parent: ET.Element, data: Any):
        """Função auxiliar recursiva para construir a árvore XML."""
        if isinstance(data, dict):
            for key, value in data.items():
                element = ET.SubElement(parent, key)
                self._build_xml(element, value)
        elif isinstance(data, list):
            # Para listas, cria um elemento para cada item
            for index, item in enumerate(data):
                # Usando o nome do pai com sufixo _item ou um nome genérico
                item_tag = f"{parent.tag}_item" if parent.tag else "item"
                element = ET.SubElement(parent, item_tag, attrib={"index": str(index)})
                self._build_xml(element, item)
        else:
            # Converte valores não-string para string
            parent.text = str(data)