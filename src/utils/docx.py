# -*- coding: utf-8 -*-
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union, List
from src.logger.logger import logger

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def extract_docx_text(file_path: Union[str, Path], as_markdown: bool = True) -> Optional[str]:
    path = Path(file_path)
    if not path.is_file():
        logger.error(f"DOCX file not found: {path}")
        return None
    try:
        with zipfile.ZipFile(path, "r") as zf:
            if "word/document.xml" not in zf.namelist():
                logger.error(f"Invalid DOCX: {path}")
                return None
            xml_content = zf.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            body = tree.find(W_NS + "body")
            if body is None:
                return ""
            lines: List[str] = []
            for elem in body:
                tag = elem.tag.replace(W_NS, "")
                if tag == "p":
                    p_text = "".join(t.text for t in elem.findall(".//" + W_NS + "t") if t.text)
                    style = ""
                    ppr = elem.find(W_NS + "pPr")
                    if ppr is not None:
                        pstyle = ppr.find(W_NS + "pStyle")
                        if pstyle is not None:
                            style = pstyle.attrib.get(W_NS + "val", "")
                    if as_markdown and style.startswith("Heading"):
                        lvl = style.replace("Heading", "").strip()
                        h = "#" * int(lvl) if lvl.isdigit() else "##"
                        lines.append(f"{h} {p_text}")
                    elif p_text.strip():
                        lines.append(p_text)
                elif tag == "tbl":
                    for row in elem.findall(".//" + W_NS + "tr"):
                        row_cells = []
                        for cell in row.findall(".//" + W_NS + "tc"):
                            cell_text = " ".join(t.text for t in cell.findall(".//" + W_NS + "t") if t.text)
                            row_cells.append(cell_text.strip())
                        if row_cells:
                            if as_markdown:
                                lines.append("| " + " | ".join(row_cells) + " |")
                            else:
                                lines.append("\t".join(row_cells))
            return "\n\n".join(lines)
    except Exception as ex:
        logger.error(f"Failed to extract DOCX: {path}", ex)
        return None
