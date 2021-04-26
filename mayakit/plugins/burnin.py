from __future__ import absolute_import
import getpass
import sys
import os
from functools import partial

import maya.OpenMaya as om1
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaRender as omr
from maya import cmds
import pymel.core as pm


MAYA_VERSION = int(cmds.about(version=True))
ANIMCONTROL = oma.MAnimControl
ALIGNMENTS = ('top left', 'top center', 'top right',
              'middle left', 'middle center', 'middle right',
              'bottom left', 'bottom center', 'bottom right')
TEXT_ATTRS = ('textString', 'textAlign', 'textOffset',
              'textScale', 'textColor', 'textAlpha')
TEXT_ALIGN = {
    0: 'left',
    1: 'center',
    2: 'right'
}
FONT_FAMILIES = omr.MUIDrawManager.getFontList()
FONT_WEIGHTS = {
    87: 'black',
    75: 'bold',
    63: 'demiBold',
    50: 'normal',
    25: 'light'
}
FONT_STRETCHES = {
    75: 'Condensed',
    125: 'Expanded',
    62: 'ExtraCondensed',
    150: 'ExtraExpanded',
    87: 'SemiCondensed',
    112: 'SemiExpanded',
    50: 'UltraCondensed',
    200: 'UltraExpanded',
    100: 'Unstretched'
}
USE_FONT_OPTION = 9999
BOX_TYPES = {
    0: 'square',
    1: 'horizontal',
    2: 'vertical',
}
view_menu_procs = [
    'postModelEditorViewMenuCmd',
    'postModelEditorViewMenuCmd_Old'
]


def maya_useNewAPI():
    pass


def get_viewport_burnin():
    '''Get the default viewport burnin'''

    viewport_burnin = cmds.ls('*.viewport_burnin', objectsOnly=True)
    if viewport_burnin:
        return viewport_burnin[0]


def toggle_burnin(value):
    '''Toggle default viewport burnin'''

    viewport_burnin = get_viewport_burnin()
    if viewport_burnin:
        cmds.setAttr(viewport_burnin + '.v', value)
        return

    if not value:
        return

    if not cmds.pluginInfo(burnin.type_name, q=True, loaded=True):
        cmds.loadPlugin(burnin.type_name)

    viewport_burnin = cmds.createNode('burnin')
    cmds.setAttr(viewport_burnin + '.overrideEnabled', 1)
    cmds.setAttr(viewport_burnin + '.overrideDisplayType', 2)
    cmds.addAttr(viewport_burnin, ln='viewport_burnin', at='bool', dv=True)
    cmds.setAttr(viewport_burnin + '.fontSize', 18)
    cmds.setAttr(viewport_burnin + '.fontWeight', 25)
    cmds.setAttr(viewport_burnin + '.fontAlpha', 1.0)

    for i, font in enumerate(FONT_FAMILIES):
        if font == 'Consolas':
            cmds.setAttr(viewport_burnin + '.fontFamily', i)

    t0 = viewport_burnin + '.textArray[0]'
    cmds.setAttr(
        t0 + '.textString',
        '{camera} : {focal_length:>3.0f}mm : {frame:0>3d}',
        type='string'
    )
    cmds.setAttr(t0 + '.textColor', 1, 1, 1)
    cmds.setAttr(t0 + '.textAlign', 8)
    cmds.setAttr(t0 + '.textOffset', 0, -22)
    cmds.setAttr(t0 + '.textAlpha', 1.0)

    t1 = viewport_burnin + '.textArray[1]'
    cmds.setAttr(t1 + '.textString', '{user:>12} : {scene}', type='string')
    cmds.setAttr(t1 + '.textColor', 1, 1, 1)
    cmds.setAttr(t1 + '.textAlign', 6)
    cmds.setAttr(t1 + '.textOffset', 0, -22)
    cmds.setAttr(t1 + '.textAlpha', 1.0)

    b0 = viewport_burnin + '.boxArray[0]'
    cmds.setAttr(b0 + '.boxType', 1)
    cmds.setAttr(b0 + '.boxSize', 18, 18)
    cmds.setAttr(b0 + '.boxAlpha', 0.2)
    cmds.setAttr(b0 + '.boxAlign', 7)


