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
    ('Add Curves To Hair System', {
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
    ('Blank', {
        'command': '',
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('blank.png'),
        'annotation': '',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }),
    ('Create Strands Setup', {
        'command': (
            'import mayakit\n'
            'mayakit.create_strands_system()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('create_system.png'),
        'annotation': 'Create a new strands setup',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }),
    ('Add Hair System', {
        'command': (
            'import mayakit\n'
            'mayakit.create_strands_system()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('create_hair_system.png'),
        'annotation': 'Add a new hair system to the active setup',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }),
    ('Active Selected Hair System', {
        'command': (
            'import mayakit\n'
            'mayakit.set_active_hairsystem_from_selected()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('create_system.png'),
        'annotation': 'Activate the selected hairSystem',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }),
    ('Create Strand', {
        'command': (
            'import mayakit\n'
            'mayakit.create_strand()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('create_system.png'),
        'annotation': 'Create a new strand in the active hairSystem',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }),
    ('Curve to Strand', {
        'command': (
            'cmds.warning("N/A")'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('curve_to_strand.png'),
        'annotation': 'Convert an existing curve to a strand...',
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
