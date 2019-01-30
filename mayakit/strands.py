# -*- coding: utf-8 -*-
'''
strands
=======
Easy strands library
'''
from __future__ import division
import maya.api.OpenMaya as om
from maya import cmds
import uuid
from . import tags


def set_color(obj, *color):
    cmds.setAttr(obj + '.useOutlinerColor', 1)
    cmds.setAttr(obj + '.outlinerColor', *color)
    cmds.color(obj, rgb=color)


def set_default_color(obj):
    cmds.setAttr(obj + '.useOutlinerColor', 0)
    cmds.setAttr(obj + '.outlinerColor', 0.0, 0.0, 0.0)
    cmds.color(obj)


def get_active_nucleus():
    nuclei = tags.search(strands_nucleus='active')
    if nuclei:
        return nuclei[0]


def set_active_nucleus(nucleus):
    nuclei = tags.search(strands_nucleus='active')
    for _nucleus in nuclei:
        tags.add(_nucleus, strands_nucleus='inactive')
        set_default_color(_nucleus)
    tags.add(nucleus, strands_nucleus='active')
    set_color(nucleus, 1.0, 1.0, 0.0)


def get_active_hairsystem():
    hair_systems = tags.search(strands_hairsystem='active')
    if hair_systems:
        return hair_systems[0]


def get_hairsystem_grp(hair_system):
    xform = cmds.listRelatives(hair_system, parent=True)[0]
    groups = cmds.listRelatives(xform, parent=True)
    if groups:
        return groups[0]


def get_strands_grp(hair_system):
    groups = tags.search(hair_system=tags.query(hair_system, '_id'))
    if groups:
        return groups[0]


def set_active_hairsystem(hair_system):
    hair_systems = tags.search(strands_hairsystem='active')
    for _hair_system in hair_systems:
        tags.add(_hair_system, strands_hairsystem='inactive')
        set_default_color(cmds.listRelatives(_hair_system, parent=True)[0])
        strands_grp = get_strands_grp(_hair_system)
        set_default_color(strands_grp)

    tags.add(hair_system, strands_hairsystem='active')
    set_color(cmds.listRelatives(hair_system, parent=True)[0], 1.0, 1.0, 0.0)
    strands_grp = get_strands_grp(hair_system)
    set_color(strands_grp, 1.0, 1.0, 0.0)


def set_active_hairsystem_from_selected():
    try:
        hair_system = cmds.ls(sl=True, dag=True, leaf=True)[0]
    except IndexError:
        raise RuntimeError('Select a hairSystem to activate')

    if cmds.nodeType(hair_system) != 'hairSystem':
        raise RuntimeError('Select a hairSystem to activate')

    nucleus = cmds.listConnections(hair_system, type='nucleus')[0]
    set_active_hairsystem(hair_system)
    set_active_nucleus(nucleus)


def create_nucleus(name=None):

    nucleus = cmds.createNode('nucleus')
    cmds.connectAttr('time1.outTime', nucleus + '.currentTime')
    if name:
        nucleus = cmds.rename(nucleus, name)
    return nucleus


def create_hair_system(name, nucleus=None):
    '''Create a hair system, add it to specified nucleus or active nucleus'''

    nucleus = nucleus or create_nucleus(name + '_nucleus')

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
    if name:
        xform = cmds.listRelatives(hair_system, parent=True)[0]
        xform = cmds.rename(xform, name)
        hair_system = cmds.listRelatives(xform, shapes=True)[0]

    return hair_system


def create_strands_system(name='strands', activate=True):
    '''Create a new strands system with a nucleus and hair_system'''

    nucleus = create_nucleus(name + '_nucleus#')
    nucleus_id = uuid.uuid4()
    tags.add(nucleus, _id=nucleus_id)
    cmds.group(nucleus, name=name + '_root#')
    create_strands_hair_system(name, nucleus, activate)

    if activate:
        set_active_nucleus(nucleus)


def create_strands_hair_system(name='strands', nucleus=None, activate=True):

    nucleus = nucleus or get_active_nucleus()

    hair_system = create_hair_system(name + '_hair#', nucleus)
    cmds.setAttr(hair_system + '.stretchResistance', 500)
    cmds.setAttr(hair_system + '.drag', 0.1)
    cmds.setAttr(hair_system + '.motionDrag', 0.002)
    cmds.setAttr(hair_system + '.damp', 0.002)
    cmds.setAttr(hair_system + '.restLengthScale', 0.5)
    hair_id = uuid.uuid4()
    tags.add(hair_system, _id=hair_id)
    strands_grp = cmds.group(name=name + '_controls#')
    tags.add(strands_grp, hair_system=hair_id)

    if activate:
        set_active_hairsystem(hair_system)

    group = cmds.listRelatives(nucleus, parent=True)[0]
    cmds.parent([hair_system, strands_grp], group)


