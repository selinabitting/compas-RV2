from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas.geometry import Point
from compas.geometry import Scale
from compas.geometry import Translation
from compas.geometry import Rotation

from .meshobject import MeshObject


__alll__ = ['SubdObject']


class SubdObject(MeshObject):
    """Scene object for subdobject in RV2.
    """

    SETTINGS = {
        'color.edges': [0, 0, 0],
        'nu': 4,
        'nv': 4,
        'n': 2
    }

    @property
    def vertex_xyz(self):
        """dict : The view coordinates of the mesh object."""
        origin = Point(0, 0, 0)
        if self.anchor is not None:
            xyz = self.mesh.vertex_attributes(self.anchor, 'xyz')
            point = Point(* xyz)
            T1 = Translation.from_vector(origin - point)
            S = Scale.from_factors([self.scale] * 3)
            R = Rotation.from_euler_angles(self.rotation)
            T2 = Translation.from_vector(self.location)
            X = T2 * R * S * T1
        else:
            S = Scale.from_factors([self.scale] * 3)
            R = Rotation.from_euler_angles(self.rotation)
            T = Translation.from_vector(self.location)
            X = T * R * S
        mesh = self.mesh.transformed(X)
        vertex_xyz = {vertex: mesh.vertex_attributes(vertex, 'xyz') for vertex in mesh.vertices()}
        return vertex_xyz

    def draw(self):
        """Draw the objects representing the force diagram.
        """
        layer = self.settings['layer']
        self.artist.layer = layer
        self.artist.clear_layer()
        self.clear()
        if not self.visible:
            return
        self.artist.vertex_xyz = self.vertex_xyz

        # edges
        edges = list(self.mesh.edges())
        color = {edge: self.settings['color.edges'] for edge in edges}

        guids = self.artist.draw_edges(edges, color)
        self.guid_edge = zip(guids, edges)

        # draw subd mesh as conduit

        # draw edge labels
