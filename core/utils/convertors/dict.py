# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Dictionary and SimpleNamespace conversion utilities
# =============================================================================
# Description:
#   Converts between dictionaries and SimpleNamespace objects recursively.
#   Provides export functions to various formats (XML, CSV, JSON, XLS, HTML, PDF)
#   for flexible data serialization and format conversion.
#
# File: dict.py
# Project: ai-breadboard
# Package: core.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Converter for converting between dict and SimpleNamespace objects.

Functions:
    - `dict2ns`: Recursively convert dictionaries to SimpleNamespace objects.
    - `dict2xml`: Generate an XML string from a dictionary.
    - `dict2csv`: Save dictionary or SimpleNamespace data to a CSV file.
    - `dict2json`: Save dictionary or SimpleNamespace data to a JSON file.
    - `dict2xls`: Save dictionary or SimpleNamespace data to an XLS file.
    - `dict2html`: Generate an HTML table string from a dictionary or SimpleNamespace object.
    - `dict2pdf`: Save dictionary data as a PDF file.
"""

import json
from types import SimpleNamespace
from typing import Any, Dict, List
from pathlib import Path
from xml.dom.minidom import getDOMImplementation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from core.utils.xls import save_xls_file

def replace_key_in_dict(data, old_key, new_key) -> dict:
    """
    Recursively replaces a key in a dictionary or list.
    
    Args:
        data (dict | list): The dictionary or list where key replacement occurs.
        old_key (str): The key to be replaced.
        new_key (str): The new key.
    
    Returns:
        dict: The updated dictionary with replaced keys.

    Example Usage:

        replace_key_in_json(data, 'name', 'category_name')

        # Example 1: Simple dictionary
        data = {"old_key": "value"}
        updated_data = replace_key_in_json(data, "old_key", "new_key")
        # updated_data becomes {"new_key": "value"}

        # Example 2: Nested dictionary
        data = {"outer": {"old_key": "value"}}
        updated_data = replace_key_in_json(data, "old_key", "new_key")
        # updated_data becomes {"outer": {"new_key": "value"}}

        # Example 3: List of dictionaries
        data = [{"old_key": "value1"}, {"old_key": "value2"}]
        updated_data = replace_key_in_json(data, "old_key", "new_key")
        # updated_data becomes [{"new_key": "value1"}, {"new_key": "value2"}]

        # Example 4: Mixed nested structure with lists and dictionaries
        data = {"outer": [{"inner": {"old_key": "value"}}]}
        updated_data = replace_key_in_json(data, "old_key", "new_key")
        # updated_data becomes {"outer": [{"inner": {"new_key": "value"}}]}

    """
    if isinstance(data, dict):
        for key in list(data.keys()):
            new_k = key
            if key == old_key:
                data[new_key] = data.pop(old_key)
                new_k = new_key
            
            if isinstance(data[new_k], (dict, list)):
                replace_key_in_dict(data[new_k], old_key, new_key)
    elif isinstance(data, list):
        for item in data:
            replace_key_in_dict(item, old_key, new_key)
    
    return data

def dict2pdf(data: dict | SimpleNamespace, file_path: str | Path) -> None:
    """
    Save dictionary data to a PDF file.

    Args:
        data (dict | SimpleNamespace): The dictionary to convert to PDF.
        file_path (str | Path): Path to the output PDF file.
    """
    if isinstance(data, SimpleNamespace):
        data = data.__dict__

    pdf = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4
    x, y = 50, height - 50

    pdf.setFont("Helvetica", 12)

    for key, value in data.items():
        line = f"{key}: {value}"
        pdf.drawString(x, y, line)
        y -= 20

        if y < 50:  # Create new page if not enough space
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = height - 50

    pdf.save()

def dict2ns(data: Dict[str, Any] | List[Any]) -> Any:
    """
    Recursively convert dictionaries to SimpleNamespace.

    Args:
        data (Dict[str, Any] | List[Any]): The data to convert.

    Returns:
        Any: Converted data as a SimpleNamespace or a list of SimpleNamespace.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = dict2ns(value)
            elif isinstance(value, list):
                data[key] = [dict2ns(item) if isinstance(item, dict) else item for item in value]
        return SimpleNamespace(**data)
    elif isinstance(data, list):
        return [dict2ns(item) if isinstance(item, dict) else item for item in data]
    return data

