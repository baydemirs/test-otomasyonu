"""Görev kanıt doğrulayıcılarının ortak dosya ve koşul işlemleri."""
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def project_path(root, reference):
    root = Path(root).resolve()
    path = (root / reference).resolve()
    path.relative_to(root)
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_versions(root, versions, expected_files, message):
    normalized = {name.replace('\\', '/'): value for name, value in versions.items()}
    require(set(normalized) == set(expected_files), message)
    for name, value in normalized.items():
        require(digest(project_path(root, name)) == value, 'Eski surume ait kanit: ' + name)