def create_strand(hair_system=None):

    hair_system = hair_system or get_active_hairsystem()
    strands_grp = get_strands_grp(hair_system)

    start = om.MVector(0, 0, -12)
    end = om.MVector(0, 0, 12)

    start_loc = cmds.spaceLocator(name='strand_start#')[0]
    cmds.xform(start_loc, ws=True, translation=start)
    set_color(start_loc, 0.0, 0.0, 1.0)
    end_loc = cmds.spaceLocator(name='strand_end#')[0]
    cmds.xform(end_loc, ws=True, translation=end)
    set_color(end_loc, 1.0, 0.0, 0.0)

    expand_grp = cmds.group(
        [start_loc, end_loc],
        name='strand_srt#'
    )

    curve, curve_shape = curve_between(
        start,
        end,
        2,
        1,
        'strand_input_curve#'
    )
    cmds.connectAttr(
        start_loc + '.worldPosition',
        curve_shape + '.controlPoints[0]'
    )
    cmds.connectAttr(
        end_loc + '.worldPosition',
        curve_shape + '.controlPoints[1]'
    )

    root_grp = cmds.group(
        empty=True,
        name='strand_grp#'
    )
    cmds.parent(expand_grp, root_grp)

    if strands_grp:
        cmds.parent(root_grp, strands_grp)

    follicle_nodes, out_curve_nodes = add_curve_to_system(
        curve_shape,
        hair_system
    )
    cmds.setAttr(follicle_nodes[1] + '.pointLock', 3)
    cmds.setAttr(follicle_nodes[1] + '.sampleDensity', 96)
    cmds.parent(curve, follicle_nodes[0])


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


def add_follicle(follicle_shape, hair_system):

    hair_index = cmds.getAttr(hair_system + '.inputHair', size=True)
    input_hair = '{}.inputHair[{}]'.format(hair_system, hair_index)
    output_hair = '{}.outputHair[{}]'.format(hair_system, hair_index)
    cmds.connectAttr(follicle_shape + '.outHair', input_hair)
    cmds.connectAttr(output_hair, follicle_shape + '.currentPosition')


def curve_to_hair(curve_shape, hair_system):

    curve = cmds.listRelatives(curve_shape, parent=True)[0]
    curve_name = curve.split('|')[-1]

    # Create follicle
    follicle_shape = cmds.createNode('follicle')
    follicle = cmds.listRelatives(follicle_shape, parent=True)[0]
    follicle = cmds.rename(follicle, curve_name + '_follicle#')
    follicle_shape = cmds.listRelatives(follicle, shapes=True)[0]
    cmds.connectAttr(
        curve + '.worldMatrix',
        follicle_shape + '.startPositionMatrix'
    )
    cmds.connectAttr(
        curve_shape + '.local',
        follicle_shape + '.startPosition'
    )

    # # Create output curve
    out_curve_shape = cmds.createNode('nurbsCurve')
    out_curve = cmds.listRelatives(out_curve_shape, parent=True)[0]
    out_curve = cmds.rename(out_curve, curve_name + '_out#')
    out_curve_shape = cmds.listRelatives(out_curve, shapes=True)[0]
    cmds.connectAttr(follicle + '.outCurve', out_curve_shape + '.create')

    # Add follicle to hair system
    add_follicle(follicle_shape, hair_system)

    return [[follicle, follicle_shape], [out_curve, out_curve_shape]]


def add_curve_to_system(curve_shape, hair_system=None):

    hair_system = hair_system or get_active_hairsystem()
    hair_system_grp = get_hairsystem_grp(hair_system)
    basename = hair_system.replace('Shape', '')

    follicle_nodes, out_curve_nodes = curve_to_hair(curve_shape, hair_system)
    follicles_grp = basename + 'Follicles'
    if not cmds.objExists(follicles_grp):
        cmds.group(empty=True, name=follicles_grp)
        if hair_system_grp:
            cmds.parent(follicles_grp, hair_system_grp)
    cmds.parent(follicle_nodes[0], follicles_grp)

    outcurves_grp = basename + 'OutputCurves'
    if not cmds.objExists(outcurves_grp):
        cmds.group(empty=True, name=outcurves_grp)
        if hair_system_grp:
            cmds.parent(outcurves_grp, hair_system_grp)
    cmds.parent(out_curve_nodes[0], outcurves_grp)

    return follicle_nodes, out_curve_nodes


def add_curves_to_hair_system():

    sel = cmds.ls(sl=True, dag=True, leaf=True, long=True)
    if len(sel) < 2:
        cmds.warning('Select a bunch of curves and a hairSystem node.')
        return

    curves = sel[:-1]
    hair_system = sel[-1].split('|')[-1]
    if cmds.nodeType(hair_system) != 'hairSystem':
        cmds.warning(hair_system + ' is not a hairSystem.')
        return

    for curve in curves:
        add_curve_to_system(curve, hair_system)


def _quick_test_():
    create_strands_system()
    set_active_hairsystem_from_selected()
    create_strand()


if __name__ == "__main__":
    _quick_test_()
