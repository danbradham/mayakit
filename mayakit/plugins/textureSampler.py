from __future__ import absolute_import
import sys
from functools import partial

import maya.OpenMaya as om1
import maya.OpenMayaRender as omr1
import maya.OpenMayaFX as omfx1
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaRender as omr
from maya import cmds
import pymel.core as pm


def maya_useNewAPI():
    pass


def get_mobj(node_path):
    '''
    Get MObject from node path like "ramp1" or "ramp1.outColor"
    '''
    sel = om.MSelectionList()
    sel.add(node_path)
    return sel.getDependNode(0)


def sample_dyn2dtexture(node, texture_attr, uvs_list):
    '''Fast lookup of textures supported by dynamics, noise, fractal, etc.

    :param node: om.MObject like ramp1
    :param texture_attr: om.MObject attribute like "ramp1.outColor"
    :param uvs_list: List of uvs like [(0.0, 0.5), (0.5, 1.0)]
    '''

    # Validate texture
    valid_texture = omfx1.MDynamicsUtil.hasValidDynamics2dTexture(
        node,
        texture_attr
    )

    if not valid_texture:
        return

    u_coords = om1.MDoubleArray()
    v_coords = om1.MDoubleArray()
    for u, v in uvs_list:
        u_coords.append(u)
        v_coords.append(v)

    result_colors = om1.MVectorArray()
    result_alphas = om1.MDoubleArray()
    omfx1.MDynamicsUtil.evalDynamics2dTexture(
        node,
        texture_attr,
        u_coords,
        v_coords,
        result_colors,
        result_alphas
    )
    colors = om.MFloatVectorArray()
    for i in range(result_colors.length()):
        c = om1.MFloatVector(result_colors[i])
        colors.append(om.MVector(c.x, c.y, c.z))

    return colors


def sample_2d_texture(texture_attr, uvs_list):
    '''Samples a shading network at the specified plug

    :param texture_attr: Attribute string like "ramp1.outColor"
    :param uvs_list: List of uvs like [(0.0, 0.5), (0.5, 1.0)]
    '''

    numSamples = len(uvs_list)
    useShadowMaps = False
    reuseMaps = False
    cameraMatrix = om1.MFloatMatrix()
    points = None
    u_coords = om1.MFloatArray()
    v_coords = om1.MFloatArray()
    for u, v in uvs_list:
        u_coords.append(u)
        v_coords.append(v)
    normals = None
    refPoints = None
    tangentUs = None
    tangentVs = None
    filterSizes = None
    result_colors = om1.MFloatVectorArray()
    result_transp = om1.MFloatVectorArray()

    omr1.MRenderUtil.sampleShadingNetwork(
        texture_attr,
        numSamples,
        useShadowMaps,
        reuseMaps,
        cameraMatrix,
        points,
        u_coords,
        v_coords,
        normals,
        refPoints,
        tangentUs,
        tangentVs,
        filterSizes,
        result_colors,
        result_transp
    )

    colors = om.MFloatVectorArray()
    for i in range(result_colors.length()):
        c = om1.MFloatVector(result_colors[i])
        colors.append(om.MVector(c.x, c.y, c.z))

    return colors


class TextureSampler(object):

    def __init__(self, node):
        self._mobj = get_mobj(node)
        self._depfn = om.MFnDependencyNode(self._mobj)

    @property
    def name(self):
        return self._depfn.name()

    @name.setter
    def name(self, new_name):
        self._depfn.setName(new_name)

    def attr(self, attr_name, index=None):
        attr_name = self.name + '.' + attr_name
        if index is None:
            return attr_name
        return attr_name + '[' + str(index) + ']'

    def get_uvs(self):
        return get_uvs_list(self._mobj)

    def set_uvs(self, uvs_list):
        set_uvs_list(self._mobj, uvs_list)

    @property
    def inColor(self):
        inputs = cmds.listConnections(self.attr('inColor'), d=False, s=True)
        if inputs:
            return inputs[0]

    @inColor.setter
    def inColor(self, texture_attr):
        cmds.connectAttr(texture_attr, self.attr('inColor'))

    def connect(self, attr, nodes=None):
        nodes = nodes or cmds.ls(sl=True)
        if len(nodes) > len(self.get_uvs()):
            raise Exception('More nodes than uv samples')

        for i, node in enumerate(nodes):
            color_attr = self.attr('outColor', i)
            node_attr = node + '.' + attr
            cmds.connectAttr(color_attr, node_attr, force=True)


def texture_sampler(texture, uvs_list=None):
    '''
    Create a textureSampler node

    :param texture_node: Path to texture node like "ramp1"
    :param uvs_list: List of uvs like [(0.0, 0.5), (0.5, 1.0)]
    '''

    texture_attr = texture + '.outColor'
    if not cmds.objExists(texture_attr):
        raise Exception('texture must have an outColor attribute')

    texture_node = cmds.shadingNode('textureSampler', asUtility=True)
    sampler = TextureSampler(texture_node)
    sampler.inColor = texture_attr
    uvs_list = uvs_list or [(0.5, 0.5)]
    sampler.set_uvs(uvs_list)

    return sampler


def get_uvs_list(mobj):
    '''Get textureSampler.uvArray attribute

    :returns: List of tuples like [(0.0, 0.5), (0.5, 1.0)]
    '''

    uvArray_plug = om.MFnDependencyNode(mobj).findPlug('uvArray', True)
    uvs_list = []

    for i in uvArray_plug.getExistingArrayAttributeIndices():
        plug = uvArray_plug.elementByLogicalIndex(i)
        u = plug.child(0).asFloat()
        v = plug.child(1).asFloat()
        uvs_list.append((u, v))

    return uvs_list


