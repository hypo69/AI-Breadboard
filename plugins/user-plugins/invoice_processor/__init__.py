# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins Invoice_Processor -   Init  
# =============================================================================
# Description:
#   Plugin factory function called by plugin loader.
#
# Usage Examples:
#   Python API:
#     from plugins.user-plugins.invoice_processor.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user-plugins.invoice_processor
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Plugin factory function called by plugin loader."""

from typing import Any, Optional
from plugins.invoice_processor.plugin import InvoiceProcessorPlugin
from plugins.invoice_processor.extractor import extract_structured_invoice_data, invoice_dict_to_row
__all__ = ['InvoiceProcessorPlugin', 'extract_structured_invoice_data', 'invoice_dict_to_row', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> InvoiceProcessorPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        InvoiceProcessorPlugin: Configured plugin instance.
    """
    return InvoiceProcessorPlugin(ai_model=ai_model, config=config)