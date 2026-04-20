import json
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"

_CSS      = (_ASSETS / "style.css").read_text(encoding="utf-8")
_JS       = (_ASSETS / "script.js").read_text(encoding="utf-8")
_TEMPLATE = (_ASSETS / "template.html").read_text(encoding="utf-8")


def build_html(records: list[dict], orgaos: list[str], hoje: str, total: int) -> str:
    return (
        _TEMPLATE
        .replace("__CSS__",         _CSS)
        .replace("__JS__",          _JS)
        .replace("__DATA_JSON__",   json.dumps(records,  ensure_ascii=False))
        .replace("__ORGAOS_JSON__", json.dumps(orgaos,   ensure_ascii=False))
        .replace("__HOJE__",        hoje)
        .replace("__TOTAL__",       str(total))
    )
