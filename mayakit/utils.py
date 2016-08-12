from maya import cmds

__all__ = ['get_history']


def get_history(node, node_type=None):

    history = cmds.listHistory(node)
    if not node_type:
        return history

    return [n for n in history if cmds.nodeType(n) == node_type]
