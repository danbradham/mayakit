from math import degrees
from maya import cmds
import maya.api.OpenMaya as om

__all__ = ['create_joint', 'create_joint_chain']

AXIS = {
    'x': om.MVector.kXaxisVector,
    'y': om.MVector.kYaxisVector,
    'z': om.MVector.kZaxisVector,
}
ORDER = {
    'xyz': om.MTransformationMatrix.kXYZ,
    'yzx': om.MTransformationMatrix.kYZX,
    'zxy': om.MTransformationMatrix.kZXY,
    'xzy': om.MTransformationMatrix.kXZY,
    'yxz': om.MTransformationMatrix.kYXZ,
    'zyx': om.MTransformationMatrix.kZYX,
}


def create_joint(pos, aim_vect=AXIS['x'], aim_axis='x',
                 up_vect=AXIS['y'], up_axis='y',
                 rotate_order='xyz'):
    '''
    :param pos: om.MVector
    :param aim_pos: om.MVector
    :param aim_axis: one of ['-x', 'x', 'y', '-y', 'z', '-z']
    :param up_vect: om.MVector
    :param up_axis: one of['x', 'y', 'z']
    '''

    assert aim_axis != up_axis

    if aim_axis.startswith('-'):
        aim_vect *= -1

    T = aim_vect
    B = T ^ up_vect
    N = B ^ T

    if N * up_vect > 0 and up_axis.startswith('-'):
        N *= -1

    matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    slices = dict(x=(0, 3), y=(4, 7), z=(8, 11))
    t_slice = slices.pop(aim_axis.lstrip('-'))
    n_slice = slices.pop(up_axis.lstrip('-'))
    b_slice = slices.popitem()[1]

    matrix[t_slice[0]:t_slice[1]] = T
    matrix[b_slice[0]:b_slice[1]] = B
    matrix[n_slice[0]:n_slice[1]] = N
    matrix[12:15] = pos

    tmatrix = om.MTransformationMatrix(om.MMatrix(matrix))
    euler = tmatrix.rotation()
    euler.reorderIt(ORDER[rotate_order])
    rotation = [degrees(v) for v in tmatrix.rotationComponents()[:-1]]

    cmds.select(clear=True)
    joint = cmds.joint(p=pos, rotationOrder=rotate_order, orientation=rotation)
    return joint


def create_joint_chain(positions, **kwargs):
    '''Create a joint chain from a list of om.MVectors'''

    aim_vects = [b - a for a, b in zip(positions, positions[1:])]
    aim_vects.append(aim_vects[-1])

    joints = [create_joint(pos, aim, **kwargs) for pos, aim, in zip(positions, aim_vects)]
    for parent, child in zip(joints, joints[1:]):
        cmds.parent(child, parent)
    cmds.setAttr(joints[-1] + '.jointOrient', 0, 0, 0) # Zero out the last joint in the chain
    return joints


if __name__ == '__main__':
    positions = [om.MVector(cmds.xform(t, q=True, ws=True, rp=True)) for t in cmds.ls(sl=True)]
    joints = create_joint_chain(positions, aim_axis='-x', up_axis='-y', rotate_order='xyz')
    for jnt in joints:
        cmds.rename(jnt, 'R_' + jnt)