def view_menu_callback(*args):
    '''Callback for global mel proc postModelEditorViewMenuCmd'''

    menu_path = args[0]
    model_panel = args[1]
    menu_item_path = model_panel + 'burnin'

    burnin_enabled = False
    viewport_burnin = get_viewport_burnin()
    if viewport_burnin:
        burnin_enabled = cmds.getAttr(viewport_burnin + '.v')

    cmds.setParent(menu_path, m=True)
    if not cmds.menuItem(menu_item_path, exists=True):
        cmds.menuItem(d=True)
        cmds.menuItem(
            menu_item_path,
            label='Burn In',
            checkBox=burnin_enabled,
            command=toggle_burnin
        )
    else:
        cmds.menuItem(
            menu_item_path,
            edit=True,
            checkBox=burnin_enabled
        )


def get_font_options(mobj):
    '''Retrieve font options'''

    mfndep = om.MFnDependencyNode(mobj)
    fontFamily_mobj = mfndep.attribute('fontFamily')
    fontFamily_plug = om.MPlug(mobj, fontFamily_mobj)
    fontSize_mobj = mfndep.attribute('fontSize')
    fontSize_plug = om.MPlug(mobj, fontSize_mobj)
    fontAlpha_mobj = mfndep.attribute('fontAlpha')
    fontAlpha_plug = om.MPlug(mobj, fontAlpha_mobj)
    fontWeight_mobj = mfndep.attribute('fontWeight')
    fontWeight_plug = om.MPlug(mobj, fontWeight_mobj)
    fontStretch_mobj = mfndep.attribute('fontStretch')
    fontStretch_plug = om.MPlug(mobj, fontStretch_mobj)

    data = {
        'fontFamily': fontFamily_plug.asInt(),
        'fontSize': fontSize_plug.asInt(),
        'fontAlpha': fontAlpha_plug.asFloat(),
        'fontWeight': fontWeight_plug.asInt(),
        'fontStretch': fontStretch_plug.asInt(),
    }

    return data


def get_format_data(mobj, **kwargs):
    '''Get all the data necessary to '''

    mfndep = om.MFnDependencyNode(mobj)

    intArray_data = {}
    intArray_mobj = mfndep.attribute('intArray')
    intArray_plug = om.MPlug(mobj, intArray_mobj)
    for i in intArray_plug.getExistingArrayAttributeIndices():
        plug = intArray_plug.elementByLogicalIndex(i)
        intArray_data[i] = plug.asInt()

    floatArray_data = {}
    floatArray_mobj = mfndep.attribute('floatArray')
    floatArray_plug = om.MPlug(mobj, floatArray_mobj)
    for i in floatArray_plug.getExistingArrayAttributeIndices():
        plug = floatArray_plug.elementByLogicalIndex(i)
        floatArray_data[i] = plug.asFloat()

    data = {
        'frame': int(oma.MAnimControl.currentTime().value),
        'start': int(oma.MAnimControl.minTime().value),
        'end': int(oma.MAnimControl.maxTime().value),
        'scene': os.path.basename(om1.MFileIO().currentFile()),
        'user': getpass.getuser(),
        'intArray': intArray_data,
        'floatArray': floatArray_data,
        'env': os.environ.data,
    }
    data.update(**kwargs)

    return data


def get_textArray_data(mobj):
    '''Get all data from the textArray attribute'''

    data = []

    textArray_mobj = om.MFnDependencyNode(mobj).attribute('textArray')
    textArray_plug = om.MPlug(mobj, textArray_mobj)
    for i in textArray_plug.getExistingArrayAttributeIndices():
        plug = textArray_plug.elementByLogicalIndex(i)

        plug_data = {
            'textString': plug.child(0).asString(),
            'textAlign': plug.child(1).asShort(),
            'textOffset': (
                plug.child(2).child(0).asInt(),
                plug.child(2).child(1).asInt()
            ),
            'textScale': plug.child(3).asFloat(),
            'textColor': (
                plug.child(4).child(0).asDouble(),
                plug.child(4).child(1).asDouble(),
                plug.child(4).child(2).asDouble()
            ),
            'textAlpha': plug.child(5).asFloat(),
            'textFamily': plug.child(6).asShort(),
            'textWeight': plug.child(7).asShort(),
            'textStretch': plug.child(8).asShort(),
        }

        data.append(plug_data)

    return data


