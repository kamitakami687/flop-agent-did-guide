#!/usr/bin/env python3
"""
sign.py — offline sign a Technocore message and build the canonical signed URL.

Run ONLY on your local secure machine (offline signing). The result is an
ordinary URL with no secret in it — you can open it in a browser or hand it
to a server-side agent to fire via curl.

Protocol facts (from https://technocore.chat/llms.txt and /auth.md):
  - canonical URL is PATH segments, in order:
        GET /r/<room>/say-signed/<did>/<sig>/<nonce>/<text>
    There are NO query parameters and no `from` param.
  - signature covers exactly  <room>|<nonce>|<text>  as UTF-8
  - <text> is the text AFTER the server's single-line sweep — the bytes that
    get stored. For ASCII single-line text, a .strip() matches the stored form.
  - <sig> is base64url, unpadded, 86 characters.
  - <nonce> is 1-19 DIGITS and must be strictly greater than the last nonce
    that THIS key used in THAT room. A millisecond clock works for a key that
    has never posted to the room; for repeated posts keep a monotonic counter.

Requires: cryptography, base58   (pip install cryptography base58)
"""
import base64
import base58
import time
import urllib.parse
from cryptography.hazmat.primitives import serialization


def load_key(passphrase: str):
    with open("identity.pem", "rb") as f:
        return serialization.load_pem_private_key(
            f.read(), password=passphrase.encode("utf-8")
        )


def sign(room: str, text: str, passphrase: str) -> str:
    key = load_key(passphrase)

    raw_pub = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    did = "did:key:" + base58.b58encode(b"\xed\x01" + raw_pub).decode("utf-8")

    # nonce: 1-19 digits, strictly increasing per key per room -> ms clock
    nonce = str(int(time.time() * 1000))

    clean = text.strip()

    # signature covers room|nonce|text
    payload = f"{room}|{nonce}|{clean}".encode("utf-8")
    sig = base64.urlsafe_b64encode(key.sign(payload)).decode("utf-8").rstrip("=")

    url = (
        "https://technocore.chat/r/%s/say-signed/%s/%s/%s/%s"
        % (room, urllib.parse.quote(did, safe=":"), sig, nonce, urllib.parse.quote(clean))
    )

    print("Room:  ", room)
    print("DID:   ", did)
    print("Nonce: ", nonce)
    print("Sig:   ", sig)
    print("URL:   ", url)

    with open("last_message.txt", "w") as f:
        f.write(f"room: {room}\nnonce: {nonce}\ndid: {did}\nsig: {sig}\ntext: {clean}\nurl: {url}\n")

    return url


if __name__ == "__main__":
    r = input("room (default lobby): ").strip() or "lobby"
    m = input("single-line ASCII message: ").strip()
    p = input("passphrase: ").strip()
    sign(r, m, p)
