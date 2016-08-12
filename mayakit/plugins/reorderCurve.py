import maya.api.OpenMaya as om
import pymel.core as pmc
from random import shuffle
from collections import deque
from functools import partial
from . import utils
import sys


load = partial(utils.load_plugin, 'reorderCurve')
unload = partial(utils.unload_plugin, 'reorderCurve')
reload = partial(utils.reload_plugin, 'reorderCurve')
is_loaded = partial(utils.is_loaded, 'reorderCurve')


def maya_useNewAPI():
    pass


def rotate_array(array, steps):
    '''Rotate array by i steps'''

    array_typ = type(array)
    d = deque(array)
    d.rotate(steps)
    return array_typ(d)


def shuffle_array(array):
    '''Shuffle Array'''

    array_typ = type(array)
    s = list(array)
    shuffle(s)
    return array_typ(s)


def reverse_array(array):
    '''Reverse Array'''

    array_typ = type(array)
    return array_typ(list(reversed(array)))


class reorderCurve(om.MPxNode):

    id_ = om.MTypeId(0x00124dfd)

    def __init__(self):
        super(reorderCurve, self).__init__()

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):

        typ_attr = om.MFnTypedAttribute()
        num_attr = om.MFnNumericAttribute()
        enum_attr = om.MFnEnumAttribute()

        cls.inputCurve = typ_attr.create('inputCurve', 'ic', om.MFnData.kNurbsCurve)
        typ_attr.storable = True
        typ_attr.keyable = False
        typ_attr.readable = True
        typ_attr.writable = True
        typ_attr.cached = False
        cls.addAttribute(cls.inputCurve)

        cls.outputCurve = typ_attr.create('outputCurve', 'oc', om.MFnData.kNurbsCurve)
        typ_attr.storable = True
        typ_attr.keyable = False
        typ_attr.readable = True
        typ_attr.writable = True
        typ_attr.cached = False
        cls.addAttribute(cls.outputCurve)

        cls.method = enum_attr.create('method','mth')
        enum_attr.addField('rotate', 0)
        enum_attr.addField('random', 1)
        enum_attr.addField('reverse', 2)
        cls.addAttribute(cls.method)

        cls.rotateSteps = num_attr.create('rotateSteps', 'ros', om.MFnNumericData.kInt)
        num_attr.storable = True
        num_attr.keyable = True
        num_attr.readable = True
        num_attr.writable = True
        cls.addAttribute(cls.rotateSteps)

        cls.attributeAffects(cls.inputCurve, cls.outputCurve)
        cls.attributeAffects(cls.method, cls.outputCurve)
        cls.attributeAffects(cls.rotateSteps, cls.outputCurve)

    def compute(self, plug, data):

        if plug == self.outputCurve:

            in_curve_handle = data.inputValue(self.inputCurve)
            in_curve = in_curve_handle.asNurbsCurveTransformed()
            in_curve_fn = om.MFnNurbsCurve(in_curve)
            in_spans = in_curve_fn.numSpans
            in_degree = in_curve_fn.degree
            in_form = in_curve_fn.form
            in_knots = in_curve_fn.knots()
            in_points = in_curve_fn.cvPositions()

            method = data.inputValue(self.method).asInt()
            if method == 0: # use rotate method
                steps = data.inputValue(self.rotateSteps).asInt()
                out_points = rotate_array(in_points, steps)
            elif method == 1: # use random method
                out_points = shuffle_array(in_points)
            else:
                out_points = reverse_array(in_points)

            # Create output curve
            out_curve_data = om.MFnNurbsCurveData().create()
            out_curve_fn = om.MFnNurbsCurve()
            out_curve_fn.create(
                out_points,
                in_knots,
                in_degree,
                in_form,
                False,
                True,
                out_curve_data
            )

            # set output curve handles mobject
            out_curve_handle = data.outputValue(self.outputCurve)
            out_curve_handle.setMObject(out_curve_data)
            data.setClean(plug)


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.registerNode(
            reorderCurve.__name__,
            reorderCurve.id_,
            reorderCurve.creator,
            reorderCurve.initialize
        )
    except:
        sys.stderr.write("Failed to register node\n")
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(reorderCurve.id_)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise


class AEreorderCurveTemplate(pmc.ui.AETemplate):
    _nodeType = 'reorderCurve'

    def __init__(self, node_name):
        self.curve_controls = {}

        self.beginScrollLayout()

        self.beginLayout('Reorder Curve', collapse=False)
        self.callCustom(
            self.curve_create,
            self.curve_update,
            'inputCurve'
        )
        self.callCustom(
            self.curve_create,
            self.curve_update,
            'outputCurve'
        )
        self.addControl('method')
        self.addControl('rotateSteps')
        self.endLayout()

        self.addExtraControls()

        self.endScrollLayout()

    def get_curve_connection(self, attr):
        connections = pmc.listConnections(attr)
        if connections:
            return connections[0]
        return ''

    def curve_create(self, attr):
        pmc.rowLayout(nc=2)
        pmc.text(label=attr.split('.')[-1])
        curve_field = pmc.textField(
            editable=False,
            text=self.get_curve_connection(attr)
        )
        self.curve_controls[attr] = curve_field

    def curve_update(self, attr):
        pmc.textField(
            self.curve_controls[attr],
            edit=True,
            text=self.get_curve_connection(attr)
        )
