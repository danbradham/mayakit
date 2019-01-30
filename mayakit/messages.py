# -*- coding: utf-8 -*-
'''
Message attributes API
======================
'''
from maya import cmds

MISSING = object()
ANY = '*'
SEQUENCE = list, tuple, set


def add(messages, objects=None):
    '''Add message attributes to objects.

    When no objects are provided, adds message attrribute to the currently
    selected objects.

    Examples:
        # Add a message attribute to the current selection
        add('funk')

        # Add multiple message attributes to the current selection
        add(['super', 'funk'])

        # Add a message attribute to a specific node
        pSphere = cmds.polySphere()[0]
        add('funk', pSphere)

        # Add a message attribute to multiple nodes
        prims = [cmds.polyCube()[0], cmds.polyTorus()[0]]
        add('funk', [pCube, pTorus])
    '''

    if not objects:
        objects = cmds.ls(sl=True, long=True)
        if not objects:
            raise ValueError('add() requires at least one object.')

    if not isinstance(objects, SEQUENCE):
        objects = [objects]

    if not isinstance(messages, SEQUENCE):
        messages = [messages]

    for msg in messages:
        for obj in objects:
            msg_path = obj + '.' + msg
            if not cmds.objExists(msg_path):
                cmds.addAttr(obj, ln=msg, at='message')


def remove(messages, objects=None):
    '''Remove a message attribute from objects.

    When no objects are provided, removes message attribute from the currently
    selected objects.

    Examples:
        # Remove a message attribute from the current selection
        remove('funk')

        # Remove multiple message attributes from the current selection
        remove(['super', 'funk'])

        # Remove a message attribute from a specific node
        remove('funk', 'pSphere1')

        # Add a message attribute from multiple nodes
        remove('funk', ['pCube1', 'pTorus1'])
    '''

    if not objects:
        objects = cmds.ls(sl=True, long=True)
        if not objects:
            raise ValueError('remove() requires at least one object.')

    if not isinstance(objects, SEQUENCE):
        objects = [objects]

    if not isinstance(messages, SEQUENCE):
        messages = [messages]

    for msg in messages:
        for obj in objects:
            msg_path = obj + '.' + msg
            if cmds.objExists(msg_path):
                cmds.deleteAttr(msg_path)


def ls(obj):
    '''Get all of an objects message attributes.'''

    attrs = []
    default_attrs = [a for a in ['message'] if cmds.objExists(obj + '.' + a)]
    user_attrs = cmds.listAttr(obj, userDefined=True) or []

    for a in default_attrs + user_attrs:
        attr_path = obj + '.' + a
        if cmds.getAttr(attr_path, type=True) == 'message':
            attrs.append(a)

    return attrs


def exist(messages, obj):
    '''Returns True if the given message attributes exist'''

    if not isinstance(messages, SEQUENCE):
        messages = [messages]

    for msg in messages:
        if not cmds.objExists(obj + '.' + msg):
            return False

    return True


def get_input(message, obj, **kwargs):
    '''Query a message attributes connections.'''

    attr_path = obj + '.' + message
    if cmds.objExists(attr_path):
        kwargs.setdefault('source', True)
        kwargs.setdefault('destination', False)
        inputs = cmds.listConnections(attr_path, **kwargs)
        if not inputs:
            return
        return inputs[0]

    raise AttributeError('Message attribute does not exist: ' + attr_path)


def get_outputs(message, obj, **kwargs):
    '''Query a message attributes connections.'''

    attr_path = obj + '.' + message
    if cmds.objExists(attr_path):
        kwargs.setdefault('source', False)
        kwargs.setdefault('destination', True)
        return cmds.listConnections(attr_path, **kwargs)

    raise AttributeError('Message attribute does not exist: ' + attr_path)


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


def search(*messages):
    '''Find all objects matching the specified tags'''

    return set.intersection(
        *[set(cmds.ls('*.' + m, objectsOnly=True, r=True)) for m in messages]
    )
