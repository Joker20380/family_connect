from dataclasses import replace
import json
import os
from pathlib import Path
import pwd
import stat
import tempfile
import unittest
from unittest.mock import patch

from scripts import gateway_credential_publication as operator


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.parent = self.root / 'live'
        self.parent.mkdir(mode=0o700)
        self.receipts = self.root / 'receipts'
        self.receipts.mkdir(mode=0o700)
        self.target = self.parent / 'gateway.json'
        self.old = b'private-old-credential'
        self.new = b'private-new-credential'
        self.target.write_bytes(self.old)
        self.target.chmod(0o600)
        self.uid = os.geteuid() or next(account.pw_uid for account in pwd.getpwall() if account.pw_uid > 0)
        self.gid = os.getegid()
        if os.geteuid() == 0:
            os.chown(self.target, self.uid, self.gid)
        self.contract = operator.Contract(self.uid,self.gid,os.geteuid(),os.getegid(),0o700)
        self.receipt = self.receipts / 'result.json'
        self.readable = lambda path,uid,gid: True

    def publish(self, **options):
        return operator.publish(self.target,self.new,self.contract,self.receipt,
                                validate=options.pop('validate',lambda raw: True),
                                readable=options.pop('readable',self.readable),**options)

    def retained(self):
        self.assertEqual(self.target.read_bytes(),self.old)
        self.assertFalse(list(self.parent.glob('*.pending-*')))
        record=json.loads(self.receipt.read_bytes())
        self.assertEqual(record['status'],'FAIL')
        self.assertFalse(record['published'])
        self.assertNotIn('private-',self.receipt.read_text())

    def test_correct_metadata_before_rename_and_durable_receipt(self):
        events=[]
        original_replace,original_fsync=operator.os.replace,operator.os.fsync
        def rename(source,destination,**options):
            info=os.stat(source,dir_fd=options['src_dir_fd'])
            self.assertEqual((info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode)),(self.uid,self.gid,0o600))
            self.assertIn('readable',events)
            events.append('rename')
            return original_replace(source,destination,**options)
        def sync(descriptor):
            events.append('fsync')
            return original_fsync(descriptor)
        def readable(path,uid,gid):
            events.append('readable')
            return True
        with patch.object(operator.os,'replace',rename),patch.object(operator.os,'fsync',sync):
            result=self.publish(readable=readable)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(events[:3],['fsync','readable','rename'])
        self.assertEqual(events[-2:],['fsync','fsync'])
        self.assertEqual(json.loads(self.receipt.read_bytes()),result)
        self.assertNotIn('private-',self.receipt.read_text())

    def test_validation_failure_preserves_old(self):
        with self.assertRaises(operator.PublicationError):self.publish(validate=lambda raw: False)
        self.retained()

    def test_validation_exception_does_not_log_secret(self):
        def validate(raw):raise ValueError(self.new.decode())
        with self.assertRaises(operator.PublicationError) as error:self.publish(validate=validate)
        self.assertNotIn(self.new.decode(),str(error.exception))
        self.retained()

    def test_chown_failure_preserves_old(self):
        with patch.object(operator.os,'fchown',side_effect=PermissionError('private-secret')):
            with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()

    def test_chmod_failure_preserves_old(self):
        with patch.object(operator.os,'fchmod',side_effect=PermissionError('private-secret')):
            with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()

    def test_wrong_temporary_owner_rejected(self):
        actual=operator._metadata
        calls=[]
        def metadata(info,contract):
            calls.append(info)
            return actual(info,contract) and len(calls)!=2
        with patch.object(operator,'_metadata',metadata):
            with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()

    def test_service_cannot_read_temporary_preserves_old(self):
        with self.assertRaises(operator.PublicationError):self.publish(readable=lambda *args:False)
        self.retained()

    def test_rename_failure_preserves_old(self):
        with patch.object(operator.os,'replace',side_effect=OSError('private-secret')):
            with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()

    def test_final_readback_mismatch_is_explicit_post_rename_failure(self):
        actual=operator._read
        calls=[]
        def read(directory,name):
            raw,info=actual(directory,name)
            calls.append(name)
            return (b'private-corrupted',info) if len(calls)==4 else (raw,info)
        with patch.object(operator,'_read',read):
            with self.assertRaises(operator.PublicationError):self.publish()
        result=json.loads(self.receipt.read_bytes())
        self.assertEqual(result['stage'],'final_readback')
        self.assertTrue(result['published'])
        self.assertEqual(result['status'],'FAIL')
        self.assertNotIn('private-',self.receipt.read_text())

    def test_repeated_same_renewal_is_noop(self):
        first=self.publish()
        before=self.target.stat()
        self.receipt=self.receipts/'repeat.json'
        with patch.object(operator.os,'replace',side_effect=AssertionError('must not replace')):
            second=self.publish()
        self.assertEqual(second['status'],'PASS')
        self.assertFalse(second['changed'])
        self.assertEqual(before.st_ino,self.target.stat().st_ino)
        self.assertEqual(first['sha256'],second['sha256'])
        with self.assertRaises(operator.PublicationError):self.publish()

    def test_existing_wrong_contract_rejected(self):
        self.target.chmod(0o640)
        with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()

    def test_parent_mismatch_rejected(self):
        self.contract=replace(self.contract,parent_mode=0o755)
        with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()

    def test_concurrent_target_change_rejected(self):
        def readable(*args):
            with os.fdopen(os.open(self.target,os.O_WRONLY|os.O_TRUNC),'wb') as output:
                output.write(b'concurrent-private-state')
            return True
        with self.assertRaises(operator.PublicationError):self.publish(readable=readable)
        self.assertEqual(self.target.read_bytes(),b'concurrent-private-state')
        self.assertFalse(json.loads(self.receipt.read_bytes())['published'])

    def test_final_service_read_failure_reported(self):
        calls=[]
        def readable(*args):
            calls.append(True)
            return len(calls)==1
        with self.assertRaises(operator.PublicationError):self.publish(readable=readable)
        result=json.loads(self.receipt.read_bytes())
        self.assertTrue(result['published'])
        self.assertEqual(result['stage'],'final_readability')

    def test_temp_fsync_failure_retains_old(self):
        actual=operator.os.fsync
        calls=[]
        def sync(descriptor):
            calls.append(True)
            if len(calls)==1:raise OSError('private-secret')
            return actual(descriptor)
        with patch.object(operator.os,'fsync',sync):
            with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()

    def test_parent_fsync_failure_marks_published_without_success(self):
        actual=operator.os.fsync
        calls=[]
        def sync(descriptor):
            calls.append(True)
            if len(calls)==2:raise OSError('private-secret')
            return actual(descriptor)
        with patch.object(operator.os,'fsync',sync):
            with self.assertRaises(operator.PublicationError):self.publish()
        result=json.loads(self.receipt.read_bytes())
        self.assertEqual(result['stage'],'directory_sync')
        self.assertTrue(result['published'])

    def test_receipt_permission_preflight_retains_old(self):
        self.receipts.chmod(0o755)
        with self.assertRaises(operator.PublicationError):self.publish()
        self.assertEqual(self.target.read_bytes(),self.old)
        self.assertFalse(list(self.parent.glob('*.pending-*')))

    def test_receipt_failure_never_claims_success(self):
        with patch.object(operator,'_receipt',side_effect=OSError('private-secret')):
            with self.assertRaisesRegex(operator.PublicationError,'inspect destination'):self.publish()
        self.assertFalse(self.receipt.exists())

    def test_world_readable_contract_is_rejected(self):
        self.contract=replace(self.contract,mode=0o644)
        with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()


