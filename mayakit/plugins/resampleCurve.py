import maya.api.OpenMaya as om
import pymel.core as pmc
import sys
from functools import partial


def maya_useNewAPI():
    pass


def linspace(tmin, tmax, n):
    '''Clone of numpy.linspace'''

    output = []
    spread = tmax - tmin
    step = spread / (n - 1)
    for i in range(n):
        output.append(tmin + step * i)
    return output


def compute_knots(num_points, degree, array_typ=om.MDoubleArray):
    '''Compute knots for the given number of points '''

    num_knots = num_points + degree - 1
    knots = array_typ()
    for i in range(degree):
        knots.append(0)
    for i in range(num_knots - degree * 2):
        knots.append(i + 1)
    for j in range(degree):
        knots.append(i + 2)  # exploit leaked reference
    return knots


class resampleCurve(om.MPxNode):

    id_ = om.MTypeId(0x00124dff)

    def __init__(self):
        super(resampleCurve, self).__init__()

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

        cls.numPoints = num_attr.create('numPoints', 'np', om.MFnNumericData.kInt)
        num_attr.storable = True
        num_attr.keyable = True
        num_attr.readable = True
        num_attr.writable = True
        num_attr.setMin(1)
        num_attr.default = 20
        cls.addAttribute(cls.numPoints)

        cls.tmin = num_attr.create('tMinimum', 'tmin', om.MFnNumericData.kDouble)
        num_attr.storable = True
        num_attr.keyable = True
        num_attr.readable = True
        num_attr.writable = True
        num_attr.setMin(0)
        num_attr.setMax(1)
        num_attr.default = 0
        cls.addAttribute(cls.tmin)

        cls.tmax = num_attr.create('tMaximum', 'tmax', om.MFnNumericData.kDouble)
        num_attr.storable = True
        num_attr.keyable = True
        num_attr.readable = True
        num_attr.writable = True
        num_attr.setMin(0)
        num_attr.setMax(1)
        num_attr.default = 1
        cls.addAttribute(cls.tmax)

        cls.degree = enum_attr.create('degree','deg')
        enum_attr.storable = True
        enum_attr.keyable = True
        enum_attr.readable = True
        enum_attr.writable = True
        enum_attr.addField('input', 0)
        enum_attr.addField('linear', 1)
        cls.addAttribute(cls.degree)

        cls.attributeAffects(cls.inputCurve, cls.outputCurve)
        cls.attributeAffects(cls.numPoints, cls.outputCurve)
        cls.attributeAffects(cls.degree, cls.outputCurve)
        cls.attributeAffects(cls.tmin, cls.outputCurve)
        cls.attributeAffects(cls.tmax, cls.outputCurve)

    def compute(self, plug, data):

        if plug == self.outputCurve:

            in_curve_handle = data.inputValue(self.inputCurve)
            in_curve = in_curve_handle.asNurbsCurveTransformed()
            in_curve_fn = om.MFnNurbsCurve(in_curve)
            in_spans = in_curve_fn.numSpans
            in_degree = in_curve_fn.degree
            in_form = in_curve_fn.form

            tmin = data.inputValue(self.tmin).asDouble()
            tmax = data.inputValue(self.tmax).asDouble()
            out_degree = (in_degree, 1)[data.inputValue(self.degree).asInt()]

            # Compute output data
            out_num_points = data.inputValue(self.numPoints).asInt()
            out_spans = out_num_points - 1
            out_knots = compute_knots(out_num_points, out_degree)

            params = linspace(tmin * in_spans, tmax * in_spans, out_num_points)
            if tmax > 0.9999:
                params[-1] = in_spans

            out_points = om.MPointArray()
            for t in params:
                out_points.append(in_curve_fn.getPointAtParam(t))

            # Create output curve
            out_curve_data = om.MFnNurbsCurveData().create()
            out_curve_fn = om.MFnNurbsCurve()
            out_curve_fn.create(
                out_points,
                out_knots,
                out_degree,
                om.MFnNurbsCurve.kOpen,
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
            resampleCurve.__name__,
            resampleCurve.id_,
            resampleCurve.creator,
            resampleCurve.initialize
        )
    except:
        sys.stderr.write("Failed to register node\n")
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(resampleCurve.id_)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise


class AEresampleCurveTemplate(pmc.ui.AETemplate):
    _nodeType = 'resampleCurve'

    def __init__(self, node_name):
        self.curve_controls = {}

        self.beginScrollLayout()

        self.beginLayout('Resample Curve', collapse=False)
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
        self.addControl('numPoints')
        self.addControl('degree')
        self.addControl('tMinimum')
        self.addControl('tMaximum')
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
