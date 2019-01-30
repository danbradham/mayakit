# -*- coding: utf-8 -*-
__all__ = ['selection', 'undo_chunk', 'restore_time']

from contextlib import contextmanager
from maya import cmds


@contextmanager
def selection(nodes=None):
    '''Context manager that restores your current selection on close. Can also
    be used to temporarly set a selection.

    Examples:
        with selection(cmds.ls(type="nucleus")) as nuclei:
            # Do something with all nucleus nodes

        with selection():
            # Do something that might change your current selection

    '''

    old_selection = cmds.ls(sl=True)
    try:
        if nodes is not None:
            cmds.select(nodes, replace=True)
        yield nodes
    finally:
        cmds.select(old_selection)


@contextmanager
def undo_chunk():
    '''Context manager that wraps all contained code in an undo chunk.'''

    try:
        cmds.undoInfo(openChunk=True)
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


@contextmanager
def restore_time():
    '''Context manager that restores time on close.'''

    last_time = cmds.currentTime(query=True)
    try:
        yield
    finally:
        cmds.currentTime(last_time)
