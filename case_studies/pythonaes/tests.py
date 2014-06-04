#!/usr/bin/env python
"""
Demonstration the pythonaes package. Requires Python 2.6 or 3.x

This program was written as a test. It should be reviewed before use on classified material.
You should also keep a copy of your original file after it is encrypted, all of my tests were
able to get the file back 100% in tact and identical to the original. 

___This is a demo program. Do not use in production*___

The method for creating the key and iv from a password is something that I made up, not an industry standard.
    There are 256 bits of salt pulled from OS's cryptographically strong random source.
    Any specific password will generate 2^128 different Keys.
    Any specific password will generate 2^128 different IVs independent of Key

On decryption, salt is read from first 32 bytes of encrypted file.

In the encrypted file, after salt(if present), are 4 bytes* representing file size. 4GB file size limit.
It would also take quite a while to process 4GB.

* For different sizes of 'L' (unsigned long) the size of the header will change causing incompatibility for
files encrypted/decrypted on a 64 bit system vs 32 bit. This could be resolved with a strict header format that 
is checksummed among other things, but this is a demo/test harness. It will work in that capacity and this does 
not affect the aespython module. This will often cause trailing blocks < 16 bytes to be truncated during
decryption.

Copyright (c) 2010, Adam Newman http://www.caller9.com/
Licensed under the MIT license http://www.opensource.org/licenses/mit-license.php
"""
from __future__ import print_function
__author__ = "Adam Newman"

import os
import hashlib
import struct
import getopt
import sys
import time

from aespython import key_expander, aes_cipher, cbc_mode

class AESdemo:
    def __init__(self):
        self._salt = None
        self._iv = None
        self._key = None
        self._python3 = sys.version_info > (3, 0)
    
    def new_salt(self):
        self._salt = os.urandom(32)
    
    def set_iv(self, iv):
        self._iv = iv
    
    def set_key(self, key):
        self._key = key
    
    def hex_string_to_int_array(self, hex_string):
        result = []
        for i in range(0,len(hex_string),2):
            result.append( int( hex_string[i:i+2], 16))
        return result
    
    def create_key_from_password(self, password):
        if self._salt is None:
            return
        sha512 = hashlib.sha512(password.encode('utf-8') + self._salt[:16]).digest()
        self._key = bytearray(sha512[:32])
        self._iv = [i ^ j for i, j in zip(bytearray(self._salt[16:]), bytearray(sha512[32:48]))]
    
    def fix_bytes(self, byte_list):
        #bytes function is broken in python < 3. It appears to be an alias to str()
        #Either that or I have insufficient magic to make it work properly. Calling bytes on my
        #array returns a string of the list as if you fed the list to print() and captured stdout
        if self._python3:
            return bytes(byte_list)
        tmpstr=''
        for i in byte_list:
            tmpstr += chr(i)
        return tmpstr
    
    def decrypt_file(self, in_file_path, out_file_path, password = None):
        with open(in_file_path, 'rb') as in_file:
            
            #If a password is provided, generate key and iv using salt from file.
            if password is not None:
                self._salt = in_file.read (32)
                self.create_key_from_password (password)
            
            #Key and iv have not been generated or provided, bail out
            if self._key is None or self._iv is None:
                return False
            
            #Initialize encryption using key and iv
            key_expander_256 = key_expander.KeyExpander(256)
            expanded_key = key_expander_256.expand(self._key)
            aes_cipher_256 = aes_cipher.AESCipher(expanded_key)
            aes_cbc_256 = cbc_mode.CBCMode(aes_cipher_256, 16)
            aes_cbc_256.set_iv(self._iv)
            
            #Read original file size
            filesize = struct.unpack('L',in_file.read(struct.calcsize('L')))[0]
            
            #Decrypt to eof
            with open(out_file_path, 'wb') as out_file:
                eof = False
                
                while not eof:
                    in_data = in_file.read(16)
                    if len(in_data) == 0:
                        eof = True
                    else:
                        out_data = aes_cbc_256.decrypt_block(list(bytearray(in_data)))
                        #At end of file, if end of original file is within < 16 bytes slice it out.
                        if filesize - out_file.tell() < 16:
                            out_file.write(self.fix_bytes(out_data[:filesize - out_file.tell()]))
                        else:
                            out_file.write(self.fix_bytes(out_data))
                    
        
        self._salt = None
        return True
        
    def encrypt_file(self, in_file_path, out_file_path, password = None):        
        #If a password is provided, generate new salt and create key and iv
        if password is not None:
            self.new_salt()
            self.create_key_from_password(password)
        else:
            self._salt = None
        
        #If key and iv are not provided are established above, bail out.
        if self._key is None or self._iv is None:
            return False
        
        #Initialize encryption using key and iv
        key_expander_256 = key_expander.KeyExpander(256)
        expanded_key = key_expander_256.expand(self._key)
        aes_cipher_256 = aes_cipher.AESCipher(expanded_key)
        aes_cbc_256 = cbc_mode.CBCMode(aes_cipher_256, 16)
        aes_cbc_256.set_iv(self._iv)
        
        #Get filesize of original file for storage in encrypted file
        try:
            filesize = os.stat(in_file_path)[6]
        except:
            return False

        with open(in_file_path, 'rb') as in_file:
            with open(out_file_path, 'wb') as out_file:
                #Write salt if present
                if self._salt is not None:
                    out_file.write(self._salt)
                
                #Write filesize of original
                out_file.write(struct.pack('L',filesize))
                
                #Encrypt to eof
                eof = False
                while not eof:
                    in_data = in_file.read(16)
                    if len(in_data) == 0:
                        eof = True
                    else:
                        out_data = aes_cbc_256.encrypt_block(bytearray(in_data))
                        out_file.write(self.fix_bytes(out_data))                        
                
        self._salt = None
        return True

