'''
strands
=======
Easy strands library
'''

from __future__ import division
import maya.api.OpenMaya as om
from maya import cmds, mel


def linspace(tmin, tmax, n):
    '''Clone of numpy.linspace

    :param tmin: Minimum value
    :param tmax: Maximum value
    :param n: Steps between tmin and tmax
    '''

    output = []
    spread = tmax - tmin
    step = spread / (n - 1)
    for i in xrange(n):
        output.append(tmin + step * i)
    return output


def compute_knots(num_points, degree, array_typ=list):
    '''Compute knots for the given number of points

    :param num_points: number of points along curve
    :param degree: degree of curve
    :param array_typ: Type of array to return
    '''

    num_knots = num_points + degree - 1
    knots = array_typ()
    for i in xrange(degree):
        knots.append(0)
    for i in xrange(num_knots - degree * 2):
        knots.append(i + 1)
    for j in xrange(degree):
        knots.append(i + 2)  # exploit leaked reference
    return knots


def curve_between(a, b, num_points=24, degree=3, name='curve#'):
    '''Create a nurbsCurve between two MVectors

    :param a: start of curve
    :param b: end of curve
    :param num_points: number of points on curve
    :param degree: degree of curve
    '''

    v = b - a

    cvs = []
    for t in linspace(0, 1, num_points):
        cvs.append(a + v * t)
    knots = compute_knots(num_points, degree)

    curve = cmds.curve(point=cvs, degree=degree, knot=knots)
    curve = cmds.rename(curve, name)
    curve_shape = cmds.listRelatives(curve, shapes=True)[0]
    return curve, curve_shape


def new_strand(hair_system=None):

    if not hair_system:
        selection = cmds.ls(sl=True, dag=True, leaf=True, type='hairSystem')
        if selection:
            hair_system = selection[0]

    start = om.MVector(0, 0, 0)
    end = om.MVector(0, 0, 24)

    start_loc = cmds.spaceLocator(name='strand_start#')[0]
    end_loc = cmds.spaceLocator(name='strand_end#')[0]
    cmds.xform(end_loc, ws=True, translation=end)

    tta = cmds.createNode('transformsToArrays')
    cmds.connectAttr(start_loc + '.worldMatrix', tta + '.inTransforms[0].inMatrix')
    cmds.connectAttr(end_loc + '.worldMatrix', tta + '.inTransforms[1].inMatrix')
    pcc = cmds.createNode('pointCloudToCurve')
    cmds.connectAttr(tta + '.outPositionPP', pcc + '.inArray')
    expand_grp = cmds.group([start_loc, end_loc], name='strand_expand_grp#')

    curve, curve_shape = curve_between(start, end, name='strand_curve#')
    cmds.connectAttr(pcc + '.outCurve', curve_shape + '.create')
    root_grp = cmds.group(empty=True, name='strand_grp#')
    cmds.parent([expand_grp, curve], root_grp)

    follicle_nodes, out_curve_nodes = add_curve_to_system(curve_shape, hair_system)
    follicle_shape = follicle_nodes[1]
    cmds.setAttr(follicle_shape + '.pointLock', 3)
    cmds.setAttr(follicle_shape + '.sampleDensity', 24)


def get_nucleus():
    selection = cmds.ls(sl=True, dag=True, leaf=True, type='nucleus')
    if selection:
        return selection[0]

    nucleus = cmds.ls(type='nucleus')
    if nucleus:
        return nucleus[0]

    nucleus = cmds.createNode('nucleus')
    cmds.connectAttr('time1.outTime', nucleus + '.currentTime')
    return nucleus


def create_hair_system(nucleus=None):
    '''Create a hair system, add it to the specified nucleus or active nucleus'''

    if not nucleus:
        nucleus = get_nucleus()

    hair_system = cmds.createNode('hairSystem')
    cmds.connectAttr('time1.outTime', hair_system + '.currentTime')
    index = cmds.getAttr(nucleus + '.inputActive', size=True)
    input_active = '{}.inputActive[{}]'.format(nucleus, index)
    input_start = '{}.inputActiveStart[{}]'.format(nucleus, index)
    output_object = '{}.outputObjects[{}]'.format(nucleus, index)
    cmds.setAttr(hair_system + '.active', 1)
    cmds.connectAttr(hair_system + '.currentState', input_active)
    cmds.connectAttr(hair_system + '.startState', input_start)
    cmds.connectAttr(output_object, hair_system + '.nextState')
    cmds.connectAttr(nucleus + '.startFrame', hair_system + '.startFrame')
    return hair_system


def add_follicle(follicle_shape, hair_system):

    hair_index = cmds.getAttr(hair_system + '.inputHair', size=True)
    input_hair = '{}.inputHair[{}]'.format(hair_system, hair_index)
    output_hair = '{}.outputHair[{}]'.format(hair_system, hair_index)
    cmds.connectAttr(follicle_shape + '.outHair', input_hair)
    cmds.connectAttr(output_hair, follicle_shape + '.currentPosition')


def curve_to_hair(curve_shape, hair_system):

    curve = cmds.listRelatives(curve_shape, parent=True)[0]

    # Create follicle
    follicle_shape = cmds.createNode('follicle')
    follicle = cmds.listRelatives(follicle_shape, parent=True)[0]
    follicle = cmds.rename(follicle, curve + '_follicle')
    follicle_shape = cmds.listRelatives(follicle, shapes=True)[0]
    cmds.connectAttr(curve + '.worldMatrix', follicle_shape + '.startPositionMatrix')
    cmds.connectAttr(curve_shape + '.local', follicle_shape + '.startPosition')

    # Create output curve
    out_curve_shape = cmds.createNode('nurbsCurve')
    out_curve = cmds.listRelatives(out_curve_shape, parent=True)[0]
    out_curve = cmds.rename(out_curve, curve + '_out')
    out_curve_shape = cmds.listRelatives(out_curve, shapes=True)[0]
    cmds.connectAttr(follicle + '.outCurve', out_curve_shape + '.create')

    # Add follicle to hair system
    add_follicle(follicle_shape, hair_system)

    return [[follicle, follicle_shape], [out_curve, out_curve_shape]]


def add_curve_to_system(curve_shape, hair_system=None):

    if hair_system is None:
        selection = cmds.ls(sl=True, dag=True, leaf=True, type='hairSystem')
        if selection:
            hair_system = selection[0]
        else:
            hair_system = create_hair_system()

    follicle_nodes, out_curve_nodes = curve_to_hair(curve_shape, hair_system)
    follicles_grp = hair_system + 'Follicles'
    outcurves_grp = hair_system + 'OutputCurves'
    if not cmds.objExists(follicles_grp):
        cmds.group(empty=True, name=follicles_grp)
    if not cmds.objExists(outcurves_grp):
        cmds.group(empty=True, name=outcurves_grp)
    cmds.parent(follicle_nodes[0], follicles_grp)
    cmds.parent(out_curve_nodes[0], outcurves_grp)

    return follicle_nodes, out_curve_nodes


def add_curves_to_hair_system():

    sel = cmds.ls(sl=True, dag=True, leaf=True)
    if len(sel) < 2:
        cmds.warning('Select a bunch of curves and a hairSystem node.')
        return

    curves = sel[:-1]
    hair_system = sel[-1]
    if cmds.nodeType(hair_system) != 'hairSystem':
        cmds.warning(hair_system + ' is not a hairSystem.')
        return

    for curve in curves:
        add_curve_to_system(curve, hair_system)
