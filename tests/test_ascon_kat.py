"""
tests.test_ascon_kat
====================
Known-Answer Tests (KAT) for Ascon-AEAD128 against the official NIST SP 800-232 /
NIST Lightweight Cryptography (LWC) test vectors (LWC_AEAD_KAT_128_128.txt).
"""

import unittest
from core.crypto import AsconAEAD128Cipher

NIST_SP800_232_VECTORS = [
    {
        "count": 1,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "",
        "ad": "",
        "ct": "4F9C278211BEC9316BF68F46EE8B2EC6"
    },
    {
        "count": 2,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "",
        "ad": "30",
        "ct": "CCCB674FE18A09A285D6AB11B35675C0"
    },
    {
        "count": 5,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "",
        "ad": "30313233",
        "ct": "000BA92E52B5ED6B97C9D913CC4C82DF"
    },
    {
        "count": 34,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "20",
        "ad": "",
        "ct": "E8DD576ABA1CD3E6FC704DE02AEDB79588"
    },
    {
        "count": 35,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "20",
        "ad": "30",
        "ct": "962B8016836C75A7D86866588CA245D886"
    },
    {
        "count": 67,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "2021",
        "ad": "",
        "ct": "E8C35A12D2A396E76224F6EE5418F6465197"
    },
    {
        "count": 100,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "202122",
        "ad": "",
        "ct": "E8C3DEAF8E12816B8EDF39AD1571A9492B7CA2"
    },
    {
        "count": 250,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "20212223242526",
        "ad": "303132333435363738393A3B3C3D3E3F4041",
        "ct": "B3B05F0A08C5769CCCC489FA07B844EF5F21E1712844CB"
    },
    {
        "count": 500,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "202122232425262728292A2B2C2D2E",
        "ad": "30313233",
        "ct": "CF5337FCB70EC45D179E0C3F51BB256429C3D7D02FCC989BE215B45CA38F36"
    },
    {
        "count": 1000,
        "key": "000102030405060708090A0B0C0D0E0F",
        "nonce": "101112131415161718191A1B1C1D1E1F",
        "pt": "202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D",
        "ad": "303132333435363738",
        "ct": "BF79D7476D6FB05B8891A079BE8A1992B63FFE31062DC7AAE254516F0860A895946CDD7001544DBC0F430A3DF552"
    }
]

class TestAsconKAT(unittest.TestCase):
    def setUp(self):
        self.cipher = AsconAEAD128Cipher()

    def test_nist_sp800_232_kat_vectors(self):
        for vec in NIST_SP800_232_VECTORS:
            count = vec['count']
            key = bytes.fromhex(vec['key'])
            nonce = bytes.fromhex(vec['nonce'])
            pt = bytes.fromhex(vec['pt']) if vec['pt'] else b''
            ad = bytes.fromhex(vec['ad']) if vec['ad'] else b''
            expected_ct = bytes.fromhex(vec['ct'])

            # 1. Test Encryption
            ct = self.cipher.encrypt(key, nonce, pt, ad)
            self.assertEqual(
                ct, expected_ct,
                f"KAT failed on Count {count} (Encrypt)"
            )

            # 2. Test Decryption & Authentication Tag
            dec_pt = self.cipher.decrypt(key, nonce, ct, ad)
            self.assertEqual(
                dec_pt, pt,
                f"KAT failed on Count {count} (Decrypt)"
            )

if __name__ == '__main__':
    unittest.main()
