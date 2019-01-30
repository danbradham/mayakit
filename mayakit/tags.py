# -*- coding: utf-8 -*-
'''
Attribute Tagging and Lookup API
================================
'''
from maya import cmds
from fnmatch import fnmatch

MISSING = object()
ANY = '*'


def add(objects=None, **tags):
    '''Add tag attributes to an object'''

    if not objects:
        objects = cmds.ls(sl=True, long=True)
        if not objects:
            raise ValueError('add() requires at least one object.')

    if not isinstance(objects, SEQUENCE):
        objects = [objects]

    for tag, value in tags.items():
        tag_path = obj + '.' + tag
        if not cmds.objExists(tag_path):
            cmds.addAttr(obj, ln=tag, dt='string')
        cmds.setAttr(tag_path, value, type='string')


def remove(obj, *tags):
    '''Remove tag attributes from an object'''

    for tag in tags:
        tag_path = obj + '.' + tag
        if cmds.objExists(tag_path):
            cmds.deleteAttr(tag_path)


def ls(obj):
    '''Get all of an object's tags'''

    user_attrs = cmds.listAttr(obj, userDefined=True) or []
    data = {}
    for a in user_attrs:
        attr_path = obj + '.' + a
        if cmds.getAttr(attr_path, type=True) == 'string':
            data[a] = cmds.getAttr(attr_path)
    return data


def get(obj, tag, default=MISSING):
    '''Query an objects tag, returning the value or default'''

    tag_path = obj + '.' + tag
    if cmds.objExists(tag_path):
        return cmds.getAttr(tag_path)

    if default is not MISSING:
        return default

    raise AttributeError('Attribute does not exist: ' + tag_path)


def exist(obj, *tags):
    '''Returns True if the given message attributes exist'''

    for tag in tags:
        if not cmds.objExists(obj + '.' + tag):
            return False
    return True


def search(**tags):
    '''Find all objects matching the specified tags'''

    sel = set.intersection(*[
        set(cmds.ls('*.' + tag, objectsOnly=True, recursive=True))
        for tag in tags
    ])
    objects = []
    for obj in sel:
        matches = [
            fnmatch(cmds.getAttr(obj + '.' + tag), value)
            for tag, value in tags.items()
        ]
        if all(matches):
            objects.append(obj)
    return objects