def get_boxArray_data(mobj):
    '''Get all data from the boxArray attribute'''

    data = []

    boxArray_mobj = om.MFnDependencyNode(mobj).attribute('boxArray')
    boxArray_plug = om.MPlug(mobj, boxArray_mobj)
    for i in boxArray_plug.getExistingArrayAttributeIndices():
        plug = boxArray_plug.elementByLogicalIndex(i)

        plug_data = {
            'boxType': plug.child(0).asShort(),
            'boxFill': plug.child(1).asBool(),
            'boxAlign': plug.child(2).asShort(),
            'boxOffset': (
                plug.child(3).child(0).asInt(),
                plug.child(3).child(1).asInt(),
            ),
            'boxSize': (
                plug.child(4).child(0).asInt(),
                plug.child(4).child(1).asInt(),
            ),
            'boxColor': (
                plug.child(5).child(0).asDouble(),
                plug.child(5).child(1).asDouble(),
                plug.child(5).child(2).asDouble(),
            ),
            'boxAlpha': plug.child(6).asFloat(),
        }

        data.append(plug_data)

    return data


def set_textArray_data(mobj, text_data):
    '''Set all data from a list of dicts'''

    pass


def textString_to_lines(textString):
    '''Splits a unicode textString into lines'''

    return repr(textString)[2:-1].replace('\\t', '    ').split('\\n')


def get_text_position_and_alignment(view_width, view_height, alignment,
                                    line_height, offset, num_lines):
    '''Get the position of where to start drawing text and the
    alignment of the text.
    '''

    if alignment in (0, 3, 6):  # LEFT
        x = line_height + offset[0]
        align = 0
    elif alignment in (1, 4, 7):  # CENTER
        x = int(view_width * 0.5 - offset[0])
        align = 1
    else:  # RIGHT
        x = view_width - line_height - offset[0]
        align = 2

    if alignment < 3:  # TOP
        y = view_height - line_height - offset[1]
    elif alignment < 6:  # MIDDLE
        y = int(
            view_height * 0.5 +
            (num_lines * 0.5 * line_height) -
            offset[1]
        )
    else:  # BOTTOM
        y = line_height + ((num_lines - 1) * line_height) + offset[1]

    return x, y, align


def get_box_position(view_width, view_height, alignment, scale, offset):

    if alignment in (0, 3, 6):  # LEFT
        x = scale[0] + offset[0]
    elif alignment in (1, 4, 7):  # CENTER
        x = int(view_width * 0.5 - offset[0])
    else:  # RIGHT
        x = view_width - scale[0] - offset[0]

    if alignment < 3:  # TOP
        y = view_height - scale[1] - offset[1]
    elif alignment < 6:  # MIDDLE
        y = int(view_height * 0.5 + offset[1])
    else:  # BOTTOM
        y = scale[1] + offset[1]

    return x, y


