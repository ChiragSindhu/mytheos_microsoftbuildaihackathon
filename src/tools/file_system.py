"""File system operations."""
from pathlib import Path
from typing import List, Optional
import shutil
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FileSystem:
    """File system utilities."""
    
    @staticmethod
    def read_file(file_path: str) -> Optional[str]:
        """Read file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None
    
    @staticmethod
    def write_file(file_path: str, content: str) -> bool:
        """Write content to file."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            return False
    
    @staticmethod
    def find_files(directory: str, pattern: str = "*") -> List[str]:
        """Find files matching pattern."""
        try:
            return [str(p) for p in Path(directory).rglob(pattern)]
        except Exception as e:
            logger.error(f"Failed to find files: {e}")
            return []
    
    @staticmethod
    def copy_file(source: str, destination: str) -> bool:
        """Copy file."""
        try:
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logger.error(f"Failed to copy {source} to {destination}: {e}")
            return False