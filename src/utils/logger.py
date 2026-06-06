"""Logging configuration."""
import logging
import sys
from pathlib import Path
from datetime import datetime
from rich.logging import RichHandler
from config.settings import settings

# Create logs directory
LOGS_DIR = settings.BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Console handler with Rich
    console_handler = RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        show_path=True
    )
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_format)
    
    # File handler
    log_file = LOGS_DIR / f"debug_swarm_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger