# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   """
#
# File: xls.py
# Project: ai-breadboard
# Package: core.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
.. module:: src.utils.convertors 
	:platform: Windows, Unix
	:synopsis:

"""

from pathlib import Path

from core.utils.xls import read_xls_as_dict, save_xls_file

def xls2dict(xls_file: str | Path) -> dict | None:
    """"""
    return read_xls_as_dict(xls_file = xls_file)