def usage():
    print('AES Demo.py usage:')
    print('-u \t\t\t\t Run unit tests.')
    print('-d \t\t\t\t Use decryption mode.')
    print('-i INFILE   or --in=INFILE \t Specify input file.')
    print('-o OUTFILE  or --out=OUTFILE \t Specify output file.')
    print('-p PASSWORD or --pass=PASSWORD \t Specify password. precludes key/iv')
    print('-k HEXKEY   or --key=HEXKEY \t Provide 256 bit key manually. Requires iv.')
    print('-v HEXIV    or --iv=HEXIV \t Provide 128 bit IV manually. Requires key.')

def unittests():
    import unittest
    from aespython import cfb_mode, ofb_mode
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(key_expander.TestKeyExpander))
    suite.addTest(unittest.makeSuite(aes_cipher.TestCipher))
    suite.addTest(unittest.makeSuite(cbc_mode.TestEncryptionMode))
    suite.addTest(unittest.makeSuite(cfb_mode.TestEncryptionMode))
    suite.addTest(unittest.makeSuite(ofb_mode.TestEncryptionMode))
    
    return not unittest.TextTestRunner(verbosity = 2).run(suite).wasSuccessful()
    
def main():
    
    if sys.version_info < (2,6):
        print ('Requires Python 2.6 or greater')
        sys.exit(1)
    
    if len(sys.argv) < 2:
        usage()
        sys.exit(2)
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'udk:v:i:o:p:', ['key=','iv=','in=','out=','pass='])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    
    in_file = None
    out_file = None
    key = None
    iv = None
    password = None
    decrypt = False
    
    demo = AESdemo()
    for o, a in opts:
        if o == '-u':            
            sys.exit(unittests())
        elif o == '-d':
            decrypt=True
        elif o in ('-i','--in'):
            in_file = a
        elif o in ('-o','--out'):
            out_file = a
        elif o in ('-k','--key'):
            key = demo.hex_string_to_int_array(a)            
        elif o in ('-v','--iv'):
            iv = demo.hex_string_to_int_array(a)            
        elif o in ('-p','--pass'):
            password = a
    
    if (key is None and password is None) or (key is not None and password is not None):
        print('provide either key and iv or password')
        sys.exit(2)
    elif key is not None and iv is None:
        print('iv must be provided with key')
        sys.exit(2)
    elif key is not None:
        demo.set_key(key)
        demo.set_iv(iv)
    
    if in_file is None or out_file is None:
        print('Both input and output filenames are required')
        sys.exit(2)
    
    start = time.time()
    if decrypt:
        print ('Decrypting', in_file, 'to', out_file)
        demo.decrypt_file( in_file, out_file, password)
    else:
        print ('Encrypting', in_file, 'to', out_file)
        demo.encrypt_file( in_file, out_file, password)
    end = time.time()
    
    print('Time',end - start,'s')
    
if __name__ == "__main__":
    sys.exit(unittests())
#    main()
