from maya.utils import executeDeferred
from .callbacks import MelProcCallback
from .plugins import burnin


def add_callbacks():
    '''Install all bns callbacks'''

    MelProcCallback.add(burnin.view_menu_proc, burnin.view_menu_callback)


executeDeferred(add_callbacks)
