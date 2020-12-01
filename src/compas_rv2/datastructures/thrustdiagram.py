from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.geometry import subtract_vectors
from compas.geometry import length_vector
from compas.geometry import cross_vectors

from compas_rv2.datastructures.formdiagram import FormDiagram


__all__ = ['ThrustDiagram']


class ThrustDiagram(FormDiagram):
    """The RV2 ThrustDiagram."""

    def __init__(self, *args, **kwargs):
        super(ThrustDiagram, self).__init__(*args, **kwargs)
        self.attributes.update({
            'name': 'ThrustDiagram',
        })

    def tributary_area(self, vertex):
        area = 0.

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


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':
    pass
