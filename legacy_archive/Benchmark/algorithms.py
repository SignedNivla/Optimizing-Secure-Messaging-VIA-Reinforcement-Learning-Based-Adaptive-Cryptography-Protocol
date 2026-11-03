from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305 as authchacha20
import ascon
from abc import ABC,abstractmethod
import os
import base64

class EncryptionAlgorithm(ABC):
    def __init__(self,key,nonce):
        self._key = key
        self._nonce = nonce
    @abstractmethod
    def encrypt(self,plain_text):
        pass
    @abstractmethod
    def decrypt(self,cipher_text):
        pass

class ChaCha20Algorithm(EncryptionAlgorithm):
    def encrypt(self, plain_text:str) -> bytes:
        cipher = Cipher(algorithms.ChaCha20(self._key,self._nonce),mode=None,backend=default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(plain_text.encode()) + encryptor.finalize()
    def decrypt(self, cipher_text:str) -> str:
        cipher = Cipher(algorithms.ChaCha20(self._key,self._nonce),mode=None,backend=default_backend())
        decryptor = cipher.decryptor()
        plain_text = decryptor.update(cipher_text) + decryptor.finalize()
        return plain_text.decode('utf-8')
    def generate_random_key(self):
        self._key = os.urandom(32)
    def generate_random_nonce(self):
        self._nonce = os.urandom(12)

class AES256Algorithm(EncryptionAlgorithm):
    def encrypt(self, plain_text:str) -> bytes:
        iv = os.urandom(16)
        cipher = Cipher(algorithm=algorithms.AES(self._key),mode=modes.CFB(iv),backend=default_backend())
        encryptor = cipher.encryptor()
        cipher_text = encryptor.update(plain_text.encode()) + encryptor.finalize()
        return base64.b64encode(iv+cipher_text).decode('utf-8')
    def decrypt(self, cipher_text) -> str:
        cipher_text_bytes = base64.b64decode(cipher_text)
        iv = cipher_text_bytes[:16]
        cipher_text = cipher_text_bytes[16:]
        cipher = Cipher(algorithm=algorithms.AES(self._key),mode=modes.CFB(iv),backend=default_backend())
        decryptor = cipher.decryptor()
        plain_text = decryptor.update(cipher_text)+decryptor.finalize()

        return plain_text.decode('utf-8')
    def generate_random_key(self):
        self._key = os.urandom(32)
    
class AuthEncryptionAlgorithm(EncryptionAlgorithm):
    def __init__(self, key, nonce,associated_data):
        super().__init__(key, nonce)
        self._associated_data = associated_data

class ChaCha20Poly1305Algorithm(AuthEncryptionAlgorithm):
    def encrypt(self, plain_text:str):
        aead = authchacha20(self._key)
        return aead.encrypt(self._nonce,plain_text.encode(),self._associated_data)
    def decrypt(self, cipher_text:bytes):
        aead = authchacha20(self._key)
        plain_text:bytes =  aead.decrypt(nonce = self._nonce,plaintext=cipher_text,associated_data=self._associated_data)
        return plain_text.decode('utf-8')
    def generate_random_key(self):
        self._key = os.urandom(32)
    def generate_random_nonce(self):
        self._nonce = os.urandom(12)

class AsconAlgorithm(AuthEncryptionAlgorithm):
    def encrypt(self, plain_text:str) ->bytes:
        cipher_text = ascon.encrypt(self._key,self._nonce,self._associated_data,plain_text.encode())
        return cipher_text
    def decrypt(self, cipher_text:bytes) -> str:
        plain_text = ascon.decrypt(self._key,self._nonce,self._associated_data,cipher_text)
        return plain_text.decode('utf-8')
    def generate_random_key(self):
        self._key = os.urandom(16)
    def generate_random_nonce(self):
        self._nonce = os.urandom(16)