def dict2xml(data: Dict[str, Any], encoding: str = 'UTF-8') -> str:
    """
    Generate an XML string from a dictionary.

    Args:
        data (Dict[str, Any]): The data to convert to XML.
        encoding (str, optional): Data encoding. Defaults to 'UTF-8'.

    Returns:
        str: The XML string representing the input dictionary.

    Raises:
        Exception: If more than one root node is provided.
    """
    def _process_simple(doc, tag, tag_value):
        """
        Generate a node for simple types (int, str).

        Args:
            doc (xml.dom.minidom.Document): XML document object.
            tag (str): Tag name for the XML element.
            tag_value (Any): Value of the tag.

        Returns:
            xml.dom.minidom.Element: Node representing the tag and value.
        """
        node = doc.createElement(tag)
        node.appendChild(doc.createTextNode(str(tag_value)))
        return node

    def _process_attr(doc, attr_value: Dict[str, Any]):
        """
        Generate attributes for an XML element.

        Args:
            doc (xml.dom.minidom.Document): XML document object.
            attr_value (Dict[str, Any]): Dictionary of attributes.

        Returns:
            List[xml.dom.minidom.Attr]: List of attributes for the XML element.
        """
        attrs = []
        for attr_name, value in attr_value.items():
            attr = doc.createAttribute(attr_name)
            attr.nodeValue = value if not isinstance(value, dict) else value.get('value', '')
            attrs.append(attr)
        return attrs

    def _process_complex(doc, children):
        """
        Generate nodes for complex types like lists or dicts.

        Args:
            doc (xml.dom.minidom.Document): XML document object.
            children (List[Tuple[str, Any]]): List of tag-value pairs.

        Returns:
            Tuple[List[xml.dom.minidom.Element], List[xml.dom.minidom.Attr]]: List of child nodes and attributes.
        """
        nodelist = []
        attrs = []
        for tag, value in children:
            if tag == 'attrs':
                attrs = _process_attr(doc, value)
            else:
                nodes = _process(doc, tag, value)
                nodelist.extend(nodes if isinstance(nodes, list) else [nodes])
        return nodelist, attrs

    def _process(doc, tag, tag_value):
        """
        Generate XML DOM object for a tag and its value.

        Args:
            doc (xml.dom.minidom.Document): XML document object.
            tag (str): Tag name for the XML element.
            tag_value (Any): Value of the tag.

        Returns:
            xml.dom.minidom.Element | List[xml.dom.minidom.Element]: Node or list of nodes for the tag and value.
        """
        if isinstance(tag_value, dict) and list(tag_value.keys()) == ['value']:
            tag_value = tag_value['value']

        if tag_value is None:
            tag_value = ''

        if isinstance(tag_value, (float, int, str)):
            return _process_simple(doc, tag, tag_value)

        if isinstance(tag_value, list):
            return _process_complex(doc, [(tag, x) for x in tag_value])[0]

        if isinstance(tag_value, dict):
            node = doc.createElement(tag)
            nodelist, attrs = _process_complex(doc, tag_value.items())
            for child in nodelist:
                node.appendChild(child)
            for attr in attrs:
                node.setAttributeNode(attr)
            return node

    doc = getDOMImplementation().createDocument(None, None, None)
    if len(data) > 1:
        raise Exception('Only one root node allowed')
    
    root, _ = _process_complex(doc, data.items())
    doc.appendChild(root[0])
    return doc.toxml(encoding)

def dict2csv(data: dict | SimpleNamespace, file_path: str | Path) -> bool:
    """
    Save dictionary or SimpleNamespace data to a CSV file.

    Args:
        data (dict | SimpleNamespace): The data to save to a CSV file.
        file_path (str | Path): Path to the CSV file.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    return save_csv_file(data, file_path)

def dict2xls(data: dict | SimpleNamespace, file_path: str | Path) -> bool:
    """
    Save dictionary or SimpleNamespace data to an XLS file.

    Args:
        data (dict | SimpleNamespace): The data to save to an XLS file.
        file_path (str | Path): Path to the XLS file.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    return save_xls_file(data, file_path)

def dict2html(data: dict | SimpleNamespace, encoding: str = 'UTF-8') -> str:
    """
    Generate an HTML table string from a dictionary or SimpleNamespace object.

    Args:
        data (dict | SimpleNamespace): The data to convert to HTML.
        encoding (str, optional): Data encoding. Defaults to 'UTF-8'.

    Returns:
        str: The HTML string representing the input dictionary.
    """
    def dict_to_html_table(data: dict, depth: int = 0) -> str:
        """
        Recursively convert dictionary to HTML table.

        Args:
            data (dict): The dictionary data to convert.
            depth (int, optional): The depth of recursion, used for nested tables. Defaults to 0.

        Returns:
            str: The HTML table as a string.
        """
        html = ['<table border="1" cellpadding="5" cellspacing="0">']
        
        if isinstance(data, dict):
            for key, value in data.items():
                html.append('<tr>')
                html.append(f'<td><strong>{key}</strong></td>')
                if isinstance(value, dict):
                    html.append(f'<td>{dict_to_html_table(value, depth + 1)}</td>')
                elif isinstance(value, list):
                    html.append('<td>')
                    html.append('<ul>')
                    for item in value:
                        html.append(f'<li>{item}</li>')
                    html.append('</ul>')
                    html.append('</td>')
                else:
                    html.append(f'<td>{value}</td>')
                html.append('</tr>')
        else:
            html.append(f'<tr><td colspan="2">{data}</td></tr>')
        
        html.append('</table>')
        return '\n'.join(html)
    
    # Convert data to dictionary if it's a SimpleNamespace
    if isinstance(data, SimpleNamespace):
        data = data.__dict__
    
    html_content = dict_to_html_table(data)
    return f'<!DOCTYPE html>\n<html>\n<head>\n<meta charset="{encoding}">\n<title>Dictionary to HTML</title>\n</head>\n<body>\n{html_content}\n</body>\n</html>'

