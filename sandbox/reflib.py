# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
from maya import cmds
import os


def sre(search, replace):
    '''Search replace transform factory.

    Example:
        repath_references(['refRN'], [sre('search', 'replace')])
    '''
    def _sre(path):
        return path.replace(search, replace)
    return _sre


def repath_preview(ref_nodes, transformations):
    '''Preview repath transformations.

    Arguments:
        ref_nodes: list of referenceNodes
        transformations: functions to apply to reference nodes

    Examples:
        repath_preview(['refRN'], [lambda x: x.replace('search', 'replace')])
    '''

    for ref_node in ref_nodes:
        path = get_path(ref_node)
        orig = path
        for transform in transformations:
            path = transform(path)
        if os.path.exists(path):
            print(' OK:\n\t%s\n\t%s' % (orig, path))
        else:
            print('ERR: Could not find new path\n\t%s\n\t%s' % (orig, path))


def repath(ref_nodes, transformations):
    '''Apply all transformations to the paths of ref_nodes.

    Arguments:
        ref_nodes: list of referenceNodes
        transformations: functions to apply to reference nodes

    Examples:
        ref_nodes = [n for n in cmds.ls(references=True)
                     if 'str' in get_path(n)]
        repath_references(
            ref_nodes,
            [sre('search', 'replace')]
        )
    '''

    for ref_node in ref_nodes:
        path = get_path(ref_node)
        orig = path
        for transform in transformations:
            path = transform(path)
        if os.path.exists(path):
            print(' OK:\n\t%s\n\t%s' % (orig, path))
        else:
            err = 'ERR: Could not find new path\n\t%s\n\t%s' % (orig, path)
            cmds.warning(err)
            continue
        update(ref_node, path)


def namespace_for(in_file):
    '''some/path/mdl_file_v002.mb => mdl_file_v002'''

    return os.path.splitext(os.path.basename(in_file))[0]


def update(ref_node, in_file, namespace=None):
    '''Update a reference node.

    Namespace will default to the basename of in_file.

    Arguments:
        ref_node: reference node
        in_file: new file path
        namespace: custom namespace
    '''

    namespace = namespace or namespace_for(in_file)
    cmds.file(in_file, loadReference=ref_node)
    path = get_path(ref_node)
    cmds.file(path, edit=True, namespace=namespace)
    cmds.lockNode(ref_node, lock=False)
    cmds.rename(ref_node, namespace + 'RN')
    cmds.lockNode(namespace + 'RN', lock=True)


def get_path(ref_node):
    '''Get a reference nodes path'''

    return cmds.referenceQuery(ref_node, filename=True)