class burnin(omui.MPxLocatorNode):
    '''
    :ivar textArray: Array of text string attributes
    :ivar textString: String to format and display
    :ivar textAlign: Text screen alignment
    :ivar textOffset: Text pixel offset
    :ivar textColor: Text Color
    :ivar intArray: Integer array
    :ivar floatArray: Float array
    '''

    type_name = 'burnin'
    type_id = om.MTypeId(0x00124dfc)
    type_classification = "drawdb/geometry/burnin"

    def __init__(self):
        super(burnin, self).__init__()

    def compute(self, plug, data):
        return

    def postConstructor(self):
        om.MFnDagNode(self.thisMObject()).setName(self.type_name + 'Shape#')

    def draw(self, view, path, style, status):

        text_data = get_textArray_data(self.thisMObject())
        font_options = get_font_options(self.thisMObject())
        camera = view.getCamera()
        camera_fn = om.MFnDependencyNode(camera.pop(0).node())
        focal_length = camera_fn.findPlug('focalLength', False).asFloat()
        format_data = get_format_data(
            self.thisMObject(),
            camera=camera.pop(1).partialPathName(),
            focal_length=focal_length
        )
        line_height = 20
        view_width = view.portWidth()
        view_height = view.portHeight()

        view.beginGL()

        for text in text_data:
            try:
                formatted = text['textString'].format(**format_data)
            except Exception:
                formatted = repr(text['textString'])[2:-1]

            lines = textString_to_lines(formatted)
            x, y, alignment = get_text_position_and_alignment(
                view_width=view_width,
                view_height=view_height,
                alignment=text['textAlign'],
                line_height=line_height,
                offset=text['textOffset'],
                num_lines=len(lines)
            )

            alpha = text['textAlpha'] * font_options['fontAlpha']
            color = om.MColor(list(text['textColor']) + [alpha])
            view.setDrawColor(color)
            for i, line in enumerate(lines):
                near, far = om.MPoint(), om.MPoint()
                view.viewToWorld(x, y - i * line_height, near, far)
                view.drawText(line, far, alignment)

        view.endGL()

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):

        typ_attr = om.MFnTypedAttribute()
        num_attr = om.MFnNumericAttribute()
        enum_attr = om.MFnEnumAttribute()
        comp_attr = om.MFnCompoundAttribute()

        # Default font attributes

        fontFamily = enum_attr.create('fontFamily', 'ffamily')
        for i, font in enumerate(FONT_FAMILIES):
            enum_attr.addField(font, i)
            if font == 'Arial':
                enum_attr.default = i
        enum_attr.storable = True
        enum_attr.writable = True
        enum_attr.channelBox = True
        enum_attr.connectable = False
        enum_attr.affectsAppearance = True
        cls.addAttribute(fontFamily)

        fontWeight = enum_attr.create('fontWeight', 'fweight')
        for i, weight in FONT_WEIGHTS.items():
            enum_attr.addField(weight, i)
        enum_attr.default = 50
        enum_attr.storable = True
        enum_attr.writable = True
        enum_attr.channelBox = True
        enum_attr.connectable = False
        enum_attr.affectsAppearance = True
        cls.addAttribute(fontWeight)

        fontStretch = enum_attr.create('fontStretch', 'fstretch')
        for i, stretch in FONT_STRETCHES.items():
            enum_attr.addField(stretch, i)
        enum_attr.default = 100
        enum_attr.storable = True
        enum_attr.writable = True
        enum_attr.channelBox = True
        enum_attr.connectable = False
        enum_attr.affectsAppearance = True
        cls.addAttribute(fontStretch)

        fontAlpha = num_attr.create(
            'fontAlpha',
            'falpha',
            om.MFnNumericData.kFloat
        )
        num_attr.default = 1.0
        num_attr.setMin(0.0)
        num_attr.setMax(1.0)
        num_attr.storable = True
        num_attr.writable = True
        num_attr.channelBox = True
        num_attr.affectsAppearance = True
        cls.addAttribute(fontAlpha)

        fontSize = num_attr.create(
            'fontSize',
            'fsize',
            om.MFnNumericData.kLong
        )
        num_attr.default = 12
        num_attr.storable = True
        num_attr.writable = True
        num_attr.channelBox = True
        num_attr.affectsAppearance = True
        cls.addAttribute(fontSize)

        # textArray attributes

        textString = typ_attr.create(
            'textString',
            'tstr',
            om.MFnData.kString,
            om.MFnStringData().create()
        )
        typ_attr.internal = True

        textAlign = enum_attr.create('textAlign', 'talign')
        for i, alignment in enumerate(ALIGNMENTS):
            enum_attr.addField(alignment, i)
        enum_attr.internal = True

        textOffsetX = num_attr.create(
            'textOffsetX',
            'toffsetx',
            om.MFnNumericData.kLong
        )
        num_attr.internal = True

        textOffsetY = num_attr.create(
            'textOffsetY',
            'toffsety',
            om.MFnNumericData.kLong
        )
        num_attr.internal = True

        textOffset = comp_attr.create('textOffset', 'toffset')
        comp_attr.addChild(textOffsetX)
        comp_attr.addChild(textOffsetY)

        textScale = num_attr.create(
            'textScale',
            'tscale',
            om.MFnNumericData.kFloat
        )
        num_attr.default = 1.0
        num_attr.setMin(0.0)
        num_attr.setMax(10.0)
        num_attr.internal = True

        textColor = num_attr.createColor('textColor', 'tcolor')
        num_attr.internal = True

        textAlpha = num_attr.create(
            'textAlpha',
            'talpha',
            om.MFnNumericData.kFloat
        )
        num_attr.setMin(0.0)
        num_attr.setMax(1.0)
        num_attr.default = 1.0
        num_attr.internal = True

        textFamily = enum_attr.create('textFamily', 'tfamily')
        enum_attr.addField('Use Font Option', USE_FONT_OPTION)
        for i, font in enumerate(FONT_FAMILIES):
            enum_attr.addField(font, i)
        enum_attr.default = USE_FONT_OPTION
        enum_attr.internal = True

        textWeight = enum_attr.create('textWeight', 'tweight')
        enum_attr.addField('Use Font Option', USE_FONT_OPTION)
        for i, weight in FONT_WEIGHTS.items():
            enum_attr.addField(weight, i)
        enum_attr.default = USE_FONT_OPTION
        enum_attr.internal = True

        textStretch = enum_attr.create('textStretch', 'tstretch')
        enum_attr.addField('Use Font Option', USE_FONT_OPTION)
        for i, stretch in FONT_STRETCHES.items():
            enum_attr.addField(stretch, i)
        enum_attr.default = USE_FONT_OPTION
        enum_attr.internal = True

        cls.textArray = comp_attr.create('textArray', 'tarray')
        comp_attr.addChild(textString)
        comp_attr.addChild(textAlign)
        comp_attr.addChild(textOffset)
        comp_attr.addChild(textScale)
        comp_attr.addChild(textColor)
        comp_attr.addChild(textAlpha)
        comp_attr.addChild(textFamily)
        comp_attr.addChild(textWeight)
        comp_attr.addChild(textStretch)
        comp_attr.array = True
        comp_attr.affectsAppearance = True
        cls.addAttribute(cls.textArray)

        # boxArray attributes

        boxType = enum_attr.create('boxType', 'btype')
        for i, type in BOX_TYPES.items():
            enum_attr.addField(type, i)
        enum_attr.internal = True

        boxFill = num_attr.create(
            'boxFill',
            'bfill',
            om.MFnNumericData.kBoolean
        )
        num_attr.default = True
        num_attr.internal = True

        boxAlign = enum_attr.create('boxAlign', 'balign')
        for i, alignment in enumerate(ALIGNMENTS):
            enum_attr.addField(alignment, i)
        enum_attr.internal = True

        boxOffsetX = num_attr.create(
            'boxOffsetX',
            'boffsetx',
            om.MFnNumericData.kLong
        )
        num_attr.internal = True

        boxOffsetY = num_attr.create(
            'boxOffsetY',
            'boffsety',
            om.MFnNumericData.kLong
        )
        num_attr.internal = True

        boxOffset = comp_attr.create('boxOffset', 'boffset')
        comp_attr.addChild(boxOffsetX)
        comp_attr.addChild(boxOffsetY)

        boxSizeX = num_attr.create(
            'boxSizeX',
            'bscalex',
            om.MFnNumericData.kLong
        )
        num_attr.default = 100
        num_attr.internal = True

        boxSizeY = num_attr.create(
            'boxSizeY',
            'bscaley',
            om.MFnNumericData.kLong
        )
        num_attr.default = 100
        num_attr.internal = True

        boxSize = comp_attr.create('boxSize', 'bscale')
        comp_attr.addChild(boxSizeX)
        comp_attr.addChild(boxSizeY)

        boxColor = num_attr.createColor('boxColor', 'bcolor')
        num_attr.internal = True

        boxAlpha = num_attr.create(
            'boxAlpha',
            'balpha',
            om.MFnNumericData.kFloat
        )
        num_attr.setMin(0.0)
        num_attr.setMax(1.0)
        num_attr.default = 0.5
        num_attr.internal = True

        cls.boxArray = comp_attr.create('boxArray', 'barray')
        comp_attr.addChild(boxType)
        comp_attr.addChild(boxFill)
        comp_attr.addChild(boxAlign)
        comp_attr.addChild(boxOffset)
        comp_attr.addChild(boxSize)
        comp_attr.addChild(boxColor)
        comp_attr.addChild(boxAlpha)
        comp_attr.array = True
        comp_attr.affectsAppearance = True
        cls.addAttribute(cls.boxArray)

        # intArray attribute

        cls.intArray = num_attr.create(
            'intArray', 'iarray', om.MFnNumericData.kLong)
        num_attr.storable = True
        num_attr.writable = True
        num_attr.connectable = True
        num_attr.channelBox = True
        num_attr.array = True
        num_attr.usesArrayDataBuilder = True
        comp_attr.affectsAppearance = True
        cls.addAttribute(cls.intArray)

        # floatArray attribute

        cls.floatArray = num_attr.create(
            'floatArray', 'farray', om.MFnNumericData.kDouble)
        num_attr.storable = True
        num_attr.writable = True
        num_attr.connectable = True
        num_attr.channelBox = True
        num_attr.array = True
        num_attr.usesArrayDataBuilder = True
        comp_attr.affectsAppearance = True
        cls.addAttribute(cls.floatArray)


