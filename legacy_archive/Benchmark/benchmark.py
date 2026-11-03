
from algorithms import EncryptionAlgorithm,AES256Algorithm,ChaCha20Algorithm,AsconAlgorithm
import time
import os

def benchmark(algorithm:EncryptionAlgorithm,message, iteration = 1000):
    st = time.perf_counter()
    for _ in range(iteration):
        ct = algorithm.encrypt(message)
        pt = algorithm.decrypt(ct)
    et = time.perf_counter()
    if pt != message:
        return -1,-1
    return {
        "base_cost":(et-st)/iteration,
        "overhead":len(ct)/len(pt)
    }

key = os.urandom(32)
nonce = os.urandom(16)

message = {
    "low":"This is exactly 30 bytes long.",
    "medium":"This sentence is exactly fifty bytes long in size.",
    "large":"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in r "
}

def get_benchmark(size):
    pt = message[size]
    ad = b"ID-001"
    result = {
        "AES-256":benchmark(AES256Algorithm(key,nonce),pt),
        "ChaCha20":benchmark(ChaCha20Algorithm(key,nonce),pt),
        "ASCON":benchmark(AsconAlgorithm(os.urandom(16),nonce,ad),pt)
    }
    return result