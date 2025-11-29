"""
Logging utilities for Trajectory Synthetic Data Generator.
"""

import sys
import logging
from pathlib import Path
from typing import Optional


class CustomLogger(logging.Logger):
    """Extended logger with success level."""
    
    SUCCESS = 25  # Between INFO (20) and WARNING (30)
    
    def __init__(self, name: str):
        super().__init__(name)
        logging.addLevelName(self.SUCCESS, "SUCCESS")
    
    def success(self, message: str, *args, **kwargs):
        """Log success message."""
        if self.isEnabledFor(self.SUCCESS):
            self._log(self.SUCCESS, message, args, **kwargs)


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    logger_name: str = "trajectory_generator"
) -> logging.Logger:
    """
    Set up logger with custom formatting.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        logger_name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Set custom logger class
    logging.setLoggerClass(CustomLogger)
    
    # Get logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