class burninDrawOverride(omr.MPxDrawOverride):

    def __init__(self, obj):
        super(burninDrawOverride, self).__init__(obj, self.draw)
        self.text_data = None
        self.box_data = None
        self.font_options = None

    @classmethod
    def creator(cls, obj):
        return cls(obj)

    @staticmethod
    def draw(context, data):
        return

    def prepareForDraw(self, objPath, camera, frameContext, oldData):
        mobj = objPath.node()
        self.text_data = get_textArray_data(mobj)
        self.box_data = get_boxArray_data(mobj)
        self.font_options = get_font_options(mobj)

    def supportedDrawAPIs(self):
        return (
            omr.MRenderer.kOpenGL |
            omr.MRenderer.kDirectX11 |
            omr.MRenderer.kOpenGLCoreProfile
        )

    def isBounded(self, objPath, cameraPath):
        return False

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        mobj = objPath.node()
        text_data = self.text_data
        box_data = self.box_data
        font_options = self.font_options
        if not text_data or not font_options:
            return

        def get_option(name):
            if text['text' + name] != USE_FONT_OPTION:
                return text['text' + name]
            return font_options['font' + name]

        camera = frameContext.getCurrentCameraPath()
        camera_fn = om.MFnDependencyNode(camera.pop(0).node())
        focal_length = camera_fn.findPlug('focalLength', False).asFloat()
        format_data = get_format_data(
            mobj,
            camera=camera.pop(1).partialPathName(),
            focal_length=focal_length
        )
        dimensions = frameContext.getViewportDimensions()
        view_width = dimensions[2]
        view_height = dimensions[3]

        drawManager.beginDrawable()

        for text in text_data:
            text_size = int(text['textScale'] * font_options['fontSize'])
            line_height = text_size * 1.5
            alpha = text['textAlpha'] * font_options['fontAlpha']
            color = om.MColor(list(text['textColor']) + [alpha])
            family = FONT_FAMILIES[get_option('Family')]
            weight = get_option('Weight')
            stretch = get_option('Stretch')

            try:
                formatted = text['textString'].format(**format_data)
            except:
                formatted = 'Error! Unable to format text string.'

            lines = textString_to_lines(formatted)
            x, y, alignment = get_text_position_and_alignment(
                view_width=view_width,
                view_height=view_height,
                alignment=text['textAlign'],
                line_height=line_height,
                offset=text['textOffset'],
                num_lines=len(lines)
            )

            drawManager.setColor(color)
            drawManager.setFontName(family)
            drawManager.setFontSize(text_size)
            drawManager.setFontWeight(weight)
            drawManager.setFontStretch(stretch)
            for i, line in enumerate(lines):
                drawManager.text2d(
                    om.MPoint(x, y - i * line_height),
                    line,
                    alignment,
                )

        drawManager.endDrawable()

        drawManager.beginDrawable()

        for box in box_data:

            scalex, scaley = box['boxSize']

            box_type = box['boxType']
            if box_type == 1:
                scalex = view_width
            elif box_type == 2:
                scaley = view_height

            x, y = get_box_position(
                view_width=view_width,
                view_height=view_height,
                alignment=box['boxAlign'],
                scale=[scalex, scaley],
                offset=box['boxOffset'],
            )
            fill = box['boxFill']
            up = om.MVector(0, 1, 0)
            color = om.MColor(list(box['boxColor']) + [box['boxAlpha']])
            drawManager.setColor(color)
            drawManager.rect2d(om.MPoint(x, y), up, scalex, scaley, fill)

        drawManager.endDrawable()


