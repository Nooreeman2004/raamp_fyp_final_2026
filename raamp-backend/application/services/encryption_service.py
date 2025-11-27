from cryptography.fernet import Fernet
import os


class EncryptionService:
    def __init__(self, key: str = None):
        # Accept key from env or parameter. If none provided, raise — we require a stable key.
        env_key = os.getenv('ENCRYPTION_KEY')
        k = key or env_key
        if not k:
            raise RuntimeError("ENCRYPTION_KEY not set. Please set a 32-byte urlsafe base64 key in env 'ENCRYPTION_KEY'.")
        self.fernet = Fernet(k)

    def encrypt(self, plaintext: str) -> str:
        if plaintext is None:
            return None
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        return self.fernet.encrypt(plaintext).decode('utf-8')

    def decrypt(self, token: str) -> str:
        if token is None:
            return None
        try:
            return self.fernet.decrypt(token.encode('utf-8')).decode('utf-8')
        except Exception:
            return None
