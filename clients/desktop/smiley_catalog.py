"""Android106 text-token semantics; no wire or stored text conversion."""
import json
from pathlib import Path
import unicodedata

CATALOG = json.loads(Path(__file__).with_name('smiley_catalog.json').read_text())
FACES = tuple(CATALOG['faces'])


def whitespace(character):
    return character in '\t\n\v\f\r\x1c\x1d\x1e\x1f' or (
        unicodedata.category(character) in ('Zs', 'Zl', 'Zp') and character not in '\u00a0\u2007\u202f')


def find(text):
    if len(text.encode('utf-16-le')) // 2 > 4096:
        raise ValueError('Chat text too long')
    matches = []
    offset = 0
    while offset < len(text):
        best = None
        if offset == 0 or whitespace(text[offset - 1]):
            for index, face in enumerate(FACES):
                for alias in face['aliases']:
                    end = offset + len(alias)
                    if text.startswith(alias, offset) and (end == len(text) or whitespace(text[end])):
                        if best is None or end > best[1]:
                            best = (offset, end, index)
        if best is None:
            offset += 1
        else:
            matches.append(best)
            offset = best[1]
    return matches


def insertion(text, start, end, token):
    before = ' ' if start and not whitespace(text[start - 1]) else ''
    after = ' ' if end < len(text) and not whitespace(text[end]) else ''
    return before + token + after
