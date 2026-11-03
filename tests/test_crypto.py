import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.crypto import (
    CIPHERS,
    AES256GCMCipher,
    ChaCha20Poly1305Cipher,
    AsconAEAD128Cipher,
    InvalidTag
)


class TestCryptoAEAD(unittest.TestCase):
    def setUp(self):
        self.ciphers = [
            AES256GCMCipher(),
            ChaCha20Poly1305Cipher(),
            AsconAEAD128Cipher()
        ]
        self.payload_sizes = [32, 128, 1024, 4096]

    def test_key_and_nonce_sizes(self):
        """Verify key and nonce length requirements according to standards."""
        # AES-256-GCM: 32B key, 12B nonce
        aes = AES256GCMCipher()
        self.assertEqual(len(aes.generate_key()), 32)
        self.assertEqual(len(aes.generate_nonce()), 12)
        self.assertEqual(aes.tag_size, 16)

        # ChaCha20-Poly1305: 32B key, 12B nonce
        cha = ChaCha20Poly1305Cipher()
        self.assertEqual(len(cha.generate_key()), 32)
        self.assertEqual(len(cha.generate_nonce()), 12)
        self.assertEqual(cha.tag_size, 16)

        # Ascon-AEAD128: 16B key, 16B nonce
        asc = AsconAEAD128Cipher()
        self.assertEqual(len(asc.generate_key()), 16)
        self.assertEqual(len(asc.generate_nonce()), 16)
        self.assertEqual(asc.tag_size, 16)

    def test_invalid_key_and_nonce_rejected(self):
        """Must reject invalid key and nonce lengths."""
        for c in self.ciphers:
            with self.assertRaises(ValueError):
                c.encrypt(b"bad_key", c.generate_nonce(), b"data")
            with self.assertRaises(ValueError):
                c.encrypt(c.generate_key(), b"bad_nonce", b"data")
            with self.assertRaises(TypeError):
                c.encrypt("string_key", c.generate_nonce(), b"data")

    def test_exact_tag_overhead_16_bytes(self):
        """Ciphertext length MUST be exactly len(plaintext) + 16 bytes for all AEADs."""
        for c in self.ciphers:
            for sz in self.payload_sizes:
                pt = os.urandom(sz)
                key = c.generate_key()
                nonce = c.generate_nonce()
                ad = b"metadata-header-ad"
                
                ct = c.encrypt(key, nonce, pt, ad)
                self.assertEqual(
                    len(ct),
                    sz + 16,
                    f"{c.name} overhead mismatch: expected {sz + 16}, got {len(ct)}"
                )

    def test_roundtrip_all_payload_sizes(self):
        """Encrypt and decrypt roundtrip must recover exact original plaintext."""
        for c in self.ciphers:
            for sz in self.payload_sizes:
                pt = os.urandom(sz)
                key = c.generate_key()
                nonce = c.generate_nonce()
                
                # With non-empty associated data
                ad = b"header-test-id-1234"
                ct = c.encrypt(key, nonce, pt, ad)
                recovered = c.decrypt(key, nonce, ct, ad)
                self.assertEqual(recovered, pt, f"{c.name} roundtrip failed on size {sz}")

                # With empty associated data
                ct_empty_ad = c.encrypt(key, nonce, pt, b"")
                recovered_empty = c.decrypt(key, nonce, ct_empty_ad, b"")
                self.assertEqual(recovered_empty, pt, f"{c.name} roundtrip with empty AD failed on size {sz}")

    def test_tampered_ciphertext_detection(self):
        """Modifying any bit in the ciphertext MUST raise InvalidTag."""
        for c in self.ciphers:
            key = c.generate_key()
            nonce = c.generate_nonce()
            pt = b"Critical secure message: transfer $1,000,000"
            ad = b"auth-ad"
            
            ct = bytearray(c.encrypt(key, nonce, pt, ad))
            # Flip a bit in the ciphertext payload
            ct[5] ^= 0x01
            
            with self.assertRaises(InvalidTag, msg=f"{c.name} failed to detect tampered ciphertext"):
                c.decrypt(key, nonce, bytes(ct), ad)

    def test_tampered_tag_detection(self):
        """Modifying any bit in the 16-byte tag MUST raise InvalidTag."""
        for c in self.ciphers:
            key = c.generate_key()
            nonce = c.generate_nonce()
            pt = b"Standard test message"
            ad = b"auth-ad"
            
            ct = bytearray(c.encrypt(key, nonce, pt, ad))
            # Flip a bit in the authentication tag (last 16 bytes)
            ct[-1] ^= 0x01
            
            with self.assertRaises(InvalidTag, msg=f"{c.name} failed to detect tampered tag"):
                c.decrypt(key, nonce, bytes(ct), ad)

    def test_tampered_associated_data_detection(self):
        """Modifying Associated Data MUST fail tag verification on decrypt."""
        for c in self.ciphers:
            key = c.generate_key()
            nonce = c.generate_nonce()
            pt = b"Payload data authenticated with AD"
            ad = b"Algorithm_ID=1;Sender=Alice;Receiver=Bob"
            
            ct = c.encrypt(key, nonce, pt, ad)
            
            # Tamper AD: Eve changes Sender to Mallory
            tampered_ad = b"Algorithm_ID=1;Sender=Mallory;Receiver=Bob"
            
            with self.assertRaises(InvalidTag, msg=f"{c.name} failed to detect tampered Associated Data"):
                c.decrypt(key, nonce, ct, tampered_ad)


if __name__ == '__main__':
    unittest.main()

