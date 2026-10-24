"""Auto-specific memory contract using the existing sealed systemd FD store."""
import auto_ipc
from mesh_intent import Intent


class AutoIntent(Intent):
    name, limit = 'fc-auto-intent-v1', 32768

    @staticmethod
    def validate(materials):
        auto_ipc.selection(materials)
