"""Validate and locally persist answer keys for arbitrary three-digit exam codes."""
from __future__ import annotations

import json
import os
from pathlib import Path

from omr import CODES, DEFAULT_KEY, normalize_code, normalize_key

LOCAL_CONFIG_PATH = Path(__file__).resolve().parent / 'answer_keys_local.json'


def default_keys() -> dict[str, str]:
    """Example data only; users must replace demo keys before real grading."""
    return {code: DEFAULT_KEY for code in CODES}


def validate_keys(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError('Cấu hình phải là đối tượng JSON chứa ít nhất một mã đề.')
    result = {}
    for raw_code, raw_key in raw.items():
        code = normalize_code(raw_code)
        if code in result:
            raise ValueError(f'Mã đề {code} bị trùng.')
        result[code] = normalize_key(raw_key)
    return result


def parse_config(content: str | bytes) -> dict[str, str]:
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise ValueError('Tệp JSON không đọc được hoặc sai định dạng.') from exc
    # Cho phép cả định dạng cũ {"101":"ABCD..."} và định dạng mới {"answer_keys":{...}}.
    if isinstance(parsed, dict) and 'answer_keys' in parsed:
        parsed = parsed['answer_keys']
    return validate_keys(parsed)


def dump_config(raw: dict[str, str]) -> str:
    clean = validate_keys(raw)
    return json.dumps({'version': 1, 'answer_keys': clean}, indent=2, ensure_ascii=False)


def load_config(path: Path = LOCAL_CONFIG_PATH) -> dict[str, str]:
    path = Path(path)
    if not path.exists():
        return default_keys()
    return parse_config(path.read_text(encoding='utf-8'))


def save_config(raw: dict[str, str], path: Path = LOCAL_CONFIG_PATH) -> None:
    path = Path(path)
    content = dump_config(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    try:
        tmp.write_text(content, encoding='utf-8')
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