def initializePlugin(obj):
    if MAYA_VERSION < 2016:
        raise Exception('burnin only supported in Maya2015 or greater')

    plugin = om.MFnPlugin(obj)

    try:
        plugin.registerNode(
            burnin.type_name,
            burnin.type_id,
            burnin.creator,
            burnin.initialize,
            om.MPxNode.kLocatorNode,
            burnin.type_classification
        )
    except Exception:
        sys.stderr.write('Failed to register node\n')
        raise

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(
            burnin.type_classification,
            burnin.type_name,
            burninDrawOverride.creator
        )
    except Exception:
        sys.stderr.write('Failed to register override\n')
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(burnin.type_id)
    except Exception:
        sys.stderr.write('Failed to deregister node\n')
        raise

    try:
        omr.MDrawRegistry.deregisterDrawOverrideCreator(
            burnin.type_classification,
            burnin.type_name
        )
    except Exception:
        sys.stderr.write('Failed to deregister override\n')
        pass


HELP_STR = '''
Draw text and attribute values in your viewport.
Make use of Python string formatting. Choice of
font and font size are only supported in Viewport 2.0.

Available format data:

    frame:          Current frame
    start:          Start frame
    end:            End frame
    camera:         Current Camera
    focal_length:   Current focal length
    scene:          Current Scene Name
    user:           Current username
    intArray[n]:    Input Ints
    floatArray[n]:  Input Floats
    env[envvar]:    Access to OS Environment Variables


For Example:

{camera}
{frame:0>3d}
{user}
{env[MAYA_LOCATION]}

would wind up looking something like this:

persp
005
dan
/usr/autodesk/maya2017


More information on python string formatting can be found here:
https://docs.python.org/2/library/string.html#format-string-syntax
'''


