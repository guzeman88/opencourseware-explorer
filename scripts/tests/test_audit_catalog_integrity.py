import json

from scripts.audit_catalog_integrity import decode_copy_text_line


def test_decode_copy_text_line_restores_json_escapes():
    original = {"description": 'Line one\nLine two with "quotes" and a \\ slash'}
    json_text = json.dumps(original, ensure_ascii=False)
    copy_text = (
        json_text.replace("\\", "\\\\")
        .replace("\b", "\\b")
        .replace("\f", "\\f")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace("\v", "\\v")
        + "\n"
    ).encode("utf-8")

    assert json.loads(decode_copy_text_line(copy_text)) == original
