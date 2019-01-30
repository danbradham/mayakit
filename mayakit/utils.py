# -*- coding: utf-8 -*-
from maya import cmds

__all__ = ['get_history']


def get_history(node, node_type=None):

    history = cmds.listHistory(node)
    if not node_type:
        return history

    return [n for n in history if cmds.nodeType(n) == node_type]


def get_frame_range():
    slider = mel.eval("$pytmp=$gPlayBackSlider")
    frame_range = cmds.timeControl(slider, q=True, rangeArray=True)
    if frame_range[1] - frame_range[0] < 2:
        frame_range = [
            cmds.playbackOptions(q=True, minTime=True),
            cmds.playbackOptions(q=True, maxTime=True)
        ]
    return [int(frame_range[0]), int(frame_range[1])]
