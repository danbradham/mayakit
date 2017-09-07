import maya.api.OpenMaya as om
from maya import cmds


def to_curve_fn(curve):

    shape = None
    if cmds.nodeType(curve, 'nurbsCurve'):
        shape = curve
    else:
        child = cmds.listRelatives(curve, shapes=True, noIntermediate=True)
        if child:
            shape = child[0]
        else:
            cmds.warning('Not a proper nurbsCurve: {}'.format(curve))
            raise Exception('Not a proper nurbsCurve: {}'.format(curve))

    sel = om.MSelectionList()
    sel.add(shape)
    dep = sel.getDagPath(0)
    fn = om.MFnNurbsCurve(dep)
    return fn


def build_matrix(normal, tangent, position):

    bitangent = (normal ^ tangent).normalize()
    tangent = (normal ^ bitangent).normalize()
    normal = (tangent ^ bitangent).normalize()
    return om.MMatrix([
        tangent[0], tangent[1], tangent[2], 0,
        bitangent[0], bitangent[1], bitangent[2], 0,
        normal[0], normal[1], normal[2], 0,
        position[0], position[1], position[2], 1
    ])


def align_to_curve(xforms, curve):

    curve_fn = to_curve_fn(curve)
    num_xforms = len(xforms)
    param_step = curve_fn.numSpans / float(num_xforms - 1)
    for i, xform in enumerate(xforms):
        param = i * param_step
        normal = curve_fn.normal(param, om.MSpace.kWorld)
        tangent = -curve_fn.tangent(param, om.MSpace.kWorld)
        position = curve_fn.getPointAtParam(param, om.MSpace.kWorld)
        matrix = build_matrix(normal, tangent, position)
        cmds.xform(xform, ws=True, matrix=matrix)


def align_selected_to_curve():
    sel = cmds.ls(sl=True, long=True)
    align_to_curve(sel[:-1], sel[-1])
