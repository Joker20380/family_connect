"""Print reference-derived desktop visual tokens and RU/EN text; never edit Android."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from scripts.verify_desktop_reference import MANIFEST, ROOT, local_path


def extract(root=ROOT):
    reference = json.loads((root / MANIFEST).read_text())
    source = local_path(root, reference["reference"]["source"])
    app = "clients/android/app/src/main/"
    java = app + "java/com/familyconnect/app/TerminalUi.java"
    expected = reference["android_ui_and_handlers"]

    def read(name):
        path = local_path(source, name)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[name]:
            raise ValueError("reference drift: " + name)
        return raw.decode("utf-8")

    terminal = read(java)
    colors = dict(re.findall(r"\b([A-Z_]+)\s*=\s*0xff([0-9a-fA-F]{6})\b", terminal))
    strokes = dict(re.findall(r"\b(STROKE_[A-Z]+)\s*=\s*([.0-9]+)f", terminal))
    if len(colors) != 9 or len(strokes) != 3:
        raise ValueError("reference token declarations changed")
    strings = {}
    files = {}
    for language, directory in (("en", "values"), ("ru", "values-ru")):
        strings[language] = {}
        for name in sorted(expected):
            if not name.startswith(app + "res/" + directory + "/") or not name.endswith(".xml"):
                continue
            resource = ET.fromstring(read(name))
            for element in resource.findall("string"):
                key = element.attrib["name"]
                if key in strings[language]:
                    raise ValueError("duplicate Android string: " + key)
                strings[language][key] = "".join(element.itertext())
                files[language + ":" + key] = name
    return {
        "schema": 1,
        "android_reference": reference["reference"]["apk_sha256"],
        "palette": {name.lower(): "#" + value.lower() for name, value in colors.items()},
        "strokes_dp": {name.removeprefix("STROKE_").lower(): float(value) for name, value in strokes.items()},
        "navigation": ["home", "messenger", "route", "settings"],
        "home_order": ["brand", "connection_controls", "connection_workspace", "map", "navigation"],
        "layout_sources": {name: expected[name] for name in expected if name.rsplit("/", 1)[-1] in
                           ("TerminalUi.java", "CompactHome.java", "HomeBrand.java", "FriendsActivity.java", "ChatActivity.java")},
        "strings": strings,
        "string_sources": files,
        "note": "Exact Android resource text, including Android escapes/placeholders. Presence is not a claim that a feature is enabled. Screenshots and platform layout acceptance remain separate.",
    }


if __name__ == "__main__":
    print(json.dumps(extract(), ensure_ascii=False, indent=2))