@unittest.skipUnless(os.geteuid()==0,'requires isolated root DAC test')
class IsolatedRootTests(PublicationTests):
    def setUp(self):
        super().setUp()
        accounts=[account for account in pwd.getpwall() if account.pw_uid>0]
        account=accounts[0]
        self.uid,self.gid=account.pw_uid,account.pw_gid
        self.unrelated=next(account for account in accounts if account.pw_uid!=self.uid)
        self.root.chmod(0o755)
        os.chown(self.parent,0,self.gid)
        self.parent.chmod(0o1770)
        os.chown(self.target,self.uid,self.gid)
        self.contract=operator.Contract(self.uid,self.gid,0,self.gid,0o1770)
        self.readable=operator.service_readable

    def test_actual_service_read_and_unrelated_denial(self):
        self.publish()
        self.assertTrue(operator.service_readable(self.target,self.uid,self.gid))
        self.assertFalse(operator.service_readable(self.target,self.unrelated.pw_uid,self.unrelated.pw_gid))

    def test_reproduce_original_root_temporary_rename_loss(self):
        from control.friends.restricted_sync import atomic
        self.assertTrue(operator.service_readable(self.target,self.uid,self.gid))
        atomic(self.target,self.new)
        info=self.target.stat()
        self.assertEqual((info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode)),(0,0,0o600))
        self.assertFalse(operator.service_readable(self.target,self.uid,self.gid))

    def test_actual_wrong_temp_owner_rejected_without_repair(self):
        with patch.object(operator.os,'fchown',return_value=None):
            with self.assertRaises(operator.PublicationError):self.publish()
        self.retained()


if __name__=='__main__':unittest.main()
