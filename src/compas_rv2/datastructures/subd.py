from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas.datastructures import Mesh
from compas.utilities import pairwise
from copy import deepcopy

__all__ = ['Subd']


def mesh_fast_copy(other):
    subd = Mesh()
    subd.vertex = deepcopy(other.vertex)
    subd.face = deepcopy(other.face)
    subd.facedata = deepcopy(other.facedata)
    subd.halfedge = deepcopy(other.halfedge)
    subd._max_face = other._max_face
    subd._max_vertex = other._max_vertex
    return subd


def edge_strip(mesh, uv):
    """ find other edges on the same strip of the input edge """
    edges = []
    v, u = uv
    while True:
        edges.append((u, v))
        fkey = mesh.halfedge[u][v]
        if fkey is None:
            break
        vertices = mesh.face_vertices(fkey)
        if len(vertices) != 4:
            break
        i = vertices.index(u)
        u = vertices[i - 1]
        v = vertices[i - 2]
    edges[:] = [(u, v) for v, u in edges[::-1]]
    u, v = uv
    while True:
        fkey = mesh.halfedge[u][v]
        if fkey is None:
            break
        vertices = mesh.face_vertices(fkey)
        if len(vertices) != 4:
            break
        i = vertices.index(u)
        u = vertices[i - 1]
        v = vertices[i - 2]
        edges.append((u, v))
    return edges


def strip_edges(mesh):
    """ create a dict to categorize edges based on the strips """
    edges = list(mesh.edges())

    strips = {}
    index = -1
    while len(edges) > 0:
        index += 1
        u0, v0 = edges.pop()
        strip = edge_strip(mesh, (u0, v0))
        strips.update({index: strip})

        for u, v in strip:
            if (u, v) in edges:
                edges.remove((u, v))
            elif (v, u) in edges:
                edges.remove((v, u))

    return strips


def mesh_split_edge(mesh, u, v, n=2):

    fkey_uv = mesh.halfedge[u][v]
    fkey_vu = mesh.halfedge[v][u]

    insert_keys = [u]
    for i in range(n)[1:]:
        t = 1/n * i

        # coordi= menates
        x, y, z = mesh.edge_point(u, v, t)

        # the split vertex
        w = mesh.add_vertex(x=x, y=y, z=z)
        insert_keys.append(w)

    insert_keys.append(v)
    # split half-edge UV
    for a, b in pairwise(insert_keys):
        mesh.halfedge[a][b] = fkey_uv

    del mesh.halfedge[u][v]

    # update the UV face if it is not the `None` face
    if fkey_uv is not None:
        j = mesh.face[fkey_uv].index(v)
        for w in insert_keys[::-1][1:-1]:
            mesh.face[fkey_uv].insert(j, w)

    # split half-edge VU
    for b, a in pairwise(insert_keys[::-1]):
        mesh.halfedge[b][a] = fkey_vu

    del mesh.halfedge[v][u]

    # update the VU face if it is not the `None` face
    if fkey_vu is not None:
        i = mesh.face[fkey_vu].index(u)
        for w in insert_keys[1:-1]:
            mesh.face[fkey_vu].insert(i, w)

    return insert_keys


def mesh_split_edges(mesh, edges, n):
    subd = mesh_fast_copy(mesh)
    for u, v in edges:
        mesh_split_edge(subd, u, v, n)

    return subd


def mesh_subdivide_strip(mesh, uv, n):

    edges = edge_strip(mesh, uv)
    subd = mesh_split_edges(mesh, edges, n)

    for u, v in edges:
        fkey = mesh.halfedge[u][v]
        if fkey is None:
            continue

        # add faces
        face = subd.face[fkey]
        n = len(face)
        i = face.index(u)

        for w in range(int(n/2-1)):
            subd.add_face([face[(w+i) % n], face[(w+1+i) % n], face[(n-w-2+i) % n], face[(n-w-1+i) % n]])

        del subd.face[fkey]
        del subd.facedata[fkey]

    return subd


class Subd(Mesh):
    """ Subd is a mesh storing coarse mesh and its subdivision """

    def __init__(self):
        super(Subd, self).__init__()
        self._strip_edges = {}
        self._strip_division = {}
        self.subd_mesh = None

    # ----------------------------------------------------------------------
    # properties
    # ----------------------------------------------------------------------

    # ----------------------------------------------------------------------
    # constructors
    # ----------------------------------------------------------------------

    @classmethod
    def from_mesh(cls, mesh):
        """ Create a Subd from a compas mesh.

        Parameters
        ----------
        lines: :class:`compas.datastructrues.Mesh`
            a compas mesh

        Return
        ------
        Subd: :class:`compas_RV2.datastructure.Subd`
            a Subd mesh
        """
        subd = cls()
        subd.vertex = deepcopy(mesh.vertex)
        subd.face = deepcopy(mesh.face)
        subd.facedata = deepcopy(mesh.facedata)
        subd.halfedge = deepcopy(mesh.halfedge)
        subd._max_face = mesh._max_face
        subd._max_vertex = mesh._max_vertex

        subd._strip_edges = strip_edges(subd)
        subd._get_default_strip_subdvision()

        return subd

    def _get_default_strip_subdvision(self):
        """get subdivision number for each strip by user input target length"""
        total_length = 0
        default_n = 10.0
        for u, v in self.edges():
            total_length += self.edge_length(u, v)

        target_length = total_length/self.number_of_edges()/default_n

        for i, edges in self._strip_edges.items():
            edge0 = edges[0]
            n = int(self.edge_length(*edge0) / target_length)

            self._strip_division.update({i: n})

    def get_subd(self):
        """get subdivided mesh based on the division of each strip"""
        subd_temp = self
        for i, edges in self._strip_edges.items():
            n = self._strip_division[i]
            subd_temp = mesh_subdivide_strip(subd_temp, edges[0], n)

        self.subd_mesh = subd_temp

    # ----------------------------------------------------------------------
    # modification
    # ----------------------------------------------------------------------

    def change_division(self, edge, n):
        """change subdivision for a strip"""
        for i, edges in self._strip_edges.items():
            if (edge[0], edge[1]) in edges or (edge[1], edge[0]) in edges:
                break

        self._strip_division.update({i: n})


if __name__ == "__main__":
    pass
