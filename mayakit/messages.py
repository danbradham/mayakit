'''
Message attributes API
======================
'''
from maya import cmds

MISSING = object()
ANY = '*'


def add(obj, *messages):
    '''Add message attributes to an object'''

    for msg in messages:
        msg_path = obj + '.' + msg
        if not cmds.objExists(msg_path):
            cmds.addAttr(obj, ln=msg, at='message')


def remove(obj, *messages):
    '''Remove message attributes from an object'''

    for msg in messages:
        msg_path = obj + '.' + msg
        if cmds.objExists(msg_path):
            cmds.deleteAttr(msg_path)


def get(obj):
    '''Get all of an objects message attributes.'''

    attrs = []
    for a in cmds.listAttr(obj):
        attr_path = obj + '.' + a
        if cmds.getAttr(attr_path, type=True) == 'message':
            attrs.append(a)
    return attrs


def connect(src_message, dest_message, *objects):
    '''Connect source message attribute to destination message attribute.

    Arguments:
        src_message: Name of source message attribute
        dest_message: Name of destination message attribute
        *objects: List of objects to connect. The first object is the source.
            If no objects are provided, use your current maya selection.
    '''

    if not objects:
        objects = cmds.ls(sl=True, long=True)
        if not objects:
            raise ValueError('Must select some objects')

    if len(objects) < 2:
        raise ValueError('Connect requires at least two objects')

    src, dests = objects[0], objects[1:]
    src_attr = src + '.' + src_message
    for dest in dests:
        dest_attr = dest + '.' + dest_message
        cmds.connectAttr(src_attr, dest_attr, force=True)


def disconnect(src_message, dest_message, *objects):
    '''Disconnect source message attribute from destination message attribute.

    Arguments:
        src_message: Name of source message attribute
        dest_message: Name of destination message attribute
        *objects: List of objects to connect. The first object is the source.
            If no objects are provided, use your current maya selection.
    '''

    if not objects:
        objects = cmds.ls(sl=True, long=True)
        if not objects:
            raise ValueError('Must select some objects')

    if len(objects) < 2:
        raise ValueError('Connect requires at least two objects')

    src, dests = objects[0], objects[1:]
    src_attr = src + '.' + src_message
    for dest in dests:
        dest_attr = dest + '.' + dest_message
        cmds.disconnectAttr(src_attr, dest_attr, force=True)


def query(obj, message):
    '''Query a message attributes connections.'''

    attr_path = obj + '.' + message
    if cmds.objExists(attr_path):
        return cmds.listConnections(attr_path)

    raise AttributeError('Message attribute does not exist: ' + attr_path)


def search(*messages):
    '''Find all objects matching the specified tags'''

    return set.intersection(
        *[set(cmds.ls('*.' + m, objectsOnly=True, r=True)) for m in messages]
    )
