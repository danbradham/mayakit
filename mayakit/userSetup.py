# -*- coding: utf-8 -*-
from maya.utils import executeDeferred
from .callbacks import MelProcCallback
from .plugins import burnin


def add_callbacks():
    '''Install all mayakit callbacks'''

    for proc in burnin.view_menu_procs:
        MelProcCallback.add(proc, burnin.view_menu_callback)


executeDeferred(add_callbacks)
