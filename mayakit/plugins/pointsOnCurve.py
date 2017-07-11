from __future__ import division
import maya.api.OpenMaya as om
import pymel.core as pmc
import sys


def maya_useNewAPI():
    pass


def linspace(tmin, tmax, n):
    '''Clone of numpy.linspace'''

    output = []
    spread = tmax - tmin
    step = spread / (n - 1.0)
    for i in xrange(n):
        output.append(tmin + step * i)
    print output
    return output


class pointsOnCurve(om.MPxNode):

    id_ = om.MTypeId(0x00124dfb)

    def __init__(self):
        super(pointsOnCurve, self).__init__()

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):

        typ_attr = om.MFnTypedAttribute()
        num_attr = om.MFnNumericAttribute()
        mat_attr = om.MFnMatrixAttribute()

        cls.incurve = typ_attr.create('inCurve', 'ic', om.MFnData.kNurbsCurve)
        typ_attr.storable = True
        typ_attr.keyable = False
        typ_attr.readable = True
        typ_attr.writable = True
        typ_attr.cached = False
        cls.addAttribute(cls.incurve)

        cls.outposition = typ_attr.create('outPosition', 'op', om.MFnData.kPointArray)
        typ_attr.storable = True
        typ_attr.keyable = False
        typ_attr.readable = True
        typ_attr.writable = True
        typ_attr.cached = False
        cls.addAttribute(cls.outposition)

        cls.outnormal = typ_attr.create('outNormal', 'on', om.MFnData.kVectorArray)
        typ_attr.storable = True
        typ_attr.keyable = False
        typ_attr.readable = True
        typ_attr.writable = True
        typ_attr.cached = False
        cls.addAttribute(cls.outnormal)

        cls.outtangent = typ_attr.create('outTangent', 'ot', om.MFnData.kVectorArray)
        typ_attr.storable = True
        typ_attr.keyable = False
        typ_attr.readable = True
        typ_attr.writable = True
        typ_attr.cached = False
        cls.addAttribute(cls.outtangent)

        cls.outbitangent = typ_attr.create('outBitangent', 'ob', om.MFnData.kVectorArray)
        typ_attr.storable = True
        typ_attr.keyable = False
        typ_attr.readable = True
        typ_attr.writable = True
        typ_attr.cached = False
        cls.addAttribute(cls.outbitangent)

        cls.outmatrx = mat_attr.create('outMatrix', 'om', om.MFnMatrixAttribute.kDouble)
        mat_attr.storable = True
        mat_attr.keyable = False
        mat_attr.readable = True
        mat_attr.writable = True
        mat_attr.hidden = False
        mat_attr.array = True
        mat_attr.usesArrayDataBuilder = True
        cls.addAttribute(cls.outmatrix)

        cls.numpoints = num_attr.create('numPoints', 'np', om.MFnNumericData.kInt)
        num_attr.storable = True
        num_attr.keyable = True
        num_attr.readable = True
        num_attr.writable = True
        num_attr.setMin(1)
        num_attr.default = 20
        cls.addAttribute(cls.numpoints)

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

        cls.ushift = num_attr.create('uShift', 'us', om.MFnNumericData.kDouble)
        num_attr.storable = True
        num_attr.keyable = True
        num_attr.readable = True
        num_attr.writable = True
        cls.addAttribute(cls.ushift)

        cls.loop = num_attr.create('loop', 'lp', om.MFnNumericData.kBoolean)
        num_attr.storable = True
        num_attr.keyable = True
        num_attr.readable = True
        num_attr.writable = True
        num_attr.default = 1
        cls.addAttribute(cls.loop)

        cls.attributeAffects(cls.incurve, cls.outmatrix)
        cls.attributeAffects(cls.numpoints, cls.outmatrix)
        cls.attributeAffects(cls.tmin, cls.outmatrix)
        cls.attributeAffects(cls.tmax, cls.outmatrix)
        cls.attributeAffects(cls.ushift, cls.outmatrix)
        cls.attributeAffects(cls.loop, cls.outmatrix)

    def compute(self, plug, data):

        this = self.thisMObject()

        if plug == self.outmatrix:

            curve_handle = data.inputValue(self.incurve)
            curve = curve_handle.asNurbsCurveTransformed()
            curve_fn = om.MFnNurbsCurve(curve)
            curve_spans = curve_fn.numSpans

            tmin = data.inputValue(self.tmin).asDouble()
            tmax = data.inputValue(self.tmax).asDouble()
            ushift = data.inputValue(self.ushift).asDouble()
            loop = data.inputValue(self.loop).asDouble()

            # Get parameters to sample along incurve
            numpoints = data.inputValue(self.numpoints).asInt()
            params = linspace(
                tmin * curve_spans,
                tmax * curve_spans,
                numpoints
            )

            # Create output arrays
            positions = om.MPointArray()
            tangents = om.MVectorArray()
            bitangents = om.MVectorArray()
            normals = om.MVectorArray()
            matrices = om.MMatrixArray()
            N = om.MVector(0, 1, 0)
            for param in params:
                param = (param + ushift) % curve_spans
                P = curve_fn.getPointAtParam(param, om.MSpace.kObject)
                T = curve_fn.tangent(param, om.MSpace.kObject).normal()

                # N = curve_fn.normal(param, om.MSpace.kObject)
                # P, T, N = curve_fn.getDerivativesAtParam(param, om.MSpace.kObject, True)
                B = (T ^ N).normal()
                N = (B ^ T).normal()
                M = om.MMatrix([
                    T.x, T.y, T.z, 0,
                    B.x, B.y, B.z, 0,
                    N.x, N.y, N.z, 0,
                    P.x, P.y, P.z, 1
                ])
                positions.append(P)
                normals.append(N)
                tangents.append(T)
                bitangents.append(B)
                matrices.append(M)

            # Set output attributes
            outmatrix_handle = data.outputArrayValue(self.outmatrix)
            outmatrix_builder = om.MArrayDataBuilder(data, self.outmatrix, numpoints)

            outmatrix_builder.growArray(len(matrices))
            for i, m in enumerate(matrices):
                mhandle = outmatrix_builder.addElement(i)
                mhandle.setMMatrix(m)

            outmatrix_handle.set(outmatrix_builder)
            outmatrix_handle.setAllClean()

            # # Setting typed attributes is much nicer...
            # outposition_handle = data.outputValue(self.outposition)
            # outposition_data = om.MFnPointArrayData(outposition_handle.data())
            # outposition_data.set(positions)

            # outnormal_handle = data.outputValue(self.outnormal)
            # outnormal_data = om.MFnVectorArrayData(outnormal_handle.data())
            # outnormal_data.set(normals)

            # outtangent_handle = data.outputValue(self.outtangent)
            # outtangent_data = om.MFnVectorArrayData(outtangent_handle.data())
            # outtangent_data.set(tangents)

            # outbitangent_handle = data.outputValue(self.outbitangent)
            # outbitangent_data = om.MFnVectorArrayData(outbitangent_handle.data())
            # outbitangent_data.set(bitangents)

            data.setClean(self.outmatrix)
            data.setClean(self.outposition)
            data.setClean(self.outnormal)
            data.setClean(self.outtangent)
            data.setClean(self.outbitangent)


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.registerNode(
            pointsOnCurve.__name__,
            pointsOnCurve.id_,
            pointsOnCurve.creator,
            pointsOnCurve.initialize
        )
    except:
        sys.stderr.write("Failed to register node\n")
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(pointsOnCurve.id_)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise


class AEpointsOnCurveTemplate(pmc.ui.AETemplate):
    _nodeType = pointsOnCurve.__name__

    def __init__(self, node_name):
        self.curve_controls = {}

        self.beginScrollLayout()

        self.beginLayout('pointsOnCurve', collapse=False)
        self.callCustom(
            self.curve_create,
            self.curve_update,
            'inCurve'
        )
        self.addControl('numPoints')
        self.addControl('tMinimum')
        self.addControl('tMaximum')
        self.addControl('uShift')
        self.addControl('loop')
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
