"""XML file type adapter."""

import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Any

from .base import FileTypeAdapter


class XMLAdapter(FileTypeAdapter):
    """Adapter for XML files."""

    def __init__(self, encoding: str = "utf-8", record_path: str = ".//record"):
        self.encoding = encoding
        self.record_path = record_path

    def parse(self, source: str | bytes) -> list[dict]:
        if isinstance(source, str):
            source = source.encode(self.encoding)

        tree = ET.parse(BytesIO(source))
        root = tree.getroot()

        records = []
        for elem in root.findall(self.record_path):
            records.append(self._element_to_dict(elem))

        return records

    def _element_to_dict(self, element: ET.Element) -> dict:
        result = {}
        for attr, value in element.attrib.items():
            result[f"@{attr}"] = value
        for child in element:
            if len(child) > 0:
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(self._element_to_dict(child))
                else:
                    result[child.tag] = self._element_to_dict(child)
            else:
                result[child.tag] = child.text
        if element.text and element.text.strip():
            result["_text"] = element.text.strip()
        return result

    def _dict_to_element(self, data: dict, parent: ET.Element) -> None:
        for key, value in data.items():
            if key.startswith("@"):
                parent.set(key[1:], value)
            elif key == "_text":
                parent.text = str(value)
            elif isinstance(value, dict):
                child = ET.SubElement(parent, key)
                self._dict_to_element(value, child)
            elif isinstance(value, list):
                for item in value:
                    child = ET.SubElement(parent, key)
                    if isinstance(item, dict):
                        self._dict_to_element(item, child)
                    else:
                        child.text = str(item)
            else:
                child = ET.SubElement(parent, key)
                child.text = str(value)

    def serialize(self, data: list[dict], destination: str) -> None:
        root = ET.Element("root")
        for record in data:
            record_elem = ET.SubElement(root, "record")
            self._dict_to_element(record, record_elem)

        tree = ET.ElementTree(root)
        tree.write(destination, encoding=self.encoding, xml_declaration=True)

    def get_schema(self) -> dict:
        return {"type": "xml", "record_path": self.record_path, "encoding": self.encoding}

    def validate(self, data: list[dict]) -> bool:
        if not data:
            return False
        return all(isinstance(record, dict) for record in data)