def set_uvs_list(mobj, uvs_list):
    '''Set textureSampler.uvArray attribute

    :param uvs_list: List of uvs like [(0.0, 0.5), (0.5, 1.0)]
    :returns: List of tuples like [(0.0, 0.5), (0.5, 1.0)]
    '''

    uvArray_plug = om.MFnDependencyNode(mobj).findPlug('uvArray', True)
    uvArray_attr = uvArray_plug.name() + '[{}]'

    for i in uvArray_plug.getExistingArrayAttributeIndices():
        pm.removeMultiInstance(uvArray_attr.format(i))

    for i, (u, v) in enumerate(uvs_list):
        plug = uvArray_plug.elementByLogicalIndex(i)
        plug.child(0).setFloat(u)
        plug.child(1).setFloat(v)


class textureSampler(om.MPxNode):
    '''
    :ivar uvArray: Array of uv coords to sample
    :ivar inColors: Input color to sample
    :ivar outColor: Array of output colors
    '''

    id_ = om.MTypeId(0x00124dfb)

    def __init__(self):
        super(textureSampler, self).__init__()

    def compute(self, plug, data):

        if plug == self.outColor:

            uvs_list = get_uvs_list(self.thisMObject())
            num_colors = len(uvs_list)

            incolor_plug = om.MFnDependencyNode(self.thisMObject()).findPlug('inColor', True)
            connections = incolor_plug.connectedTo(True, False)
            if connections:
                color_attr = connections[0].name()
                colors_list = sample_2d_texture(color_attr, uvs_list)
            else:
                incolor_handle = data.inputValue(self.inColor)
                c = incolor_handle.asMFloatVector()
                colors_list = [c.copy() for i in range(num_colors)]

            colors_handle = data.outputArrayValue(self.outColor)
            colors_builder = om.MArrayDataBuilder(data, self.outColor, num_colors)

            colors_builder.growArray(num_colors)
            for i, color in enumerate(colors_list):

                mhandle = colors_builder.addElement(i)
                mhandle.setMFloatVector(color)

            colors_handle.set(colors_builder)
            colors_handle.setAllClean()

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):

        typ_attr = om.MFnTypedAttribute()
        num_attr = om.MFnNumericAttribute()
        comp_attr = om.MFnCompoundAttribute()

        cls.inColor = num_attr.createColor('inColor', 'inc')
        cls.addAttribute(cls.inColor)

        cls.outColor = num_attr.createColor('outColor', 'outc')
        num_attr.array = True
        num_attr.usesArrayDataBuilder = True
        cls.addAttribute(cls.outColor)

        uCoord = num_attr.create(
            'uCoord',
            'u',
            om.MFnNumericData.kFloat
        )
        num_attr.internal = True

        vCoord = num_attr.create(
            'vCoord',
            'v',
            om.MFnNumericData.kFloat
        )
        num_attr.internal = True

        cls.uvArray = comp_attr.create('uvArray', 'uvs')
        comp_attr.addChild(uCoord)
        comp_attr.addChild(vCoord)
        comp_attr.array = True
        cls.addAttribute(cls.uvArray)

        cls.attributeAffects(cls.inColor, cls.outColor)
        cls.attributeAffects(cls.uvArray, cls.outColor)


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.registerNode(
            textureSampler.__name__,
            textureSampler.id_,
            textureSampler.creator,
            textureSampler.initialize
        )
    except:
        sys.stderr.write('Failed to register node\n')
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(textureSampler.id_)
    except:
        sys.stderr.write('Failed to deregister node\n')
        raise


class AEtextureSamplerTemplate(pm.ui.AETemplate):

    _nodeType = textureSampler.__name__

    def __init__(self, nodeName):
        super(AEtextureSamplerTemplate, self).__init__(nodeName)

        #Template layout
        self.textfields = []
        self.beginScrollLayout()

        self.beginLayout("Input Arrays", collapse=False)
        self.callCustom(
            self.array_builder,
            self.array_builder,
            'uvArray')
        self.endLayout()

        self.addExtraControls()
        self.endScrollLayout()

        self.suppress("caching")
        self.suppress("nodeState")

    def array_builder(self, attrName):
        frame = 'array_frame'

        if pm.columnLayout(frame, exists=True):
            pm.deleteUI(frame)

        pm.columnLayout(frame)
        pm.rowLayout(numberOfColumns=2)

        uv_array_length = pm.getAttr(attrName, s=True)
        next_attr = '{}[{}]'.format(attrName, uv_array_length)
        add_command = partial(self.add_multiInstance, next_attr)
        pm.button(label='New Item', command=add_command)

        last_attr = '{}[{}]'.format(attrName, uv_array_length - 1)
        remove_command = partial(self.rem_multiInstance, last_attr)
        pm.button(label='Remove Last Item', command=remove_command)

        pm.setParent('..')

        for i in range(uv_array_length):
            index_attr = '{}[{}]'.format(attrName, i)
            u_attr = index_attr + '.uCoord'
            v_attr = index_attr + '.vCoord'

            pm.attrControlGrp(attribute=index_attr)

    def add_multiInstance(self, attrName, *args):
        pm.setAttr(attrName + '.uCoord', 0.0)
        pm.setAttr(attrName + '.vCoord', 0.0)

    def rem_multiInstance(self, attrName, *args):
        pm.removeMultiInstance(attrName)

