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
import pymel.core as pm

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


def maya_useNewAPI():
    pass


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


def textString_to_lines(textString):
    '''Splits a unicode textString into lines'''

    return repr(textString)[2:-1].replace('\\t', '    ').split('\\n')


def get_text_position_and_alignment(view_width, view_height, alignment,
                                    line_height, offset, num_lines):
    '''Get the position of where to start drawing text and the
    alignment of the text.
    '''

    if alignment in (0, 3, 6):
        x = line_height + offset[0]
        align = 0 # kLeft
    elif alignment in (1, 4, 7):
        x = int(view_width * 0.5 - offset[0])
        align = 1 # kCenter
    else:
        x = view_width - line_height - offset[0]
        align = 2 # kRight

    if alignment < 3:
        y = view_height - line_height - offset[1]
    elif alignment < 6:
        y = int(view_height * 0.5 + (num_lines * 0.5 * line_height) - offset[1])
    else:
        y = line_height + (num_lines * line_height) + offset[1]

    return x, y, align


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
        format_data = get_format_data(
            self.thisMObject(),
            camera=camera.pop(1).partialPathName()
        )
        line_height = 20
        view_width = view.portWidth()
        view_height = view.portHeight()

        view.beginGL()

        for text in text_data:
            try:
                formatted = text['textString'].format(**format_data)
            except:
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

        textString = typ_attr.create(
            'textString',
            "tstr",
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

        cls.intArray = num_attr.create(
            "intArray", "iarray", om.MFnNumericData.kLong)
        num_attr.storable = True
        num_attr.writable = True
        num_attr.connectable = True
        num_attr.channelBox = True
        num_attr.array = True
        num_attr.usesArrayDataBuilder = True
        comp_attr.affectsAppearance = True
        cls.addAttribute(cls.intArray)

        cls.floatArray = num_attr.create(
            "floatArray", "farray", om.MFnNumericData.kDouble)
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
        print 'burninDrawOverride.__init__'
        self.text_data = None
        self.font_options = None

    @classmethod
    def creator(cls, obj):
        return burninDrawOverride(obj)

    @classmethod
    def draw(cls, context, data):
        return

    def prepareForDraw(self, objPath, camera, frameContext, oldData):
        mobj = objPath.node()
        self.text_data = get_textArray_data(mobj)
        self.font_options = get_font_options(mobj)

    def supportedDrawAPIs(self):
        return (
            omr.MRenderer.kOpenGL|
            omr.MRenderer.kDirectX11|
            omr.MRenderer.kOpenGLCoreProfile
        )

    def isBounded(self, objPath, cameraPath):
        return False

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        mobj = objPath.node()
        text_data = self.text_data
        font_options = self.font_options
        if not text_data or not font_options:
            return

        def get_option(name):
            if text['text' + name] != USE_FONT_OPTION:
                return text['text' + name]
            return font_options['font' + name]

        camera = frameContext.getCurrentCameraPath()
        format_data = get_format_data(
            mobj,
            camera=camera.pop(1).partialPathName()
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


def initializePlugin(obj):
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
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(
            burnin.type_classification,
            burnin.type_name,
            burninDrawOverride.creator
        )
    except:
        sys.stderr.write("Failed to register override\n")
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(burnin.type_id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise

    try:
        omr.MDrawRegistry.deregisterDrawOverrideCreator(
            burnin.type_classification,
            burnin.type_name
        )
    except:
        sys.stderr.write("Failed to deregister override\n")
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

        #Template layout
        self.textfields = []
        self.beginScrollLayout()

        self.beginLayout('Font Options', collapse=False)
        self.addControl('fontFamily')
        self.addControl('fontSize')
        self.addControl('fontWeight')
        self.addControl('fontStretch')
        self.addControl('fontAlpha')
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
        for i in xrange(array_length):
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
        for i in xrange(text_array_length):
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

            pm.frameLayout(label=index_attr, collapse=False)
            pm.columnLayout(adj=True)

            text_field = pm.scrollField()
            self.textfields.append(text_field)
            text_field_cmd = partial(self.set_string_attr, text_field, textString_attr)
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

    def create_help_display(self, *args):
        self.help_field = pm.scrollField()
        self.help_field.setEditable(False)
        self.help_field.setText(HELP_STR)
