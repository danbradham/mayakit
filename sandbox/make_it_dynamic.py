from maya import cmds
from contextlib import contextmanager
import mayakit
from mayakit import messages


MESSAGES = ['nucleus', 'nParticle', 'nParticleXform', 'dyn_locator']


def get_frame_range():
    slider = mel.eval("$pytmp=$gPlayBackSlider")
    frame_range = cmds.timeControl(slider, q=True, rangeArray=True)
    if frame_range[1] - frame_range[0] < 2:
        frame_range = [
            cmds.playbackOptions(q=True, minTime=True),
            cmds.playbackOptions(q=True, maxTime=True)
        ]
    return [int(frame_range[0]), int(frame_range[1])]


def make_dynamic(xform, weight=0.8, damp=0.01, drag=0.01):
    '''Make an xform dynamic'''

    messages.add(MESSAGES, xform)

    # Create objects
    position = cmds.xform(xform, query=True, worldSpace=True, rotatePivot=True)
    parti, parti_shape = cmds.nParticle(position=position)
    cmds.setAttr(parti_shape + ".particleRenderType", 4)
    cmds.goal(parti_shape, useTransformAsGoal=True, weight=weight, goal=xform)
    cmds.setAttr(parti_shape + ".damp", damp)
    cmds.setAttr(parti_shape + ".drag", drag)
    nucleus = cmds.listConnections(parti_shape, type="nucleus")[0]
    dyn_locator = cmds.spaceLocator()[0]
    dyn_locator = cmds.rename(dyn_locator, xform + '_dyn')
    cmds.connectAttr(parti_shape + '.centroid', dyn_locator + '.t')

    messages.connect("message", "nucleus", nucleus, xform)
    messages.connect("message", "nParticle", parti_shape, xform)
    messages.connect("message", "nParticleXform", parti, xform)
    messages.connect("message", "dyn_locator", dyn_locator, xform)



def make_selected_dynamic(weight=0.8, damp=0.01, drag=0.01):

    xforms = cmds.ls(sl=True, transforms=True)
    for xform in xforms:
        make_dynamic(xform, weight=weight, damp=damp, drag=drag)


def bake_dynamic(xform):

    # Make sure we're working on an xform that's attached to dynamics
    if not messages.exist(MESSAGES, xform):
        cmds.warning(xform + " is not attached to dynamics.")
        return

    dyn_locator = messages.get_input('dyn_locator', xform)
    if not dyn_locator:
        cmds.warning("Xform is not attached to a dyn locator")
        return

    # Get Translate values from dyn_locator
    frame_range = range(*get_frame_range())
    keys = []
    with mayakit.restore_time():
        for frame in frame_range:
            cmds.currentTime(frame)
            keys.append(cmds.getAttr(dyn_locator + '.translate')[0])

    # Set keyframes on xform
    for frame, key in zip(frame_range, keys):
        cmds.setKeyframe(xform + '.tx', value=key[0], time=frame)
        cmds.setKeyframe(xform + '.ty', value=key[1], time=frame)
        cmds.setKeyframe(xform + '.tz', value=key[2], time=frame)

    nucleus = messages.get_input('nucleus', xform)
    parti = messages.get_input('nParticleXform', xform)
    parti_shape = messages.get_input('nParticle', xform)

    # Delete dynamics nodes
    cmds.delete([nucleus, parti, parti_shape, dyn_locator])

    # Remove message attributes
    messages.remove(MESSAGES, xform)


def bake_selected_dynamic():

    xforms = cmds.ls(sl=True, transforms=True)
    for xform in xforms:
        bake_dynamic(xform)


if __name__ == "__main__":

    with mayakit.undo_chunk():
        with mayakit.selection():
            make_selected_dynamic(weight=0.6, damp=0.01, drag=0.01)
        bake_selected_dynamic()
