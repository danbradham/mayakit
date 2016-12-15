from maya import cmds


def multi_curve_field(curve_shapes):

    positions, tangents = combine_curves(curve_shapes)

    field = cmds.createNode('pointCloudToField')
    cmds.connectAttr(positions + '.outArray', field + '.inPositionPP')
    cmds.connectAttr(tangents + '.outArray', field + '.inDirectionPP')


def combine_curves(curve_shapes):

    pnt_attr_nodes = []
    for node in curve_shapes:
        pa = cmds.createNode('pointAttributeToArray')
        cmds.connectAttr(node + '.worldSpace', pa + '.inGeometry')
        cmds.setAttr(pa + '.pointPosition', 1)
        cmds.setAttr(pa + '.pointTangent', 1)
        pnt_attr_nodes.append(pa)


    positions = cmds.createNode('combineArrays')
    tangents = cmds.createNode('combineArrays')

    for i, pa in enumerate(pnt_attr_nodes):
        cmds.connectAttr(pa + '.outPositionPP', (positions + '.inArrays[{}]').format(i))
        cmds.connectAttr(pa + '.outTangentPP', (tangents + '.inArrays[{}]').format(i))

    return positions, tangents
