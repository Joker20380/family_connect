"""Operator-only ENOSPC acceptance inside an isolated, networkless container.

Input must be a disposable preformatted ext4 FILE mounted into /lab/relay.ext4.
Never pass a block device or production volume. Container needs mount capability.
"""
import errno
import json
import os
from pathlib import Path
import stat
import subprocess

from messenger.relay import Spool,SpoolFull


def main():
    image=Path('/lab/relay.ext4');info=image.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size!=16*1024*1024:
        raise ValueError('Expected disposable 16MiB regular image file')
    root=Path('/mnt/fc-relay-check');root.mkdir(mode=0o700)
    mounted=False;spool=None
    try:
        subprocess.run(['mount','-o','loop,nodev,nosuid,noexec',str(image),str(root)],check=True)
        mounted=True
        spool=Spool(root/'spool',max_bytes=1048576,max_messages=1000,sender_bytes=1048576,sender_messages=1000)
        sender=b's'*16;recipient=b'r'*16
        first=recipient+os.urandom(4784)
        ident=spool.put(sender,first)
        filler=root/'synthetic-rns-cache'
        fd=os.open(filler,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        enospc=False
        try:
            for _ in range(4096):
                os.write(fd,b'x'*4096)
                os.fsync(fd)
        except OSError as error:
            if error.errno!=errno.ENOSPC:raise
            enospc=True
        finally:os.close(fd)
        assert enospc,'Filesystem did not enforce image size'
        accepted=False
        try:spool.put(sender,recipient+os.urandom(4784));accepted=True
        except SpoolFull:pass
        assert not accepted,'Full-volume insertion incorrectly acknowledged'
        assert spool.get(recipient,[[ident],[]])==[first]
        filler.unlink()
        spool.put(sender,recipient+os.urandom(4784))
        assert spool.stats()['count']==2
        spool.close();spool=None
        reopened=Spool(root/'spool',max_bytes=1048576,max_messages=1000,sender_bytes=1048576,sender_messages=1000)
        try:assert reopened.stats()['count']==2
        finally:reopened.close()
        print(json.dumps(dict(volume_bytes=info.st_size,enospc=True,false_ack=False,
                              previous_message_preserved=True,recovery_and_reopen=True)))
    finally:
        if spool is not None:spool.close()
        if mounted:subprocess.run(['umount',str(root)],check=True)


if __name__=='__main__':main()
