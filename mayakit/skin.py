# -*- coding: utf-8 -*-

from maya import cmds
from . import utils

__all__ = ['copy_skin']


def copy_skin(source, destination):
    '''Duplicate the selected mesh with skinning'''

    joints = utils.get_history(source, 'joint')
    history = utils.get_history(destination, 'skinCluster')
    if history:
        skincluster = history[0]
        for joint in joints:
            try:
                cmds.skinCluster(skincluster, edit=True, lw=True, ai=joint)
            except RuntimeError as e:
                if 'is already attached' not in str(e):
                    raise
    else:
        skincluster = cmds.skinCluster(*(joints + [destination]), tsb=True)
    cmds.copySkinWeights(
        source, destination,
        noMirror=True,
        surfaceAssociation='closestPoint',
        influenceAssociation='closestJoint'
    )
