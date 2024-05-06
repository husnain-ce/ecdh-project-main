from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization

def generate_server_keys_for_server():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key

def generate_shared_secret_on_server(private_key, peer_public_key):
    peer_public_key = serialization.load_pem_public_key(peer_public_key)
    shared_key = private_key.exchange(ec.ECDH(), peer_public_key)
    # shared_key_string = base64.b64encode(shared_key).decode('utf-8')
    return shared_key

def encrypt_message_on_server(shared_secret, message):
    kdf = X963KDF(algorithm=hashes.SHA256(), length=32, sharedinfo=None)
    derived_key = kdf.derive(shared_secret)
    
    iv = b'0123456789abcdef'
    cipher = Cipher(algorithms.AES(derived_key), modes.CFB(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()
    
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return ciphertext

def decrypt_message_on_server(shared_secret, ciphertext):
    kdf = X963KDF(algorithm=hashes.SHA256(), length=32, sharedinfo=None)
    derived_key = kdf.derive(shared_secret)
    
    iv = b'0123456789abcdef'
    cipher = Cipher(algorithms.AES(derived_key), modes.CFB(iv))
    decryptor = cipher.decryptor()
    
    decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_message = unpadder.update(decrypted_padded_data) + unpadder.finalize()
    
    return decrypted_message.decode()

