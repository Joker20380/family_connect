import hashlib
from pathlib import Path

import pytest

from scripts import canonical_gateway_source as source


def test_startup_projection_only_changes_fixed_endpoint_contract(monkeypatch):
    raw = b'package main\n\tflag.Parse()\nServices: pinnedChatServices(*chatServices)\n'
    monkeypatch.setattr(source, 'MAIN_SHA256', hashlib.sha256(raw).hexdigest())
    projected = source.main_projection(raw)
    assert b'Services: services' in projected and b'chat-api-target' in projected
    assert b'family-config' not in projected and b'directory' not in projected
    with pytest.raises(ValueError, match='source mismatch'):
        source.main_projection(raw + b'changed')


def test_startup_projection_rejects_ambiguous_contract(monkeypatch):
    raw = b'\tflag.Parse()\n\tflag.Parse()\nServices: pinnedChatServices(*chatServices)'
    monkeypatch.setattr(source, 'MAIN_SHA256', hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError, match='projection mismatch'):
        source.main_projection(raw)


def test_fixed_endpoint_template_contains_no_operational_route():
    root = Path(__file__).resolve().parents[1]
    raw = (root / source.TEMPLATE_ROOT / 'chat_services.go').read_bytes()
    assert b'netip.ParseAddrPort(target)' in raw
    assert b'netip.MustParseAddrPort("127.0.0.1:4243")' in raw
    assert b'--' not in raw and b'/opt/' not in raw
