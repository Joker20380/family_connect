import hashlib
import json
from pathlib import Path
import shutil


root = Path(__file__).resolve().parent
previous = root.parent / 'reliable-fast-recovery-1'
sources = {}
for variant in ('baseline', 'candidate'):
    origin = previous / variant / 'carrier'
    destination = root / variant / 'carrier'
    shutil.copytree(origin, destination)
    sources[variant] = {
        str(filename.relative_to(origin)): hashlib.sha256(filename.read_bytes()).hexdigest()
        for filename in sorted(origin.rglob('*')) if filename.is_file()
    }
    fixture = (origin / 'tcpforward/integration_test.go').read_text()
    credentials = fixture[fixture.index('func testCredentials('):fixture.index('\nfunc authenticatedPair(')]
    imports = '''package telemost
import (
"crypto/ed25519"
"crypto/rand"
"crypto/sha256"
"crypto/x509"
"crypto/x509/pkix"
"encoding/hex"
"encoding/json"
"encoding/pem"
"math/big"
"net/url"
"strings"
"testing"
"time"
"github.com/Joker20380/family_connect/carrier/familysession"
)
'''
    (destination / 'telemost/full_stack_credentials_test.go').write_text(imports + credentials)
    shutil.copyfile(root / 'full_stack_test.go', destination / 'telemost/full_stack_test.go')
    shutil.copyfile(root / 'fixture_dns.go', destination / 'tcpforward/fixture_dns.go')
(root / 'input-carrier-files.json').write_text(json.dumps(sources, sort_keys=True, indent=2) + '\n')