class AEBurninTemplate(pm.ui.AETemplate):

    _nodeType = burnin.type_name

    def __init__(self, nodeName):
        super(AEBurninTemplate, self).__init__(nodeName)

        self.beginScrollLayout()

        self.beginLayout('Font Options', collapse=False)
        self.addControl('fontFamily')
        self.addControl('fontSize')
        self.addControl('fontWeight')
        self.addControl('fontStretch')
        self.addControl('fontAlpha')
        self.endLayout()

        self.beginLayout("Box Array", collapse=False)
        self.callCustom(
            self.box_array_builder,
            self.box_array_builder,
            "boxArray")
        self.endLayout()

        self.beginLayout("Text Array", collapse=False)
        self.callCustom(
            self.text_array_builder,
            self.text_array_builder,
            "textArray")
        self.endLayout()

        self.beginLayout("Input Arrays", collapse=False)
        self.callCustom(
            self.array_builder,
            self.array_builder,
            'intArray')
        self.callCustom(
            self.array_builder,
            self.array_builder,
            'floatArray')
        self.endLayout()

        self.beginLayout("Help", collapse=True)
        self.callCustom(
            self.create_help_display,
            self.create_help_display)
        self.endLayout()

        self.addExtraControls()
        self.endScrollLayout()

        self.suppress("caching")
        self.suppress("nodeState")

    def array_builder(self, attrName):
        frame = attrName.split('.')[-1]

        if pm.frameLayout(frame, exists=True):
            pm.deleteUI(frame)

        pm.frameLayout(frame, collapse=False)
        pm.rowLayout(numberOfColumns=2)
        acmd = partial(self.add_multiInstance, attrName)
        rcmd = partial(self.rem_multiInstance, attrName)
        pm.button(label='New Item', command=acmd)
        pm.button(label='Remove Last Item', command=rcmd)
        pm.setParent('..')

        array_length = pm.getAttr(attrName, s=True)
        for i in range(array_length):
            index_attr = '{}[{}]'.format(attrName, i)
            pm.attrControlGrp(
                attribute=index_attr,
                label=index_attr.split('.')[-1])
        pm.setParent('..')

    def add_multiInstance(self, attrName, *args):
        array_length = pm.getAttr(attrName, s=True)
        pm.setAttr('{}[{}]'.format(attrName, array_length), 0)

    def rem_multiInstance(self, attrName, *args):
        array_length = pm.getAttr(attrName, s=True)
        pm.removeMultiInstance('{}[{}]'.format(attrName, array_length - 1))

    def text_array_builder(self, attrName):
        frame = 'text_array_frame'

        if pm.columnLayout(frame, exists=True):
            pm.deleteUI(frame)

        pm.columnLayout(frame)
        pm.rowLayout(numberOfColumns=2)

        text_array_length = pm.getAttr(attrName, s=True)
        next_attr = '{}[{}]'.format(attrName, text_array_length)
        add_command = partial(self.add_text_multiInstance, next_attr)
        pm.button(label='New Item', command=add_command)

        last_attr = '{}[{}]'.format(attrName, text_array_length - 1)
        remove_command = partial(self.rem_text_multiInstance, last_attr)
        pm.button(label='Remove Last Item', command=remove_command)

        pm.setParent('..')

        self.textfields = []
        for i in range(text_array_length):
            index_attr = '{}[{}]'.format(attrName, i)
            textString_attr = index_attr + '.textString'
            textAlign_attr = index_attr + '.textAlign'
            textOffset_attr = index_attr + '.textOffset'
            textScale_attr = index_attr + '.textScale'
            textColor_attr = index_attr + '.textColor'
            textAlpha_attr = index_attr + '.textAlpha'
            textFamily_attr = index_attr + '.textFamily'
            textWeight_attr = index_attr + '.textWeight'
            textStretch_attr = index_attr + '.textStretch'

            pm.frameLayout(label=index_attr, collapse=True)
            pm.columnLayout(adj=True)

            text_field = pm.scrollField()
            self.textfields.append(text_field)
            text_field_cmd = partial(
                self.set_string_attr,
                text_field,
                textString_attr
            )
            text_field.changeCommand(text_field_cmd)
            text_field.keyPressCommand(text_field_cmd)
            text_field.setText(pm.getAttr(textString_attr))
            text_field.setEditable(True)

            pm.attrEnumOptionMenuGrp(
                attribute=textAlign_attr, label='textAlign')
            pm.attrFieldGrp(attribute=textOffset_attr, label='textOffset')
            pm.attrControlGrp(attribute=textScale_attr, label='textScale')
            pm.attrControlGrp(attribute=textColor_attr, label='textColor')
            pm.attrControlGrp(attribute=textAlpha_attr, label='textAlpha')
            pm.attrEnumOptionMenuGrp(
                attribute=textFamily_attr, label='textFamily')
            pm.attrEnumOptionMenuGrp(
                attribute=textWeight_attr, label='textWeight')
            pm.attrEnumOptionMenuGrp(
                attribute=textStretch_attr, label='textStretch')

            pm.setParent('..')
            pm.setParent('..')

    def set_string_attr(self, control, attrName, *args):
        value = control.getText()
        pm.setAttr(attrName, value, type="string")

    def add_text_multiInstance(self, attrName, *args):
        pm.setAttr(attrName + '.textAlign', 0)

    def rem_text_multiInstance(self, attrName, *args):
        pm.removeMultiInstance(attrName)

    def box_array_builder(self, attrName):
        frame = 'box_array_frame'

        if pm.columnLayout(frame, exists=True):
            pm.deleteUI(frame)

        pm.columnLayout(frame)
        pm.rowLayout(numberOfColumns=2)

        box_array_length = pm.getAttr(attrName, s=True)
        next_attr = '{}[{}]'.format(attrName, box_array_length)
        add_command = partial(self.add_box_multiInstance, next_attr)
        pm.button(label='New Item', command=add_command)

        last_attr = '{}[{}]'.format(attrName, box_array_length - 1)
        remove_command = partial(self.rem_box_multiInstance, last_attr)
        pm.button(label='Remove Last Item', command=remove_command)

        pm.setParent('..')

        self.boxfields = []
        for i in range(box_array_length):
            index_attr = '{}[{}]'.format(attrName, i)
            boxType_attr = index_attr + '.boxType'
            boxFill_attr = index_attr + '.boxFill'
            boxAlign_attr = index_attr + '.boxAlign'
            boxOffset_attr = index_attr + '.boxOffset'
            boxSize_attr = index_attr + '.boxSize'
            boxColor_attr = index_attr + '.boxColor'
            boxAlpha_attr = index_attr + '.boxAlpha'

            pm.frameLayout(label=index_attr, collapse=True)
            pm.columnLayout(adj=True)

            pm.attrEnumOptionMenuGrp(attribute=boxType_attr, label='boxType')
            pm.attrControlGrp(attribute=boxFill_attr, label='boxFill')
            pm.attrEnumOptionMenuGrp(attribute=boxAlign_attr, label='boxAlign')
            pm.attrFieldGrp(attribute=boxOffset_attr, label='boxOffset')
            pm.attrControlGrp(attribute=boxSize_attr, label='boxSize')
            pm.attrControlGrp(attribute=boxColor_attr, label='boxColor')
            pm.attrControlGrp(attribute=boxAlpha_attr, label='boxAlpha')

            pm.setParent('..')
            pm.setParent('..')

    def add_box_multiInstance(self, attrName, *args):
        pm.setAttr(attrName + '.boxAlign', 0)

    def rem_box_multiInstance(self, attrName, *args):
        pm.removeMultiInstance(attrName)

    def create_help_display(self, *args):
        frame = 'help_frame'

        if pm.columnLayout(frame, exists=True):
            pm.deleteUI(frame)

        pm.columnLayout(frame)
        self.help_field = pm.scrollField()
        self.help_field.setEditable(False)
        self.help_field.setText(HELP_STR)
        pm.setParent('..')
