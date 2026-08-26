## \file /src/utils/convertors/xml2dict.py
# -*- coding: utf-8 -*-

#! .pyenv/bin/python3

"""
.. module:: src.utils.convertors 
	:platform: Windows, Unix
	:synopsis: provides utilities for converting XML data into dictionaries. It includes functions for parsing XML strings and converting XML element trees into dictionary representations.

Functions:
- `_parse_node`: Parses an XML node into a dictionary.
- `_make_dict`: Generates a dictionary with the tag name and value.
- `xml2dict`: Parses an XML string into a dictionary.
- `ET2dict`: Converts an XML element tree into a dictionary.
"""

import re

try:
    import xml.etree.cElementTree as ET
except ImportError as err:
    import xml.etree.ElementTree as ET

def _parse_node(node: ET.Element) -> dict | str:
    """Parse an XML node into a dictionary.

    Args:
        node (ET.Element): The XML element to parse.

    Returns:
        dict | str: A dictionary representation of the XML node, or a string if the node has no attributes or children.
    """
    tree = {}
    attrs = {}
    for attr_tag, attr_value in node.attrib.items():
        # Skip href attributes, not supported when converting to dict
        if attr_tag == '{http://www.w3.org/1999/xlink}href':
            continue
        attrs.update(_make_dict(attr_tag, attr_value))

    value = node.text.strip() if node.text is not None else ''

    if attrs:
        tree['attrs'] = attrs

    # Save children
    has_child = False
    for child in list(node):
        has_child = True
        ctag = child.tag
        ctree = _parse_node(child)
        cdict = _make_dict(ctag, ctree)

        # No value when there are child elements
        if ctree:
            value = ''

        # First time an attribute is found
        if ctag not in tree:  # First time found
            tree.update(cdict)
            continue

        # Many times the same attribute, change to a list
        old = tree[ctag]
        if not isinstance(old, list):
            tree[ctag] = [old]  # Change to list
        tree[ctag].append(ctree)  # Add new entry

    if not has_child:
        tree['value'] = value

    # If there is only a value; no attribute, no child, return directly the value
    if list(tree.keys()) == ['value']:
        tree = tree['value']
    return tree

def _make_dict(tag: str, value: any) -> dict:
    """Generate a new dictionary with tag and value.

    Args:
        tag (str): The tag name of the XML element.
        value (any): The value associated with the tag.

    Returns:
        dict: A dictionary with the tag name as the key and the value as the dictionary value.
    """
    tag_values = value
    result = re.compile(r"\{(.*)\}(.*)").search(tag)
    if result:
        tag_values = {'value': value}
        tag_values['xmlns'], tag = result.groups()  # We have a @namespace src!
    return {tag: tag_values}

def xml2dict(xml: str) -> dict:
    """Parse XML string into a dictionary.

    Args:
        xml (str): The XML string to parse.

    Returns:
        dict: The dictionary representation of the XML.
    """
    element_tree = ET.fromstring(xml)
    return ET2dict(element_tree)

def ET2dict(element_tree: ET.Element) -> dict:
    """Convert an XML element tree into a dictionary.

    Args:
        element_tree (ET.Element): The XML element tree.

    Returns:
        dict: The dictionary representation of the XML element tree.
    """
    return _make_dict(element_tree.tag, _parse_node(element_tree))
