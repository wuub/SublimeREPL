# -*- coding: utf-8 -*-
#
#  Copyright 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

### Cropped by Wojciech Bederski for a stupid license manager :) 

__author__ = "Sybren Stuvel, Marloes de Boer, Ivo Tamboer, and Barry Mead"
__date__ = "2011-08-07"
__version__ = '3.0.1'


import hashlib
import os
import binascii
import types

# ASN.1 codes that describe the hash algorithm used.
HASH_ASN1 = {
    'SHA-256': '\x30\x31\x30\x0d\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04\x20',
}

HASH_METHODS = {
    'SHA-256': hashlib.sha256,
}

class CryptoError(Exception):
    '''Base class for all exceptions in this module.'''


class VerificationError(CryptoError):
    '''Raised when verification fails.'''


import math

def bit_size(number):
    if number < 0:
        raise ValueError('Only nonnegative numbers possible: %s' % number)

    if number == 0:
        return 1
    bits = 0
    while number:
        bits += 1
        number >>= 1
    return bits


def yield_fixedblocks(infile, blocksize):
    while True:
        block = infile.read(blocksize)

        read_bytes = len(block)
        if read_bytes == 0:
            break

        yield block

        if read_bytes < blocksize:
            break

def byte_size(number):
    return int(math.ceil(bit_size(number) / 8.0))

def bytes2int(bytes):
    return int(binascii.hexlify(bytes), 16)

def int2bytes(number, block_size=None):
    # Type checking
    if type(number) not in (types.LongType, types.IntType):
        raise TypeError("You must pass an integer for 'number', not %s" %
            number.__class__)

    if number < 0:
        raise ValueError('Negative numbers cannot be used: %i' % number)

    # Do some bounds checking
    if block_size is not None:
        needed_bytes = byte_size(number)
        if needed_bytes > block_size:
            raise OverflowError('Needed %i bytes for number, but block size '
                'is %i' % (needed_bytes, block_size))
    
    # Convert the number to bytes.
    bytes = []
    while number > 0:
        bytes.insert(0, chr(number & 0xFF))
        number >>= 8

    # Pad with zeroes to fill the block
    if block_size is not None:
        padding = (block_size - needed_bytes) * '\x00'
    else:
        padding = ''

    return padding + ''.join(bytes)

def assert_int(var, name):

    if type(var) in (types.IntType, types.LongType):
        return

    raise TypeError('%s should be an integer, not %s' % (name, var.__class__))


def decrypt_int(cyphertext, dkey, n):
    if type(cyphertext) not in (types.IntType, types.LongType):
        raise TypeError('cyphertext should be an integer, not %s' %
                cyphertext.__type__)

    assert_int(cyphertext, 'cyphertext')
    assert_int(dkey, 'dkey')
    assert_int(n, 'n')

    message = pow(cyphertext, dkey, n)
    return message


def verify(message, signature, pub_key):    
    blocksize = byte_size(pub_key.n)
    encrypted = bytes2int(signature)
    decrypted = decrypt_int(encrypted, pub_key.e, pub_key.n)
    clearsig = int2bytes(decrypted, blocksize)

    # If we can't find the signature  marker, verification failed.
    if clearsig[0:2] != '\x00\x01':
        raise VerificationError('Verification failed')
    
    # Find the 00 separator between the padding and the payload
    try:
        sep_idx = clearsig.index('\x00', 2)
    except ValueError:
        raise VerificationError('Verification failed')
    
    # Get the hash and the hash method
    (method_name, signature_hash) = _find_method_hash(clearsig[sep_idx+1:])
    message_hash = _hash(message, method_name)

    # Compare the real hash to the hash in the signature
    if message_hash != signature_hash:
        raise VerificationError('Verification failed')

def _hash(message, method_name):
    if method_name not in HASH_METHODS:
        raise ValueError('Invalid hash method: %s' % method_name)
    
    method = HASH_METHODS[method_name]
    hasher = method()

    if hasattr(message, 'read') and hasattr(message.read, '__call__'):
        # read as 1K blocks
        for block in yield_fixedblocks(message, 1024):
            hasher.update(block)
    else:
        # hash the message object itself.
        hasher.update(message)

    return hasher.digest()


def _find_method_hash(method_hash):
    for (hashname, asn1code) in HASH_ASN1.iteritems():
        if not method_hash.startswith(asn1code):
            continue
        
        return (hashname, method_hash[len(asn1code):])
    
    raise VerificationError('Verification failed')


class PubKey(object):
    def __init__(self, n, e):
        self.n = n
        self.e = e


def verify_license(blic):
    def init():
        return PubKey(6800123415740686819844898476096532361399516873643257914936867846584564974484284268021254266396087771047862929697992936322281613822324825792389152040217779L, 65537)
    import base64
    try:
        lic = base64.b64decode(blic)
        (name, sig) = lic.split("=|=", 1)
        verify(name, sig, init())
        return True, name.decode("utf-8")
    except:
        return False, None

__all__ = [verify_license]

