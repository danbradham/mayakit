# -*- coding: utf-8 -*-
from maya import cmds
from maya.api.OpenMaya import MVector
from math import pi, sin, cos, sqrt
from functools import partial


def get_curve_info(curve):

    spans = cmds.getAttr(curve + '.spans')
    degree = cmds.getAttr(curve + '.degree')
    form = cmds.getAttr(curve + '.form')
    cvs = spans + degree
    return cvs, spans, degree, form


def average_curves(*curves):

    cvs, spans, degree, form = get_curve_info(curves[0])
    points = [cmds.getAttr(curve + '.cv[*]') for curve in curves]
    if not all(len(points[0]) == len(curve_points) for curve_points in points):
        raise Exception('Input curves need to have the same number of cvs')

    averaged = [[0, 0, 0] for i in range(len(points[0]))]
    for curve_points in points:
        for point in curve_points:
            averaged[0] += point[0]
            averaged[1] += point[1]
            averaged[2] += point[2]
    averaged = [pnt / len(points) for pnt in averaged]
    return averaged


def conform_curve(source, destination):

    point_on_curve = cmds.createNode('nearestPointOnCurve')
    cmds.connectAttr(destination + '.worldSpace', point_on_curve + '.inputCurve')

    for i, point in enumerate(cmds.getAttr(source + '.cv[*]')):
        cmds.setAttr(point_on_curve + '.inPosition', point[0], point[1], point[2])
        result_point = cmds.getAttr(point_on_curve + '.result.position')[0]
        cmds.setAttr('{}.cv[{}]'.format(source, i), result_point[0], result_point[1], result_point[2])
    cmds.delete(point_on_curve)


def cool(t):
    return sin(t * pi * 0.5)


def inverse_square(t):
    try:
        return 1.0 / t
    except ZeroDivisionError:
        return 1.0


def lerp(a, b, t):
    '''
    Linear Interpolate between two values
    '''

    return a * (1.0 - t) + b * t


def hermite(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def invhermite(t):
    return t + (t - hermite(t))


def smoothstep(a, b, t):
    '''
    Hermite interpolation between two values
    '''

    real_t = t * t * t * (t * (t * 6 - 15) + 10)
    return lerp(a, b, real_t)


def graph(fn, params, scale=10, offset=(0, 0, 0)):
    '''Graph fn for the provided params'''

    points = []
    for t in params:
        x = t * scale + offset[0]
        y = fn(t) * scale + offset[1]
        points.append((x, y, offset[2]))

    cmds.curve(point=points)


def tangent_at_parameter(curve, t):
    return cmds.pointOnCurve(curve, parameter=t, normalizedTangent=True)


def sphere_normal(point, center):
    return (point - center).normal()


def lofted_normal(curve_a, curve_b, t):
    pass


def point_at_parameter(curve, t):

    return cmds.pointPosition('{}.u[{}]'.format(curve, t))


def stitch_curves(curve_a, curve_b, stitches, stitch_points, u_offset=0,
                  tangent_offset=0, normal_fn=None):

    if not normal_fn:
        normal_fn = partial(lofted_normal, curve_a, curve_b)

    stitch_step = 1.0 / (stitches * 2)
    stitch_blend_step = 1.0 / (stitch_points)

    points = []

    a_point = MVector(*point_at_parameter(curve_a, u_offset))
    a_normal = normal_fn(a_point)
    a_tangent = MVector(*tangent_at_parameter(curve_a, u_offset))

    for i in range(stitches * 2):

        u = ((stitch_step * (i + 1)) + u_offset) % 1
        tangent_offset *= -1

        if i % 2: # curve_a for odd steps
            b_point = MVector(*point_at_parameter(curve_a, u))
            b_tangent = MVector(*tangent_at_parameter(curve_a, u))
            b_normal = normal_fn(b_point)
        else: # curve_b for even steps
            b_point = MVector(*point_at_parameter(curve_b, u))
            b_tangent = MVector(*tangent_at_parameter(curve_b, u))
            b_normal = normal_fn(b_point)

        for j in range(stitch_points):

            t = j * stitch_blend_step
            normal = lerp(a_normal, b_normal, t)
            tangent = lerp(a_tangent, b_tangent, t)

            j_point = lerp(a_point, b_point, t)
            j_normal = normal * (t - hermite(t))
            j_tangent = tangent * tangent_offset * sin(t * pi)

            points.append(j_point + j_normal + j_tangent)

        a_point = b_point
        a_normal = b_normal
        a_tangent = b_tangent

    return points


def cross_stitch(stitches=108, stitch_points=8, u_offset=0, tangent_offset=0, normal_fn=None):
    '''Create cross stitching between two curves'''

    a, b = cmds.ls(sl=True, dag=True, leaf=True)

    if not normal_fn:
        normal_fn = partial(sphere_normal, center=MVector(0, 0, 0))

    half_stitches = int(stitches * 0.5)
    u_offset_a = u_offset
    u_offset_b = u_offset + 1.0 / (half_stitches * 2)
    a0, a1 = MVector(*point_at_parameter(a, 0)), MVector(*point_at_parameter(a, u_offset_b))
    tangent_offset += (a0-a1).length() * 0.3

    points = stitch_curves(a, b, half_stitches, stitch_points, u_offset_a, tangent_offset, normal_fn)
    cmds.curve(point=points)

    points = stitch_curves(a, b, half_stitches, stitch_points, u_offset_b, tangent_offset, normal_fn)
    cmds.curve(point=points)
