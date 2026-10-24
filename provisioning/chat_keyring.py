"""Linux chat storage keys belong to the user's Secret Service, never a key file."""
import base64
import os
import threading


class KeyringUnavailable(Exception):
    pass


class ChatKeyring:
    def key(self, device, *, create):
        try:
            import gi
            gi.require_version('Secret', '1')
            from gi.repository import Gio, Secret
        except (ImportError, ValueError):
            raise KeyringUnavailable('keyring_unavailable') from None
        schema = Secret.Schema.new('com.familyconnect.ChatKey.v1', Secret.SchemaFlags.NONE,
                                   {'device': Secret.SchemaAttributeType.STRING})
        attributes = {'device': device}
        cancel = Gio.Cancellable()
        timer = threading.Timer(15, cancel.cancel)
        timer.daemon = True
        timer.start()
        try:
            service = Secret.Service.open_sync(Secret.Service.__gtype__, 'org.freedesktop.secrets',
                                               Secret.ServiceFlags.OPEN_SESSION, cancel)
            stored = service.lookup_sync(schema, attributes, cancel)
            encoded = stored.get_text() if stored is not None else None
            if encoded is None:
                if not create or service.search_sync(schema, attributes, Secret.SearchFlags.ALL, cancel):
                    raise KeyringUnavailable('keyring_unavailable')
                encoded = base64.b64encode(os.urandom(32)).decode('ascii')
                secret = Secret.Value.new(encoded, -1, 'text/plain')
                if not service.store_sync(schema, attributes, Secret.COLLECTION_DEFAULT,
                                          'Family Connect encrypted chat history', secret, cancel):
                    raise KeyringUnavailable('keyring_unavailable')
                stored = service.lookup_sync(schema, attributes, cancel)
                if stored is None or stored.get_text() != encoded:
                    raise KeyringUnavailable('keyring_unavailable')
            key = base64.b64decode(encoded, validate=True)
            if len(key) != 32:
                raise KeyringUnavailable('keyring_unavailable')
            return key
        except Exception:
            raise KeyringUnavailable('keyring_unavailable') from None
        finally:
            timer.cancel()
