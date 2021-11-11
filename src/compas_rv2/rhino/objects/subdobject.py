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
