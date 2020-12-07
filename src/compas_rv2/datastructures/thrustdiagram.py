from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.geometry import subtract_vectors
from compas.geometry import length_vector
from compas.geometry import cross_vectors

from .formdiagram import FormDiagram


__all__ = ['ThrustDiagram']


class ThrustDiagram(FormDiagram):
    """The RV2 ThrustDiagram."""

    def __init__(self, *args, **kwargs):
        super(ThrustDiagram, self).__init__(*args, **kwargs)
        self.attributes.update({
            'name': 'ThrustDiagram',
        })

    def vertex_tributary_area(self, vertex):
        area = 0
        p0 = self.vertex_coordinates(vertex)
        for nbr in self.halfedge[vertex]:
            p1 = self.vertex_coordinates(nbr)
            v1 = subtract_vectors(p1, p0)
            fkey = self.halfedge[vertex][nbr]
            if fkey is not None:
                if self.face_attribute(fkey, '_is_loaded'):
                    p2 = self.face_centroid(fkey)
                    v2 = subtract_vectors(p2, p0)
                    area += length_vector(cross_vectors(v1, v2))
            fkey = self.halfedge[nbr][vertex]
            if fkey is not None:
                if self.face_attribute(fkey, '_is_loaded'):
                    p3 = self.face_centroid(fkey)
                    v3 = subtract_vectors(p3, p0)
                    area += length_vector(cross_vectors(v1, v3))
        return 0.25 * area

    def vertex_lumped_stress(self, vertex):
        stress = 0
        neighbors = self.vertex_neighbors(vertex)
        count = 0
        for nbr in neighbors:
            t = sum(self.vertices_attribute('t', keys=[vertex, nbr])) / 2
            f = self.edge_attribute((vertex, nbr), '_f')
            mp = self.edge_midpoint(vertex, nbr)
            if abs(f) > 0:
                edge_stress = 0
                f0 = self.halfedge_face(vertex, nbr)
                if f0 is not None:
                    if self.face_attribute(f0, '_is_loaded'):
                        f0_c = self.face_center(f0)
                        area = length_vector(subtract_vectors(f0_c, mp)) * t
                        if area > 0:
                            edge_stress += f / area
                f1 = self.halfedge_face(nbr, vertex)
                if f1 is not None:
                    if self.face_attribute(f1, '_is_loaded'):
                        f1_c = self.face_center(f1)
                        area = length_vector(subtract_vectors(f1_c, mp)) * t
                        if area > 0:
                            edge_stress += f / area
                if edge_stress > 0:
                    stress += edge_stress
                    count += 1
        return stress / count


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':
    pass
