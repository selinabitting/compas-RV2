from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_rhino.conduits import BaseConduit

from compas.geometry import add_vectors
from compas.geometry import scale_vector
from compas.geometry import length_vector_sqrd

from System.Drawing.Color import FromArgb

from Rhino.Geometry import Line
from Rhino.Geometry import Point3d


class SelfWeightConduit(BaseConduit):
    """Display conduit for ThrustDiagram selfweight.

    Parameters
    ----------
    mesh : :class:`compas_rv2.datastructures.ThrustDiagram`
        The thrust diagram.
    color : rgb tuple
        The color of the reaction forces.
    scale : float
        The scale factor.
    tol : float
        Minimum length of a reaction force vector.
    """

    def __init__(self, mesh, color, scale, tol, **kwargs):
        super(SelfWeightConduit, self).__init__(**kwargs)
        self.mesh = mesh
        self.color = color
        self.scale = scale
        self.tol = tol
        self.arrow_size = 0.1

    def DrawForeground(self, e):
        for vertex in self.mesh.vertices():
            ep = self.mesh.vertex_coordinates(vertex)
            area = self.mesh.vertex_tributary_area(vertex)
            thickness = self.mesh.vertex_attribute(vertex, 't')
            weight = area * thickness
            load = scale_vector((0, 0, 1), self.scale * weight)
            if length_vector_sqrd(load) < self.tol ** 2:
                continue
            sp = add_vectors(ep, load)
            line = Line(Point3d(*sp), Point3d(*ep))
            e.Display.DrawArrow(line,
                                FromArgb(*self.color),
                                0,
                                self.arrow_size)


class ReactionConduit(BaseConduit):
    """Display conduit for ThrustDiagram reactions.

    Parameters
    ----------
    mesh : :class:`compas_rv2.datastructures.ThrustDiagram`
        The thrust diagram.
    color : rgb tuple
        The color of the reaction forces.
    scale : float
        The scale factor.
    tol : float
        Minimum length of a reaction force vector.
    """

    def __init__(self, mesh, color, scale, tol, **kwargs):
        super(ReactionConduit, self).__init__(**kwargs)
        self.mesh = mesh
        self.color = color
        self.scale = scale
        self.tol = tol
        self.arrow_size = 0.1

    def DrawForeground(self, e):
        for vertex in self.mesh.vertices_where({'is_anchor': True}):
            ep = self.mesh.vertex_coordinates(vertex)
            r = self.mesh.vertex_attributes(vertex, ['_rx', '_ry', '_rz'])
            r = scale_vector(r, self.scale)
            if length_vector_sqrd(r) < self.tol ** 2:
                continue
            sp = add_vectors(ep, r)
            line = Line(Point3d(*sp), Point3d(*ep))
            e.Display.DrawArrow(line,
                                FromArgb(*self.color),
                                0,
                                self.arrow_size)


class LoadConduit(BaseConduit):
    """Display conduit for ThrustDiagram loads.

    Parameters
    ----------
    mesh : :class:`compas_rv2.datastructures.ThrustDiagram`
        The thrust diagram.
    color : rgb tuple
        The color of the reaction forces.
    scale : float
        The scale factor.
    tol : float
        Minimum length of a reaction force vector.
    """

    def __init__(self, mesh, color, scale, tol, **kwargs):
        super(LoadConduit, self).__init__(**kwargs)
        self.mesh = mesh
        self.color = color
        self.scale = scale
        self.tol = tol
        self.arrow_size = 0.1

    def DrawForeground(self, e):
        for vertex in self.mesh.vertices():
            ep = self.mesh.vertex_coordinates(vertex)
            live = self.mesh.vertex_attribute(vertex, 'pz')
            load = scale_vector((0, 0, 1), self.scale * live)
            if length_vector_sqrd(load) < self.tol ** 2:
                continue
            sp = add_vectors(ep, load)
            line = Line(Point3d(*sp), Point3d(*ep))
            e.Display.DrawArrow(line,
                                FromArgb(*self.color),
                                0,
                                self.arrow_size)


class ResidualConduit(BaseConduit):
    """Display conduit for ThrustDiagram residuals.

    Parameters
    ----------
    mesh : :class:`compas_rv2.datastructures.ThrustDiagram`
        The thrust diagram.
    color : rgb tuple
        The color of the reaction forces.
    scale : float
        The scale factor.
    tol : float
        Minimum length of a reaction force vector.
    """

    def __init__(self, mesh, color, scale, tol, **kwargs):
        super(ResidualConduit, self).__init__(**kwargs)
        self.mesh = mesh
        self.color = color
        self.scale = scale
        self.tol = tol
        self.arrow_size = 0.1

    def DrawForeground(self, e):
        for vertex in self.mesh.vertices_where({'is_anchor': False}):
            ep = self.mesh.vertex_coordinates(vertex)
            r = self.mesh.vertex_attributes(vertex, ['_rx', '_ry', '_rz'])
            r = scale_vector(r, self.scale)
            if length_vector_sqrd(r) < self.tol ** 2:
                continue
            sp = add_vectors(ep, r)
            line = Line(Point3d(*sp), Point3d(*ep))
            e.Display.DrawArrow(line,
                                FromArgb(*self.color),
                                0,
                                self.arrow_size)
