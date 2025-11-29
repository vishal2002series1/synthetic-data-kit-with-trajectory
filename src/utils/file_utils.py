"""
File utility functions.
"""

import json
import jsonlines
from pathlib import Path
from typing import List, Dict, Any, Union


def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Read JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2):
    """Write data to JSON file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_jsonl(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read JSONL file."""
    data = []
    with jsonlines.open(file_path, 'r') as reader:
        for obj in reader:
            data.append(obj)
    return data


def write_jsonl(data: List[Dict[str, Any]], file_path: Union[str, Path]):
    """Write data to JSONL file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with jsonlines.open(file_path, 'w') as writer:
        writer.write_all(data)
