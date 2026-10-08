import json
from pathlib import Path
import tempfile
import unittest

from contract import SIGNER, digest, expected, validate, verify_pair


class PairContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        files = {}
        for name in ('FamilyConnect-OwnerDiagnostic-0.1.18-beta70.apk', 'bootstrap-broker', 'libfc_restricted.so', 'libfc-awg.so'):
            path = self.root / name
            path.write_bytes(name.encode())
            files[name] = digest(path)
        self.manifest = dict(result='PASS', sealed=True, source_revision='a' * 40,
                             source_tag='diag-owner-beta70-ci1', version='0.1.18-beta70',
                             version_code=70, package_id='com.familyconnect.app.friends',
                             debuggable=False, android_architecture='arm64-v8a',
                             gateway_architecture='linux/amd64', signer_sha256=SIGNER,
                             expected_signer_sha256=SIGNER, publication_jobs='skipped',
                             callback_chain_acceptance='PASS', files=files,
                             signed_apk_sha256=files['FamilyConnect-OwnerDiagnostic-0.1.18-beta70.apk'])
        path = self.root / 'pair-manifest.json'
        path.write_text(json.dumps(self.manifest))
        self.acceptance = self.root / 'accepted-pair.json'
        self.acceptance.write_text(json.dumps(dict(result='PASS', pair_directory=str(self.root),
                                                  source_revision='a' * 40, manifest_sha256=digest(path))))

    def test_exact_pair_and_observation(self):
        manifest = verify_pair(self.acceptance)
        validate(expected(manifest), manifest)

    def test_reject_every_observed_identity_drift(self):
        for key in expected(self.manifest):
            with self.subTest(key=key):
                observation = expected(self.manifest)
                observation[key] = 'mismatch'
                with self.assertRaises(AssertionError):
                    validate(observation, self.manifest)

    def test_reject_newer_or_older_version(self):
        for version in ('69', '71'):
            observation = expected(self.manifest) | dict(version_code=version)
            with self.assertRaises(AssertionError):
                validate(observation, self.manifest)

    def test_reject_artifact_and_manifest_mutation(self):
        binary = self.root / 'bootstrap-broker'
        binary.write_bytes(b'changed')
        with self.assertRaises(AssertionError):
            verify_pair(self.acceptance)
        path = self.root / 'pair-manifest.json'
        path.write_text('{}')
        with self.assertRaises(AssertionError):
            verify_pair(self.acceptance)


if __name__ == '__main__':
    unittest.main()
