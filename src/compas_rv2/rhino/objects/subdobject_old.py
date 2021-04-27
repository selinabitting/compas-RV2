from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from copy import deepcopy

import compas_rhino
from compas_rhino.objects import BaseObject
from compas_rhino.artists import MeshArtist
from compas_rhino.geometry import RhinoSurface
from compas_rhino import delete_objects
from compas.datastructures import Mesh
from compas.utilities import pairwise

import rhinoscriptsyntax as rs


__all__ = ['SubdObject']


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


def edge_strips(mesh):
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


class SubdObject(BaseObject):

    SETTINGS = {
        'layer': "RV2::Subd",
        'layer.coarse': "RV2::Subd::coarse",
        'layer.subd': "RV2::Subd::subd",
        'color.vertices': (255, 255, 255),
        'color.edges': (0, 0, 0),
        'color.faces': (0, 0, 0),
        'color.mesh': (0, 0, 0),
        'color.subd.edges': (120, 120, 120),
        'show.mesh': True,
        'show.vertices': True,
        'show.edges': True,
        'show.faces': False,
    }

    def __init__(self, coarse=None, scene=None, name=None, layer=None, visible=True, settings=None):
        super(SubdObject, self).__init__(coarse, scene, name, layer, visible)
        self._subd = None
        self._guids = []
        self._guid_coarse_vertex = {}
        self._guid_coarse_edge = {}
        self._guid_subd_edge = {}
        self._guid_label = {}
        self._guid_subd = {}
        self._edge_strips = {}
        self._strip_division = {}
        self._guid_strip_division = {}
        self._anchor = None
        self._location = None
        self._scale = None
        self._rotation = None
        self.settings.update(type(self).SETTINGS)
        if settings:
            self.settings.update(settings)

    # ----------------------------------------------------------------------
    # properties
    # ----------------------------------------------------------------------

    @property
    def coarse(self):
        return self.item

    @coarse.setter
    def coarse(self, coarse):
        self.item = coarse
        self._guids = []
        self._guid_coarse_vertex = {}
        self._guid_coarse_edge = {}
        self._edge_strips = edge_strips(self.item)
        self._guid_label = {}

    @property
    def subd(self):
        return self._subd

    @subd.setter
    def subd(self, subd):
        self._subd = subd
        self._guid_subd_edge = {}
        self._guid_subd = {}
        self._guid_strip_division = {}

    @property
    def guid_coarse_edge(self):
        return self._guid_coarse_edge

    @guid_coarse_edge.setter
    def guid_coarse_edge(self, values):
        self._guid_coarse_edge = dict(values)

    @property
    def guid_label(self):
        return self._guid_label

    @guid_label.setter
    def guid_label(self, values):
        self._guid_label = dict(values)

    @property
    def guid_subd_edge(self):
        return self._guid_subd_edge

    @guid_subd_edge.setter
    def guid_subd_edge(self, values):
        self._guid_subd_edge = dict(values)

    @property
    def guid_strip_division(self):
        return self._guid_strip_division

    @guid_strip_division.setter
    def guid_strip_division(self, values):
        self._guid_strip_division = dict(values)

    # ----------------------------------------------------------------------
    # constructors
    # ----------------------------------------------------------------------

    @classmethod
    def from_guid(cls, guid):
        rhinosurface = RhinoSurface.from_guid(guid)
        mesh = rhinosurface.to_compas(cleanup=False)
        subdobject = cls(mesh)
        subdobject.coarse = mesh

        return subdobject

    # ----------------------------------------------------------------------
    # modification
    # ----------------------------------------------------------------------

    def get_default_strip_subdvision(self):
        """get subdivision number for each strip by user input target length"""

        import random

        def _random_color():
            return list(random.choice((range(256))) for _ in range(3))

        # target_length = compas_rhino.rs.GetReal('target edge length?')
        total_length = 0
        for u, v in self.item.edges():
            total_length += self.item.edge_length(u, v)
        target_length = total_length/self.item.number_of_edges()/10.0

        for i, edges in self._edge_strips.items():
            edge0 = edges[0]
            n = int(round(self.item.edge_length(edge0[0], edge0[1]) / target_length))

            color = _random_color()

            self._strip_division.update({i: [n, color]})

    def get_subd(self):
        subd = mesh_fast_copy(self.item)
        for i, edges in self._edge_strips.items():
            n = self._strip_division[i][0]
            subd = mesh_subdivide_strip(subd, edges[0], n)

        self.subd = subd

    def get_draw_default_subd(self):
        self.get_default_strip_subdvision()
        self.get_subd()

    def _change_division(self, edge, n):
        """change subdivision for a strip"""
        for i, edges in self._edge_strips.items():
            if (edge[0], edge[1]) in edges or (edge[1], edge[0]) in edges:
                break

        color = self._strip_division[i][1]
        self._strip_division.update({i: [n, color]})

    def change_strip_subd(self):
        """change subdivision for a strip, get input strip and division number from ui"""

        def custom_filter(rhino_object, geometry, component_index):
            if rhino_object.Attributes.ObjectId in list(self.guid_coarse_edge.keys()):
                return True
            return False

        guid = rs.GetObject(
            message='select the edge to change subdivision',
            preselect=False,
            select=True,
            custom_filter=custom_filter
        )
        if not guid:
            return

        edge = self.guid_coarse_edge[guid]
        n = compas_rhino.rs.GetInteger('divide into?')
        if not n or n < 2:
            print('has to be larger than 2!!')
            return guid

        self._change_division(edge, n)

        return guid

    def change_draw_subd(self):
        self.draw_strips_division_num(redraw=True)

        while True:
            guid = self.change_strip_subd()
            if not guid:
                break

            self.clear_strips_division_num()
            self.clear_subd()
            self.get_subd()
            self.draw_strips_division_num()
            self.draw_subd()

    # ----------------------------------------------------------------------
    # visualize
    # ----------------------------------------------------------------------

    def move(self):
        pass

    def modify(self):
        pass

    def select(self):
        pass

    def draw(self):
        pass

    def clear(self):
        self.clear_coarse()
        self.clear_subd()
        self.clear_strips_division_num()

    def draw_coarse(self):
        self.artist.layer = self.settings['layer.coarse']
        color = self.settings['color.edges']
        guids = self.artist.draw_edges(color=color)
        self.guid_coarse_edge = zip(guids, list(self.item.edges()))
        # self._draw_strips_label()
        self.artist.redraw()

    def draw_subd(self):
        artist = MeshArtist(self.subd)
        layer = self.settings['layer.subd']
        color = self.settings['color.subd.edges']
        artist.layer = layer
        edges = [edge for edge in self.subd.edges() if not self.subd.is_edge_on_boundary(edge[0], edge[1])]
        guids = artist.draw_edges(edges, color=color)
        self.guid_subd_edge = zip(guids, edges)
        artist.redraw()

    def _draw_strips_label(self):
        labels = []
        strips = []
        for i, edges in self._edge_strips.items():
            boundary_edge_a_point = self.item.edge_midpoint(*edges[0])
            boundary_edge_b_point = self.item.edge_midpoint(*edges[-1])
            labels.append({'pos': boundary_edge_a_point, 'text': str(i)})
            labels.append({'pos': boundary_edge_b_point, 'text': str(i)})
            strips.append(i)
            strips.append(i)

        guids = compas_rhino.draw_labels(labels, layer=self.settings['layer.coarse'], clear=False, redraw=False)
        self.guid_label = zip(guids, strips)

    def draw_strips_division_num(self, redraw=False):
        """draw the subdivision number for all strips"""

        labels = []
        strips = []
        for strip in list(self._edge_strips.keys()):

            division = self._strip_division[strip][0]
            color = self._strip_division[strip][1]
            edges = self._edge_strips[strip]
            boundary_edge_a_point = self.item.edge_midpoint(*edges[0])
            boundary_edge_b_point = self.item.edge_midpoint(*edges[-1])
            labels.append({'pos': boundary_edge_a_point, 'text': str(division), 'color': color})
            labels.append({'pos': boundary_edge_b_point, 'text': str(division), 'color': color})
            strips.append(strip)
            strips.append(strip)

        guids = compas_rhino.draw_labels(labels, layer=self.settings['layer.coarse'], clear=False, redraw=redraw)
        self.guid_strip_division = zip(guids, strips)

    def clear_coarse(self):
        guid_coarse_edge = list(self.guid_coarse_edge.keys())
        delete_objects(guid_coarse_edge, purge=True)
        self._guid_coarse_edge = {}

    def clear_subd(self):
        guid_subd_edge = list(self.guid_subd_edge.keys())
        delete_objects(guid_subd_edge, purge=True)
        self._guid_subd_edge = {}

        # self.clear_strips_division_num()

    def clear_strips_division_num(self):
        guids = list(self.guid_strip_division.keys())
        delete_objects(guids, purge=True)
        self._guid_strip_division = {}

    def _clear_strips_label(self):
        guids = list(self.guid_label.keys())
        delete_objects(guids, purge=True)
        self._guid_label = {}
