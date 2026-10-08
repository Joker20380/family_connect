from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


class BootstrapCauseContractTests(unittest.TestCase):
    def test_original_sequence_and_single_reconnect(self):
        source = (ROOT / 'OwnerPairBaselineTest.java').read_text()
        self.assertIn('for(int cycle=0;cycle<2;cycle++)', source)
        for literal in ['owner.open(()->{})', 'SystemClock.elapsedRealtime()+180000', 'engine.up("")', 'sample<15', 'SystemClock.sleep(1000)']:
            self.assertIn(literal, source)
        self.assertNotIn('Thread.sleep', source)
        self.assertNotIn('prearm', source)
        self.assertNotIn('singleExperiment', source)

    def test_export_precedes_cleanup_and_primary_is_preserved(self):
        source = (ROOT / 'OwnerPairBaselineTest.java').read_text()
        self.assertLess(source.index('"startup_before_cleanup"'), source.index('engine.down()'))
        self.assertLess(source.index('engine.down()'), source.index('owner.close()'))
        self.assertIn('if(primary!=null)OwnerStartupEvidence.attach(primary,secondary)', source)
        self.assertIn('engineStopped && ownerStopped', source)
        helper = (ROOT / 'OwnerStartupEvidence.java').read_text()
        self.assertIn('if(primary!=secondary)primary.addSuppressed(secondary)', helper)
        self.assertIn('NO_ACCEPTED_ATTEMPT', helper)
        self.assertIn('COLLECTION_ERROR', helper)
        self.assertIn('"Startup attempt mismatch",handle,value.attempt', helper)
        self.assertIn('StartupDiagnostics.read(context)', helper)
        self.assertIn('file.readFully()', helper)

    def test_exact_identity_and_synthetic_scope(self):
        baseline = (ROOT / 'baseline.py').read_text()
        self.assertIn("'expected_version', '71'", baseline)
        self.assertIn("manifest['signed_apk_sha256']", baseline)
        self.assertIn("manifest['files']['libfc_restricted.so']", baseline)
        synthetic = (ROOT / 'OwnerStartupPersistenceTest.java').read_text()
        self.assertIn('context.getCacheDir()', synthetic)
        self.assertIn('SYNTHETIC_NOT_LIVE', synthetic)
        self.assertNotIn('NativeRestricted.begin', synthetic)
        self.assertNotIn('StartupDiagnostics.begin', synthetic)
        self.assertNotIn('getNoBackupFilesDir', synthetic)


if __name__ == '__main__':
    unittest.main()
