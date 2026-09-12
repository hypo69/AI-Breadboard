# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Invoice Processor Plugin Package Interface
# =============================================================================
# Description:
#   Package initializer for the Invoice Processor plugin, exporting the factory
#   function plugin() and main InvoiceProcessorPlugin class.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.invoice_processor
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Optional

from plugins.invoice_processor.plugin import InvoiceProcessorPlugin
from plugins.invoice_processor.extractor import (
    extract_structured_invoice_data,
    invoice_dict_to_row,
)

__all__ = [
    "InvoiceProcessorPlugin",
    "extract_structured_invoice_data",
    "invoice_dict_to_row",
    "plugin",
]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> InvoiceProcessorPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        InvoiceProcessorPlugin: Configured plugin instance.
    """
    return InvoiceProcessorPlugin(ai_model=ai_model, config=config)