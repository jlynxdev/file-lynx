from pathlib import Path


def determine_type(path: Path) -> str:
    if path.is_dir():
        return 'folder'
    if path.is_file():
        return 'file'
    return 'unknown'
