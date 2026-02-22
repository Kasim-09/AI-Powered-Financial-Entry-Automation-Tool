from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

LOG_NAME = "financial_entry_automation"

def get_logger() -> logging.Logger:
    """Return a module-level logger configured for both CLI and Streamlit usage."""
    logger = logging.getLogger(LOG_NAME)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger

@dataclass
class ValidationIssue:
    """Represents a warning/error found during extraction/cleaning/validation."""
    serial_no: Optional[int]
    level: str  # 'warning' | 'error'
    message: str
    context: Optional[Dict[str, Any]] = None
