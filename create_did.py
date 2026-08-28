#!/usr/bin/env python3
"""
create_did.py — generate an encrypted Ed25519 identity and a public did:key.

Run ONLY on your local secure machine. The private key (identity.pem) never
leaves this machine. Run on the server is forbidden by the project BRIEF.

Requires: cryptography, base58   (pip install cryptography base58)

Output:
  identity.pem   encrypted PKCS8 Ed25519 private key (passphrase-protected)
  did.txt        public did:key:z6Mk...  (safe to share)
"""
import base58
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_agent_identity(password: str) -> None:
    private_key = ed25519.Ed25519PrivateKey.generate()

    raw_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    # did:key multicodec prefix for ed25519-pub is 0xed 0x01
    multicodec_pub = b"\xed\x01" + raw_public
    did_key = "did:key:" + base58.b58encode(multicodec_pub).decode("utf-8")

    encryption_algo = serialization.BestAvailableEncryption(password.encode("utf-8"))
    pem_data = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algo,
    )

    with open("identity.pem", "wb") as f:
        f.write(pem_data)
    with open("did.txt", "w") as f:
        f.write(did_key)

    print("[+] Identity generated successfully!")
    print(f"[+] Public DID: {did_key}")
    print("[!] Keep 'identity.pem' and your passphrase safe and offline.")


if __name__ == "__main__":
    passphrase = input("Enter a secure passphrase (12+ chars): ").strip()
    if len(passphrase) < 12:
        print("[-] Passphrase must be at least 12 characters.")
    else:
        generate_agent_identity(passphrase)
