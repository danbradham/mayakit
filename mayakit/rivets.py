# -*- coding: utf-8 -*-

import pymel.core as pmc
import pymel.core.nodetypes as nodetypes


def get_surface(node):

    if isinstance(node, nodetypes.Transform):
        node = node.getShape(noIntermediate=True)

    if isinstance(node, (nodetypes.NurbsSurface, nodetypes.Mesh)):
        return node

    raise ValueError('node must be NurbsSurface or Mesh...')


class Follicle(object):
    '''Wrapper around follicle shape nodes...

    Makes it real easy to create and attach follicles'''

    def __init__(self, xform, shape):
        self.xform = xform
        self.shape = shape
        self.u = self.shape.parameterU
        self.v = self.shape.parameterV

    @classmethod
    def create(cls):
        shape = pmc.createNode('follicle')
        xform = shape.getParent()

        shape.outTranslate >> xform.translate
        shape.outRotate >> xform.rotate
        return cls(xform, shape)

    @classmethod
    def create_on_surface(cls, surface, uvlist):
        follicles = []
        for i, uvs in enumerate(uvlist):
            f = cls.create()
            f.rename('surfacePoint_{:0>2}'.format(i + 1))
            f.attach(surface)
            f.set_uvs(*uvs)
            follicles.append(f)

        return follicles

    def __str__(self):
        return str(self.xform)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<{}>({}, {})'.format(cls_name, self.xform, self.shape)

    def rename(self, name):
        self.xform.rename(name)

    def _attach_nurbs(self, surface):
        surface.worldSpace >> self.shape.inputSurface

    def _attach_mesh(self, surface):
        surface.worldMesh >> self.shape.inputMesh
        surface.worldMatrix >> self.shape.inputWorldMatrix

    def attach(self, surface):
        surface = get_surface(surface)
        surface_type = type(surface)

        attach_method = {
            nodetypes.NurbsSurface: self._attach_nurbs,
            nodetypes.Mesh: self._attach_mesh,
        }.get(surface_type)

        if not attach_method:
            raise Exception("Can't attach follicle to a " + str(surface_type))

        attach_method(surface)

    def set_uvs(self, u=None, v=None):
        if u:
            self.u.set(u)
        if v:
            self.v.set(v)

    def get_uvs(self):
        return self.u.get(), self.v.get()


def uv_range(n, along_u=True):

    step = 1.0 / (n - 1.0)
    for i in range(n):
        u, v = 0.5, i * step
        if along_u:
            v, u = u, v
        yield u, v


def get_closest_uv(surface, point):
    surface = get_surface(surface)

    if isinstance(surface, nodetypes.NurbsSurface):
        _, u, v = surface.closestPoint(point, space='world')
        return u / surface.numSpansInU(), v / surface.numSpansInV()

    if isinstance(surface, nodetypes.Mesh):
        return surface.getUVAtPoint(point)


def attach_selected_to_surface():

    selection = pmc.selected()
    transforms = selection[:-1]
    surface = selection[-1]
    with pmc.UndoChunk():
        return attach_to_surface(transforms, surface)


def attach_to_surface(transforms, surface):

    if isinstance(transforms[0], basestring):
        transforms = [pmc.PyNode(t) for t in transforms]
    if isinstance(surface, basestring):
        surface = pmc.PyNode(surface)

    created = []
    for transform in transforms:
        p = pmc.xform(transform, query=True, worldSpace=True, rotatePivot=True)
        uv = get_closest_uv(surface, p)
        follicle = Follicle.create()
        follicle.attach(surface)
        follicle.set_uvs(*uv)
        follicle.rename('rivet#')
        created.append(follicle)

    return created


if __name__ == '__main__':

    with pmc.UndoChunk():
        surface = pmc.selected()[0]
        Follicle.create_on_surface(surface, uv_range(9))
