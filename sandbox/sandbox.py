def extrude_selected_curves(polycount=800):
    '''
    Extrudes multiple nurbsCurves using a single profile curve.

    1. Select your profile curve (nurbsCircle usually)
    2. Select the curves you'd like to extrude along
    3. execute extrude_selected_curves()
    '''

    selected = cmds.ls(sl=True, long=True)
    profile = selected[0]
    curves = selected[1:]

    for curve in curves:
        xform, extrude = cmds.extrude(
            profile,
            curve,
            extrudeType=2,
            fixedPath=True,
            useProfileNormal=True,
            useComponentPivot=1,
            rotation=0.0,
            scale=1.0,
            reverseSurfaceIfPathReversed=False,
            polygon=True
        )
        tesselate = cmds.listConnections(extrude + '.outputSurface')[0]
        cmds.setAttr(tesselate + '.polygonType', 1)
        cmds.setAttr(tesselate + '.format', 0)
        cmds.setAttr(tesselate + '.polygonCount', polycount)
        cmds.refresh()
