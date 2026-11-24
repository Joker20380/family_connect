"""Remove inherited ACLs only inside explicitly created disposable fixture trees."""
import os
from pathlib import Path


def remove_acls(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Fixture root must be a real directory')
    for path in (root, *root.rglob('*')):
        if path.is_symlink():
            continue
        names = set(os.listxattr(path, follow_symlinks=False))
        for name in names & {'system.posix_acl_access', 'system.posix_acl_default'}:
            os.removexattr(path, name, follow_symlinks=False)
