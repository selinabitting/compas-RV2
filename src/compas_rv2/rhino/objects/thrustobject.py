from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino

from compas.utilities import i_to_rgb
from compas.geometry import Point
from compas.geometry import Scale
from compas.geometry import Translation
from compas.geometry import Rotation

from .meshobject import MeshObject


__all__ = ["ThrustObject"]


class ThrustObject(MeshObject):
    """Scene object for thrust diagrams in RV2."""

    SETTINGS = {
        '_is.valid': False,
        'layer': "RV2::ThrustDiagram",

        'show.vertices': True,
        'show.edges': False,
        'show.faces': True,

        'show.selfweight': False,
        'show.loads': False,
        'show.residuals': False,
        'show.reactions': True,
        'show.pipes': False,

        'color.vertices': [255, 0, 255],
        'color.vertices:is_fixed': [0, 255, 0],
        'color.vertices:is_anchor': [255, 0, 0],

        'color.edges': [255, 0, 255],
        'color.selfweight': [0, 80, 0],
        'color.loads': [0, 80, 0],
        'color.residuals': [0, 255, 255],
        'color.reactions': [0, 80, 0],

        'color.faces': [255, 0, 255],
        'color.pipes': [0, 0, 255],
        'color.invalid': [100, 255, 100],

        'scale.selfweight': 0.1,
        'scale.externalforces': 0.1,
        'scale.residuals': 1.0,
        'scale.pipes': 0.01,

        'tol.selfweight': 1e-3,
        'tol.externalforces': 1e-3,
        'tol.residuals': 1e-3,
        'tol.pipes': 1e-3,
    }

    def __init__(self, diagram, **kwargs):
        super(ThrustObject, self).__init__(diagram, **kwargs)
        self._guid_free = {}
        self._guid_anchor = {}
        self._guid_reaction = {}
        self._guid_residual = {}
        self._guid_selfweight = {}
        self._guid_load = {}
        self._guid_pipe = {}

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

    @property
    def guid_free(self):
        return self._guid_free

    @guid_free.setter
    def guid_free(self, values):
        self._guid_free = dict(values)

    @property
    def guid_anchor(self):
        return self._guid_anchor

    @guid_anchor.setter
    def guid_anchor(self, values):
        self._guid_anchor = dict(values)

    @property
    def guid_selfweight(self):
        return self._guid_selfweight

    @guid_selfweight.setter
    def guid_selfweight(self, values):
        self._guid_selfweight = dict(values)

    @property
    def guid_load(self):
        return self._guid_load

    @guid_load.setter
    def guid_load(self, values):
        self._guid_load = dict(values)

    @property
    def guid_residual(self):
        return self._guid_residual

    @guid_residual.setter
    def guid_residual(self, values):
        self._guid_residual = dict(values)

    @property
    def guid_reaction(self):
        return self._guid_reaction

    @guid_reaction.setter
    def guid_reaction(self, values):
        self._guid_reaction = dict(values)

    @property
    def guid_pipe(self):
        return self._guid_pipe

    @guid_pipe.setter
    def guid_pipe(self, values):
        self._guid_pipe = dict(values)

    def clear(self):
        super(ThrustObject, self).clear()
        guids = []
        guids += list(self.guid_free)
        guids += list(self.guid_anchor)
        guids += list(self.guid_selfweight)
        guids += list(self.guid_reaction)
        guids += list(self.guid_load)
        guids += list(self.guid_residual)
        guids += list(self.guid_pipe)
        compas_rhino.delete_objects(guids, purge=True)
        self._guid_free = {}
        self._guid_anchor = {}
        self._guid_selfweight = {}
        self._guid_load = {}
        self._guid_residual = {}
        self._guid_reaction = {}
        self._guid_pipe = {}

    def draw(self):
        """Draw the objects representing the thrust diagram.
        """
        layer = self.settings['layer']
        self.artist.layer = layer
        self.artist.clear_layer()
        self.clear()
        if not self.visible:
            return
        self.artist.vertex_xyz = self.vertex_xyz

        # ======================================================================
        # Groups
        # ------
        # Create groups for vertices, edges, and faces.
        # These groups will be turned on/off based on the visibility settings of the diagram.
        # Separate groups are created for free and anchored vertices.
        # ======================================================================

        group_free = "{}::vertices_free".format(layer)
        group_anchor = "{}::vertices_anchor".format(layer)

        group_edges = "{}::edges".format(layer)
        group_faces = "{}::faces".format(layer)

        if not compas_rhino.rs.IsGroup(group_free):
            compas_rhino.rs.AddGroup(group_free)

        if not compas_rhino.rs.IsGroup(group_anchor):
            compas_rhino.rs.AddGroup(group_anchor)

        if not compas_rhino.rs.IsGroup(group_edges):
            compas_rhino.rs.AddGroup(group_edges)

        if not compas_rhino.rs.IsGroup(group_faces):
            compas_rhino.rs.AddGroup(group_faces)

        # ======================================================================
        # Vertices
        # --------
        # Draw the vertices and add them to the vertex group.
        # Free vertices and anchored vertices are drawn separately.
        # ======================================================================

        free = list(self.mesh.vertices_where({'is_anchor': False}))
        anchors = list(self.mesh.vertices_where({'is_anchor': True}))
        color_free = self.settings['color.vertices'] if self.settings['_is.valid'] else self.settings['color.invalid']
        color_anchor = self.settings['color.vertices:is_anchor']
        color = {vertex: color_free for vertex in free}
        color.update({vertex: color_anchor for vertex in anchors})
        guids_free = self.artist.draw_vertices(free, color)
        guids_anchor = self.artist.draw_vertices(anchors, color)
        self.guid_free = zip(guids_free, free)
        self.guid_anchor = zip(guids_anchor, anchors)
        compas_rhino.rs.AddObjectsToGroup(guids_free, group_free)
        compas_rhino.rs.AddObjectsToGroup(guids_anchor, group_anchor)

        if self.settings['show.vertices']:
            compas_rhino.rs.HideGroup(group_free)
            compas_rhino.rs.ShowGroup(group_anchor)
        else:
            compas_rhino.rs.HideGroup(group_free)
            compas_rhino.rs.HideGroup(group_anchor)

        # ======================================================================
        # Edges
        # -----
        # Draw the edges and add them to the edge group.
        # ======================================================================

        edges = list(self.mesh.edges_where({'_is_edge': True}))
        color = {edge: self.settings['color.edges'] if self.settings['_is.valid'] else self.settings['color.invalid'] for edge in edges}

        # color analysis
        if self.scene and self.scene.settings['RV2']['show.forces']:
            if self.mesh.dual:
                _edges = list(self.mesh.dual.edges())
                lengths = [self.mesh.dual.edge_length(*edge) for edge in _edges]
                edges = [self.mesh.dual.primal_edge(edge) for edge in _edges]
                lmin = min(lengths)
                lmax = max(lengths)
                for edge, length in zip(edges, lengths):
                    if lmin != lmax:
                        color[edge] = i_to_rgb((length - lmin) / (lmax - lmin))
        guids = self.artist.draw_edges(edges, color)
        self.guid_edge = zip(guids, edges)
        compas_rhino.rs.AddObjectsToGroup(guids, group_edges)

        if self.settings['show.edges']:
            compas_rhino.rs.ShowGroup(group_edges)
        else:
            compas_rhino.rs.HideGroup(group_edges)

        # ======================================================================
        # Faces
        # -----
        # Draw the faces and add them to the face group.
        # ======================================================================

        faces = list(self.mesh.faces_where({'_is_loaded': True}))
        color = {face: self.settings['color.faces'] if self.settings['_is.valid'] else self.settings['color.invalid'] for face in faces}
        guids = self.artist.draw_faces(faces, color)
        self.guid_face = zip(guids, faces)
        compas_rhino.rs.AddObjectsToGroup(guids, group_faces)

        if self.settings.get('show.faces', True):
            compas_rhino.rs.ShowGroup(group_faces)
        else:
            compas_rhino.rs.HideGroup(group_faces)

        # ======================================================================
        # Overlays
        # --------
        # Color overlays for various display modes.
        # ======================================================================

        if self.settings['_is.valid'] and self.settings['show.selfweight']:
            tol = self.settings['tol.selfweight']
            vertices = list(self.mesh.vertices())
            color = self.settings['color.selfweight']
            scale = self.settings['scale.selfweight']
            guids = self.artist.draw_selfweight(vertices, color, scale, tol)
            self.guid_selfweight = zip(guids, vertices)

        if self.settings['_is.valid'] and self.settings['show.loads']:
            tol = self.settings['tol.externalforces']
            vertices = list(self.mesh.vertices())
            color = self.settings['color.loads']
            scale = self.settings['scale.externalforces']
            guids = self.artist.draw_loads(vertices, color, scale, tol)
            self.guid_load = zip(guids, vertices)

        if self.settings['_is.valid'] and self.settings['show.residuals']:
            tol = self.settings['tol.residuals']
            vertices = list(self.mesh.vertices_where({'is_anchor': False}))
            color = self.settings['color.residuals']
            scale = self.settings['scale.residuals']
            guids = self.artist.draw_residuals(vertices, color, scale, tol)
            self.guid_residual = zip(guids, vertices)

        if self.settings['_is.valid'] and self.settings['show.reactions']:
            tol = self.settings['tol.externalforces']
            anchors = list(self.mesh.vertices_where({'is_anchor': True}))
            color = self.settings['color.reactions']
            scale = self.settings['scale.externalforces']
            guids = self.artist.draw_reactions(anchors, color, scale, tol)
            self.guid_reaction = zip(guids, anchors)

        if self.settings['_is.valid'] and self.settings['show.pipes']:
            tol = self.settings['tol.pipes']
            edges = list(self.mesh.edges_where({'_is_edge': True}))
            color = {edge: self.settings['color.pipes'] for edge in edges}

            # color analysis
            if self.scene and self.scene.settings['RV2']['show.forces']:
                if self.mesh.dual:
                    _edges = list(self.mesh.dual.edges())
                    lengths = [self.mesh.dual.edge_length(*edge) for edge in _edges]
                    edges = [self.mesh.dual.primal_edge(edge) for edge in _edges]
                    lmin = min(lengths)
                    lmax = max(lengths)
                    for edge, length in zip(edges, lengths):
                        if lmin != lmax:
                            color[edge] = i_to_rgb((length - lmin) / (lmax - lmin))

            scale = self.settings['scale.pipes']
            guids = self.artist.draw_pipes(edges, color, scale, tol)
            self.guid_pipe = zip(guids, edges)

        # self.redraw()

    def select_vertices(self):
        """Manually select vertices in the Rhino model view.

        Returns
        -------
        list
            The keys of the selected vertices.

        Examples
        --------
        >>>
        """
        guids = compas_rhino.select_points()
        if guids:
            guid_vertex = {}
            guid_vertex.update(self.guid_free)
            guid_vertex.update(self.guid_anchor)
            keys = [guid_vertex[guid] for guid in guids if guid in guid_vertex]
        else:
            keys = []
        return keys

    def select_vertices_free(self):
        """Manually select free vertices in the Rhino model view.

        Returns
        -------
        list
            The keys of the selected vertices.

        Examples
        --------
        >>>
        """
        guids = compas_rhino.select_points(message="Select free vertices.")
        if guids:
            keys = [self.guid_free[guid] for guid in guids if guid in self.guid_free]
        else:
            keys = []
        return keys

    def select_vertices_anchor(self):
        """Manually select anchor vertices in the Rhino model view.

        Returns
        -------
        list
            The keys of the selected vertices.

        Examples
        --------
        >>>
        """
        guids = compas_rhino.select_points(message="Select anchor vertices.")
        if guids:
            keys = [self.guid_anchor[guid] for guid in guids if guid in self.guid_anchor]
        else:
            keys = []
        return keys
