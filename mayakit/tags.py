'''
Attribute Tagging and Lookup API
================================
'''
from maya import cmds
from fnmatch import fnmatch

MISSING = object()
ANY = '*'


def add(obj, **tags):
    '''Add tag attributes to an object'''

    for attr, value in tags.items():
        attr_path = obj + '.' + attr
        if not cmds.objExists(attr_path):
            cmds.addAttr(obj, ln=attr, dt='string')
        cmds.setAttr(attr_path, value, type='string')


def remove(obj, *attrs):
    '''Remove tag attributes from an object'''

    for attr in attrs:
        attr_path = obj + '.' + attr
        if cmds.objExists(attr_path):
            cmds.deleteAttr(attr_path)


def get(obj):
    '''Get all of an object's tags'''

    user_attrs = cmds.listAttr(obj, userDefined=True)
    data = {}
    for a in user_attrs:
        attr_path = obj + '.' + a
        if cmds.getAttr(attr_path, type=True) == 'string':
            data[a] = cmds.getAttr(attr_path)
    return data


def query(obj, attr, default=MISSING):
    '''Query an objects tag, returning the value or default'''

    attr_path = obj + '.' + attr
    if cmds.objExists(attr_path):
        return cmds.getAttr(attr_path)

    if default is not MISSING:
        return default

    raise AttributeError('Attribute does not exist: ' + attr_path)


def search(**tags):
    '''Find all objects matching the specified tags'''

    sel = set.intersection(
        *[set(cmds.ls('*.' + a, objectsOnly=True, r=True)) for a in tags]
    )
    objects = []
    for obj in sel:
        matches = [
            fnmatch(cmds.getAttr(obj + '.' + a), v)
            for a, v in tags.items()
        ]
        if all(matches):
            objects.append(obj)
    return objects
