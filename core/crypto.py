"""
core.crypto
===========
Standardized Authenticated Encryption with Associated Data (AEAD) implementations:
- AES-256-GCM (NIST SP 800-38D)
- ChaCha20-Poly1305 (IETF RFC 8439)
- Ascon-AEAD128 (NIST SP 800-232)

All implementations provide:
- Strict `bytes` input and output.
- Exact 16-byte (128-bit) authentication tags appended to ciphertext.
- Robust Associated Data (AD) authentication.
- Unified exception handling (raises InvalidTag on authentication or tampering failure).
- Proper nonce and key generation according to primary specifications.
"""

from abc import ABC, abstractmethod
import os
from typing import Dict, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.exceptions import InvalidTag
from core._ascon_nist import ascon_encrypt, ascon_decrypt


class AuthenticationError(InvalidTag):
    """Raised when AEAD tag verification fails."""
    pass


class AEADCipher(ABC):
    """Abstract Base Class for AEAD ciphers."""
    name: str
    key_size: int      # Key length in bytes
    nonce_size: int    # Nonce length in bytes
    tag_size: int = 16 # Authentication tag length in bytes (128 bits)

    @abstractmethod
    def encrypt(
        self,
        key: bytes,
        nonce: bytes,
        plaintext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        """
        Encrypts plaintext with associated data.
        Returns: ciphertext + 16-byte authentication tag (bytes).
        """
        pass

    @abstractmethod
    def decrypt(
        self,
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        """
        Decrypts ciphertext and verifies authentication tag with associated data.
        Returns: plaintext (bytes).
        Raises: InvalidTag if ciphertext, tag, or associated data are tampered.
        """
        pass

    def generate_key(self) -> bytes:
        """Generates a cryptographically secure random key."""
        return os.urandom(self.key_size)

    def generate_nonce(self) -> bytes:
        """Generates a cryptographically secure random nonce."""
        return os.urandom(self.nonce_size)

    def validate_key(self, key: bytes) -> None:
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError(f"Key must be bytes, got {type(key)}")
        if len(key) != self.key_size:
            raise ValueError(f"{self.name} requires {self.key_size}-byte key, got {len(key)}")

    def validate_nonce(self, nonce: bytes) -> None:
        if not isinstance(nonce, (bytes, bytearray)):
            raise TypeError(f"Nonce must be bytes, got {type(nonce)}")
        if len(nonce) != self.nonce_size:
            raise ValueError(f"{self.name} requires {self.nonce_size}-byte nonce, got {len(nonce)}")


class AES256GCMCipher(AEADCipher):
    """
    AES-256-GCM Authenticated Encryption with Associated Data (NIST SP 800-38D).
    - Key: 32 bytes (256 bits)
    - Nonce: 12 bytes (96 bits standard)
    - Tag: 16 bytes (128 bits)
    """
    name = "AES-256-GCM"
    key_size = 32
    nonce_size = 12
    tag_size = 16

    def encrypt(
        self,
        key: bytes,
        nonce: bytes,
        plaintext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        self.validate_key(key)
        self.validate_nonce(nonce)
        if not isinstance(plaintext, (bytes, bytearray)):
            raise TypeError("Plaintext must be bytes")
        if not isinstance(associated_data, (bytes, bytearray)):
            raise TypeError("Associated data must be bytes")

        aesgcm = AESGCM(key)
        # AESGCM.encrypt appends 16-byte tag to the ciphertext
        return aesgcm.encrypt(nonce, plaintext, associated_data)

    def decrypt(
        self,
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        self.validate_key(key)
        self.validate_nonce(nonce)
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise TypeError("Ciphertext must be bytes")
        if not isinstance(associated_data, (bytes, bytearray)):
            raise TypeError("Associated data must be bytes")
        if len(ciphertext) < self.tag_size:
            raise InvalidTag(f"Ciphertext too short to contain {self.tag_size}-byte tag")

        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, associated_data)


class ChaCha20Poly1305Cipher(AEADCipher):
    """
    ChaCha20-Poly1305 Authenticated Encryption with Associated Data (IETF RFC 8439).
    - Key: 32 bytes (256 bits)
    - Nonce: 12 bytes (96 bits)
    - Tag: 16 bytes (128 bits)
    """
    name = "ChaCha20-Poly1305"
    key_size = 32
    nonce_size = 12
    tag_size = 16

    def encrypt(
        self,
        key: bytes,
        nonce: bytes,
        plaintext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        self.validate_key(key)
        self.validate_nonce(nonce)
        if not isinstance(plaintext, (bytes, bytearray)):
            raise TypeError("Plaintext must be bytes")
        if not isinstance(associated_data, (bytes, bytearray)):
            raise TypeError("Associated data must be bytes")

        cipher = ChaCha20Poly1305(key)
        # ChaCha20Poly1305.encrypt appends 16-byte tag
        return cipher.encrypt(nonce, plaintext, associated_data)

    def decrypt(
        self,
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        self.validate_key(key)
        self.validate_nonce(nonce)
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise TypeError("Ciphertext must be bytes")
        if not isinstance(associated_data, (bytes, bytearray)):
            raise TypeError("Associated data must be bytes")
        if len(ciphertext) < self.tag_size:
            raise InvalidTag(f"Ciphertext too short to contain {self.tag_size}-byte tag")

        cipher = ChaCha20Poly1305(key)
        return cipher.decrypt(nonce, ciphertext, associated_data)


class AsconAEAD128Cipher(AEADCipher):
    """
    Ascon-AEAD128 Lightweight Authenticated Encryption with Associated Data (NIST SP 800-232).
    - Key: 16 bytes (128 bits)
    - Nonce: 16 bytes (128 bits)
    - Tag: 16 bytes (128 bits)
    """
    name = "Ascon-AEAD128"
    key_size = 16
    nonce_size = 16
    tag_size = 16

    def encrypt(
        self,
        key: bytes,
        nonce: bytes,
        plaintext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        self.validate_key(key)
        self.validate_nonce(nonce)
        if not isinstance(plaintext, (bytes, bytearray)):
            raise TypeError("Plaintext must be bytes")
        if not isinstance(associated_data, (bytes, bytearray)):
            raise TypeError("Associated data must be bytes")

        # NIST SP 800-232 Ascon-AEAD128 returns ciphertext + 16-byte tag
        return ascon_encrypt(key, nonce, associated_data, plaintext, variant="Ascon-AEAD128")

    def decrypt(
        self,
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: bytes = b""
    ) -> bytes:
        self.validate_key(key)
        self.validate_nonce(nonce)
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise TypeError("Ciphertext must be bytes")
        if not isinstance(associated_data, (bytes, bytearray)):
            raise TypeError("Associated data must be bytes")
        if len(ciphertext) < self.tag_size:
            raise InvalidTag(f"Ciphertext too short to contain {self.tag_size}-byte tag")

        pt = ascon_decrypt(key, nonce, associated_data, ciphertext, variant="Ascon-AEAD128")
        if pt is None:
            raise InvalidTag("Ascon-AEAD128 authentication tag verification failed")
        return pt


# Global registry mapping standard names and legacy aliases
CIPHERS: Dict[str, AEADCipher] = {
    # Standard names
    "AES-256-GCM": AES256GCMCipher(),
    "ChaCha20-Poly1305": ChaCha20Poly1305Cipher(),
    "Ascon-AEAD128": AsconAEAD128Cipher(),
    # Legacy aliases (for backward compatibility)
    "AES-256": AES256GCMCipher(),
    "ChaCha20": ChaCha20Poly1305Cipher(),
    "ASCON": AsconAEAD128Cipher(),
}


def get_cipher(name: str) -> AEADCipher:
    """Returns the AEADCipher instance for a given algorithm name."""
    if name not in CIPHERS:
        raise KeyError(f"Unknown cipher '{name}'. Available: {list(CIPHERS.keys())}")
    return CIPHERS[name]

