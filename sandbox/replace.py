from maya import cmds
from contextlib import contextmanager


@contextmanager
def undo_chunk():
    '''Context manager, make an undoable block'''

    try:
        cmds.undoInfo(openChunk=True)
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


def get_shader(node):
    '''Get the shader applied to a transform or mesh'''

    node_type = cmds.nodeType(node)

    if node_type == 'transform':
        shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True)
        if not shapes:
            return
        shape = shapes[0]
    elif node_type == 'mesh':
        shape = node

    try:
        shading_engine = cmds.listConnections(shape, type='shadingEngine')[0]
    except IndexError:
        raise Exception('{} is not attached to a shading engine'.format(shape))

    try:
        shader = cmds.listConnections(shading_engine + '.surfaceShader')[0]
    except IndexError:
        raise Exception('{} shadingEngine has no surfaceShader attached'.format(shading_engine))

    return shader


def apply_shader(shape, shader):
    '''Apply a shader to the specified shape'''

    sg = cmds.listConnections(shader, type='shadingEngine')
    if not sg:
        sg = cmds.sets(name=shader + 'SG', renderable=True, nss=True)
        cmds.connectAttr(shader + '.outColor', sg + '.surfaceShader', f=True)
    else:
        sg = sg[0]

    if not cmds.sets(shape, isMember=sg):
        cmds.sets(shape, edit=True, forceElement="initialShadingGroup")
        cmds.sets(shape, edit=True, forceElement=sg)


def replace_shapes(obj, shape):
    '''Replaces an objects shape nodes with a new shape node.'''

    # Duplicate replacement object
    new_xform = cmds.duplicate(shape, rr=True, rc=True)
    new_shape = cmds.listRelatives(new_xform, shapes=True)[0]
    pos = cmds.xform(obj, q=True, ws=True, rp=True)
    cmds.xform(new_xform, ws=True, t=pos)

    # Get obj shapes and shader
    shapes = cmds.listRelatives(obj, shapes=True)
    shader = get_shader(shapes[0])

    # Delete old shapes
    cmds.delete(shapes)

    # Reparent shader and apply old shader and rename
    parented_shape = cmds.parent(new_shape, obj, add=True, shape=True)[0]
    apply_shader(parented_shape, shader)
    cmds.rename(parented_shape, shapes[0])

    # Delete duplicate replacement object
    cmds.delete(new_xform)


def replace_objects(objects, replacement):
    '''Replace a bunch of objects with a new replacement object.'''

    if cmds.nodeType(replacement) in ["mesh", "nurbsCurve", "nurbsSurface"]:
        shape = replacement
    else:
        shapes = cmds.listRelatives(replacement, noIntermediate=True, shapes=True)
        if not shapes:
            return cmds.warning("Replacement object has no shape nodes...")
        shape = shapes[0]

    with undo_chunk():
        for obj in objects:
            replace_shapes(obj, shape)


def get_width(obj):
    bbox_min = cmds.getAttr(obj + '.boundingBoxMin')[0]
    bbox_max = cmds.getAttr(obj + '.boundingBoxMax')[0]
    return bbox_max[0] - bbox_min[0]


def simple_replace_objects(objects, replacement):

    with undo_chunk():
        for obj in objects:
            pos = cmds.xform(obj, q=True, ws=True, rp=True)
            parent = cmds.listRelatives(obj, parent=True)
            shader = get_shader(obj)

            new_obj = cmds.duplicate(replacement, rr=True, rc=True)[0]
            apply_shader(new_obj, shader)

            if parent:
                cmds.parent(new_obj, parent, relative=True)
                cmds.xform(new_obj, ws=True, t=pos)

            scale = get_width(obj) / get_width(new_obj)
            cmds.xform(new_obj, relative=True, scale=[scale, scale, scale])
            cmds.delete(obj)
            cmds.rename(new_obj, obj)


def simple_replace_selected_objects():
    '''Replace objects using "simple" method. This method replaces objects
    using their rotatepivot and bouncing box size in X. This means it works
    with fucked up/frozen transforms.

    Note: Do not use if you're trying to preserve animation.

    Usage:
      1. Select replacement objects
      2. Select objects to replace
      3. execute simple_replace_selected_objects()
    '''

    selection = cmds.ls(sl=True)
    if len(selection) < 2:
        return cmds.warning("Must select a replacement, and a bunch of objects to replace.")

    replacement = selection[0]
    objects = selection[1:]
    simple_replace_objects(objects, replacement)


def replace_selected_objects():
    '''Replace objects preserving original transforms. This method
    replaces the shape node of your objects with a new shape node.

    Note: It will preserve animation, but, if your transforms were
    frozen prior to animation, it may not work.

    Usage:
      1. Select replacement objects
      2. Select objects to replace
      3. execute replace_selected_objects()
    '''

    selection = cmds.ls(sl=True)
    if len(selection) < 2:
        return cmds.warning("Must select a replacement, and a bunch of objects to replace.")

    replacement = selection[0]
    objects = selection[1:]
    replace_objects(objects, replacement)


if __name__ == "__main__":
    #simple_replace_selected_objects()
    replace_selected_objects()
