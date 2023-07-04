#!/usr/bin/env python3

import logging
import os
import re
import xml.etree.cElementTree as Xml
from binascii import hexlify
from typing import List, Set

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad

from obfuscapk import obfuscator_category
from obfuscapk import util
from obfuscapk.obfuscation import Obfuscation


class DrawableEncryption(obfuscator_category.IEncryptionObfuscator):
    def __init__(self):
        self.logger = logging.getLogger(
            "{0}.{1}".format(__name__, self.__class__.__name__)
        )
        super().__init__()

        self.encryption_secret = "This-key-need-to-be-32-character"

    def obfuscate(self, obfuscation_info: Obfuscation):
        self.logger.info('Running "{0}" obfuscator'.format(self.__class__.__name__))

        with open(os.path.join(os.path.dirname(obfuscation_info.get_smali_files()[0]), 'EncAssetFileDescriptor.smali'), 'w+') as handle:
            handle.write(util.get_decrypt_drawable_smali_code(obfuscation_info.encryption_secret))
            self.logger.warn('ENC_DRAWABLE copy pi to %s', os.path.join(os.path.dirname(obfuscation_info.get_smali_files()[0]), 'EncAssetFileDescriptor.smali'));

        self.encryption_secret = obfuscation_info.encryption_secret
        try:

            encryption_files = {}

            for base, dirs, files in os.walk(obfuscation_info.get_resource_directory()):
                for filename in files:
                    filepath = os.path.join(base, filename)
                    if filename.endswith('.gif') and 'drawable' in base:
                        encryption_files[filepath] = filename

            aes = AES.new(key=self.encryption_secret.encode(), mode=AES.MODE_ECB)
            for res_file, res_filename in util.show_list_progress(
                list(encryption_files.items()),
                interactive=obfuscation_info.interactive,
                description="Encrypting res files %d" % len(encryption_files),
            ):
                with open(res_file, 'rb') as handle:
                   content = pad(handle.read(), AES.block_size)
                encrypted_content = aes.encrypt(content)
                with open(res_file, 'w+b') as handle:
                    handle.write(encrypted_content)
                    self.logger.warn('ENC_DRAWABLE encrypted %s', res_file)

            string_res_field_pattern = re.compile(r"invoke-virtual \{(\w+), (\w+)\}, Landroid\/content\/res\/Resources;->openRawResourceFd\(I\)Landroid\/content\/res\/AssetFileDescriptor;", re.UNICODE)
            move_result_object_pattern = re.compile(r"move-result-object (\w+)", re.UNICODE)
            for smali_file in util.show_list_progress(
                obfuscation_info.get_smali_files(),
                interactive=obfuscation_info.interactive,
                description="Encrypting drawable resources",
            ):
                with open(smali_file, "r", encoding="utf-8") as current_file:
                    lines = current_file.readlines()

                append_lines = {}

                invoke_virtual_call = None
                for line_number, line in enumerate(lines):
                    match = string_res_field_pattern.match(line.strip())
                    if match:
                        reg1, reg2 = match.groups()[0], match.groups()[1]
                        self.logger.warn('ENC_DRAWABLE found %s', smali_file)
                        self.logger.warn('ENC_DRAWABLE %s', line)
                        self.logger.warn('ENC_DRAWABLE regs %s %s', reg1, reg2)
                        invoke_virtual_call = (line, reg1, reg2)
                    elif invoke_virtual_call:
                        match = move_result_object_pattern.match(line.strip())
                        if match:
                            reg = match.groups()[0]
                            self.logger.warn('ENC_DRAWABLE move-result-object reg %s', reg)
                            self.logger.warn('ENC_DRAWABLE call %s', invoke_virtual_call)
                            new_lines = [
                                'invoke-static {%s, %s}, Lpi/EncAssetFileDescriptor;->enc(Landroid/content/res/AssetFileDescriptor;I)Landroid/content/res/AssetFileDescriptor;' % (reg, invoke_virtual_call[2]),
                                'move-result-object %s' % reg
                            ]
                            self.logger.warn('ENC_DRAWABLE new lines')
                            for l in new_lines:
                                self.logger.warn('ENC_DRAWABLE %s', l)
                            append_lines[line_number] = new_lines
                            invoke_virtual_call = None
                        elif len(line.strip()) > 0 and not line.strip().startswith('.'):
                            self.logger.warn('ENC_DRAWABLE clear %s', invoke_virtual_call)
                            self.logger.warn('ENC_DRAWABLE clear %s', line)
                            invoke_virtual_call = None

                if len(append_lines) > 0:
                    with util.inplace_edit_file(smali_file) as (rf, wf):
                        line_number = 0
                        for line in rf:
                            wf.write('%s\n' % line)
                            if line_number in append_lines.keys():
                                for new_line in append_lines[line_number]:
                                    wf.write('%s\n' % new_line)
                            line_number += 1

        except Exception as e:
            self.logger.error(
                'Error during execution of "{0}" obfuscator: {1}'.format(
                    self.__class__.__name__, e
                )
            )
            raise

        finally:
            obfuscation_info.used_obfuscators.append(self.__class__.__name__)
