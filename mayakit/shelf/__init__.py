from __future__ import absolute_import
import os
from maya import mel, cmds
from Qt import QtGui
from functools import partial
from collections import OrderedDict

this_package = os.path.abspath(os.path.dirname(__file__))
shelf_path = partial(os.path.join, this_package)

SHELF_NAME = 'MayaKit'
SHELF_BUTTONS = OrderedDict([
    ('Align To Curve', {
        'command': (
            'import mayakit\n'
            'mayakit.align_selected_to_curve()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('align_selected_to_curve.png'),
        'annotation': 'Aligns selected transforms to a nurbsCurve',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }),
    ('Add Curves To Hair System',{
        'command': (
            'import mayakit\n'
            'mayakit.add_curves_to_hair_system()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('add_curves_to_hairSystem.png'),
        'annotation': 'Add selected curves to selected hairSystem',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }),
])


def create_shelf():
    '''Create the bns shelf'''

    tab_layout = mel.eval('$pytmp=$gShelfTopLevel')
    shelf_exists = cmds.shelfLayout(SHELF_NAME, exists=True)

    if shelf_exists:
        cmds.deleteUI(SHELF_NAME, layout=True)

    shelf = cmds.shelfLayout(SHELF_NAME, parent=tab_layout)

    for button, kwargs in SHELF_BUTTONS.items():

        try:
            img = QtGui.QImage(kwargs['image'])
            kwargs['width'] = img.width()
            kwargs['height'] = img.height()

            cmds.shelfButton(label=button, parent=shelf, **kwargs)
        except:
            print button + ' failed...'
            print kwargs


create_shelf()
