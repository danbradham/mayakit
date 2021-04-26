# -*- coding: utf-8 -*-
from __future__ import print_function

import re
from collections import defaultdict

from maya import mel


__all__ = ['MelProcCallback', 'get_mel_proc_data']


class MelProcCallback(object):
    '''
    Maintains a registry of python callbacks for mel global procedures.
    '''

    _registry = defaultdict(list)
    _hook_tmpl_no_params = ('python("from mayakit.callbacks import MelProcCallback; MelProcCallback.execute(\'{}\')");')
    _hook_tmpl = ('python("from mayakit.callbacks import MelProcCallback; MelProcCallback.execute(\'{}\', \'" + {} + "\')");')
    _proc_cache = {}

    @classmethod
    def add(cls, mel_proc, callback):
        '''Add callback to mel procedure'''

        if mel_proc not in cls._proc_cache:
            mel_file, mel_code, params = get_mel_proc_data(mel_proc)
            cls._proc_cache[mel_proc] = mel_file, mel_code, params
        else:
            mel_file, mel_code, params = cls._proc_cache[mel_proc]

        if params:
            py_hook = cls._hook_tmpl.format(
                mel_proc, ' + "\', \'" + '.join(params)
            )
        else:
            py_hook = cls._hook_tmpl_no_params.format(mel_proc)

        if py_hook not in mel_code:
            mel_code = mel_code[:-1] + py_hook + mel_code[-1]

            try:
                mel.eval(mel_code)
            except Exception as e:
                print('Failed to add python callback hook')
                print(e)
                return

        cls._registry[mel_proc].append(callback)

    @classmethod
    def remove(cls, mel_proc, callback):
        '''Remove callback from mel procedure'''

        try:
            cls._registry[mel_proc].remove(callback)
        except ValueError:
            pass

        if not cls._registry[mel_proc] and mel_proc in cls._proc_cache:
            mel.eval(cls._proc_cache[mel_proc][1])

    @classmethod
    def clear(cls):
        '''Clear all callbacks and source original mel files'''

        for mel_proc, (_, mel_code, _) in cls._proc_cache.items():
            mel.eval(mel_code)

        cls._registry = defaultdict(list)

    @classmethod
    def execute(cls, mel_proc, *mel_proc_args):
        '''Execute all callbacks for mel procedure'''

        for callback in cls._registry[mel_proc]:
            callback(*mel_proc_args)


def get_mel_proc_data(mel_proc):
    '''Get the mel code and parameters of global mel procedure'''

    mel_file = mel.eval('whatIs ' + mel_proc)
    if mel_file == 'Unknown':
        raise Exception('Mel procedure is unknown')
    elif 'found in: ' in mel_file:
        mel_file = mel_file.split('found in: ')[-1]
    else:
        raise Exception(
            'Mel procedure is not defined in a file, can not add callback'
        )

    with open(mel_file, 'r') as f:
        file_contents = f.read()

    mel_code = []

    pattern = re.compile(r'global proc %s\(.*\)\s+?\{' % (mel_proc))
    match = pattern.search(file_contents)
    if not match:
        raise Exception('Can not find global proc ' + mel_proc)

    mel_def = match.group(0)
    mel_def_end = match.end(0)
    pattern = re.compile(r'\$\w+')
    params = pattern.findall(mel_def)

    mel_code.append(mel_def)
    depth = 1
    for char in file_contents[mel_def_end:]:
        if depth == 0:
            break

        mel_code.append(char)
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1

    return mel_file, ''.join(mel_code), params
