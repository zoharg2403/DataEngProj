import logging
from pathlib import Path
from datetime import datetime as dt

from utils.config import Config, ConfigNode

class CustomFormatter(logging.Formatter):
    """Custom formatter to center-align log levels"""
    def format(self, record):
        # Center-align the level name to 5 characters
        record.levelname = f"{record.levelname:^10}"
        return super().format(record)


class AppLogger:

    def __init__(self, config: ConfigNode = None) -> None:

        self._formatter         = CustomFormatter('%(asctime)s [%(levelname)s]: %(message)s')
        self._is_initialized    = False
        self.config: ConfigNode = config if config else Config().logger
        self.logger             = None
        self._filepath          = self._get_filepath()

    def _get_filepath(self):
        dir_ = Path(self.config.path)
        dir_.mkdir(parents=True, exist_ok=True)
        return dir_ / (self.config.filename_base + f"_{dt.now().strftime("%Y%m%d_%H%M%S")}.txt")

    def _initialize_logger(self) -> logging.Logger:       
        # Create logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()

        handlers = [logging.StreamHandler(), logging.FileHandler(self._filepath)]
        for handler in handlers:
            handler.setLevel(logging.INFO)
            handler.setFormatter(self._formatter)
            logger.addHandler(handler)
        
        # prevent propagation to root logger to avoid duplicates
        logger.propagate = False

        # Attach AppLogger methods to the logger instance
        logger.title = self._title
        logger.subtitle = self._subtitle
        
        self.logger = logger

    def get(self):
        if self._is_initialized:
            return self.logger
        
        self._initialize_logger()
        self._is_initialized = True
        return self.logger
    
    def _title(self, txt: str) -> None:
        self.logger.info(f"{'':=^80}")
        self.logger.info(f"{txt: ^80}")
        self.logger.info(f"{'':=^80}")
    
    def _subtitle(self, txt: str) -> None:
        self.logger.info(f"{'  ' + txt + '  ':-^80}")

# if __name__ == "__main__":
#     logger = AppLogger().get()
#     logger.info("This is a test message")
#     logger.warning("This is a warning message")
#     logger.error("This is an error message")
#     logger.critical("This is a critical message")
