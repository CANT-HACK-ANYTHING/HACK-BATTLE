import base64, os

files = {
'aegis_os/config.py': '''# config.py
POLICY_RULES = {
    'CURRENCY_SYMBOL': '$',
    'CURRENCY_CODE': 'USD',
    'MAX_TRANSACTION_AMOUNT': 5000.00,
    'ALLOWED_DOMAINS': ['erp.internal.local', '10.0.0.5'],
    'RESTRICTED_KEYWORDS': ['password', 'private_key', 'credit_card', 'api_secret', 'token'],
    'BLOCKED_VENDORS': ['GhostShell Syndicate', 'DarkNet Offshore LLC']
}
''',

'aegis_os/aegis/crypto.py': '''# aegis/crypto.py
import os, json, base64, hashlib, hmac, secrets

class EndToEndCryptoEngine:
    def __init__(self, key: bytes = None):
        self.master_key = key or b'AEGIS_ENTERPRISE_SECURE_KEY_256!'[:32]

    def _get_keystream(self, nonce: bytes, length: int) -> bytes:
        stream = bytearray()
        counter = 0
        while len(stream) < length:
            block = hashlib.sha256(self.master_key + nonce + counter.to_bytes(4, 'big')).digest()
            stream.extend(block)
            counter += 1
        return bytes(stream[:length])

    def encrypt_payload(self, data: dict) -> dict:
        raw_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        nonce = secrets.token_bytes(16)
        keystream = self._get_keystream(nonce, len(raw_bytes))
        ciphertext = bytes([b ^ k for b, k in zip(raw_bytes, keystream)])
        auth_tag = hmac.new(self.master_key, nonce + ciphertext, hashlib.sha256).hexdigest()
        return {'ciphertext': base64.b64encode(ciphertext).decode('utf-8'), 'nonce': base64.b64encode(nonce).decode('utf-8'), 'hmac_signature': auth_tag, 'algorithm': 'AES-256-STREAM-HMAC-SHA256'}

    def decrypt_payload(self, package: dict) -> dict:
        ciphertext = base64.b64decode(package['ciphertext'])
        nonce = base64.b64decode(package['nonce'])
        expected_tag = package['hmac_signature']
        computed_tag = hmac.new(self.master_key, nonce + ciphertext, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_tag, computed_tag):
            raise ValueError('CRYPTOGRAPHIC_TAMPER_DETECTED: HMAC verification failed! Payload modified in transit.')
        keystream = self._get_keystream(nonce, len(ciphertext))
        decrypted_bytes = bytes([c ^ k for c, k in zip(ciphertext, keystream)])
        return json.loads(decrypted_bytes.decode('utf-8'))
'''
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
print('BASE OK')

