from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_skeleton.datastructure import Skeleton

__all__ = ['Skeleton']


class Skeleton(Skeleton):
    """Skeleton is a low poly mesh typologically generated from a group of lines."""

    # def to_pattern(self):
    #     """ Generate a form pattern mesh for compas_rv2 and compas_tna. """
    #     from compas_rv2.datastructures import Pattern

    #     mesh = self.to_mesh()
    #     xyz = mesh.vertices_attributes('xyz')
    #     faces = [mesh.face_vertices(fkey) for fkey in mesh.faces()]
    #     pattern = Pattern.from_vertices_and_faces(xyz, faces)

    #     anchor_vertices = self._get_anchor_vertices()
    #     if anchor_vertices:
    #         pattern.vertices_attributes(['is_anchor', 'is_fixed'], [True, True], keys=anchor_vertices)

    #     return pattern

    # def _get_anchor_vertices(self):
    # """ Get default anchor vertices for pattern. """
    # anchor_vertices = []
    # leaf_vertices = list(self.vertices_where({'type': 'skeleton_leaf'}))

    # if not leaf_vertices:  # this is a dome
    #     mesh = self.to_mesh()
    #     anchor_vertices = mesh.vertices_on_boundary()

    # else:
    #     iterations = self.attributes['sub_level']

    #     for key in leaf_vertices:
    #         vertices_on_edge = [key]
    #         for nbr in self.vertex_neighbors(key):
    #             if self.vertex[nbr]['type'] != 'skeleton_node':
    #                 vertices_on_edge.append(nbr)

    #         vertices_temp = [key]
    #         for i in range(iterations):
    #             vertices_temp_2 = []
    #             mesh = self._subdivide(i+1)
    #             for v in vertices_temp:
    #                 for nbr in mesh.vertex_neighbors(v):
    #                     if mesh.vertex_degree(nbr) == 3:
    #                         vertices_on_edge.append(nbr)
    #                         vertices_temp_2.append(nbr)
    #             vertices_temp = vertices_temp_2

    #         anchor_vertices.extend(vertices_on_edge)

    # return anchor_vertices

# ==============================================================================
# Main
# ==============================================================================


if __name__ == '__main__':
    pass
