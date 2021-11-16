from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino

from compas.datastructures import Mesh
from compas.datastructures import meshes_join

from compas.utilities import geometric_key

from compas_rhino.geometry import RhinoSurface


class SubdMesh(Mesh):

    def __init__(self, *args, **kwargs):
        super(SubdMesh, self).__init__(*args, **kwargs)
        self.default_edge_attributes.update({
            'brep_curve': None,
            'brep_curve_dir': None
        })
        self.default_face_attributes.update({
            'is_quad': False,
            'u_edge': None,
            'v_edge': None,
            'nu': 2,
            'nv': 2,
            'n': 1,
            'brep_face': None
        })
        self._edge_strips = {}

    @classmethod
    def from_guid(cls, guid):
        rhinosurface = RhinoSurface.from_guid(guid)
        brep = Rhino.Geometry.Brep.TryConvertBrep(rhinosurface.geometry)
        subdmesh = rhinosurface.to_compas_mesh(cls=cls)

        gkeys = {geometric_key(subdmesh.vertex_coordinates(vertex)): vertex for vertex in subdmesh.vertices()}

        for brep_face, face in zip(brep.Faces, subdmesh.faces()):

            loop = brep_face.OuterLoop
            curve = loop.To3dCurve()
            segments = curve.Explode()

            if len(segments) == 4:
                domain_u = brep_face.Domain(0)
                domain_v = brep_face.Domain(1)
                u0_xyz = brep_face.PointAt(domain_u[0], domain_v[0])
                u1_xyz = brep_face.PointAt(domain_u[1], domain_v[0])
                v0_xyz = brep_face.PointAt(domain_u[0], domain_v[0])
                v1_xyz = brep_face.PointAt(domain_u[0], domain_v[1])
                u0 = gkeys[geometric_key(u0_xyz)]
                u1 = gkeys[geometric_key(u1_xyz)]
                v0 = gkeys[geometric_key(v0_xyz)]
                v1 = gkeys[geometric_key(v1_xyz)]
                attr = ['is_quad', 'u_edge', 'v_edge', 'brep_face']
                values = [True, (u0, u1), (v0, v1), brep_face]
                subdmesh.face_attributes(face, attr, values)

            else:
                for curve, edge in zip(segments, subdmesh.face_halfedges(face)):
                    sp = curve.PointAtStart
                    ep = curve.PointAtEnd
                    u = gkeys[geometric_key(sp)]
                    v = gkeys[geometric_key(ep)]
                    subdmesh.edge_attribute(edge, 'brep_curve_dir', (u, v))

        return subdmesh

    # ==========================================================================
    #   helpers
    # ==========================================================================

    def subd_edge_strip(self, edge):

        def strip_end_faces(strip):
            # return nonquads at the end of edge strips
            faces1 = self.edge_faces(strip[0][0], strip[0][1])
            faces2 = self.edge_faces(strip[-1][0], strip[-1][1])
            nonquads = []
            for face in faces1 + faces2:
                if face is not None and len(self.face_vertices(face)) != 4:
                    nonquads.append(face)
            return nonquads

        strip = self.edge_strip(edge)

        all_edges = list(strip)

        end_faces = set(strip_end_faces(strip))
        seen = set()

        while len(end_faces) > 0:
            face = end_faces.pop()
            if face not in seen:
                seen.add(face)
                for u, v in self.face_halfedges(face):
                    halfedge = (u, v)
                    if halfedge not in all_edges:
                        rev_hf_face = self.halfedge_face(v, u)
                        if rev_hf_face is not None:
                            if len(self.face_vertices(rev_hf_face)) != 4:
                                end_faces.add(self.halfedge_face(v, u))
                                all_edges.append(halfedge)
                                continue
                        halfedge_strip = self.edge_strip(halfedge)
                        all_edges.extend(halfedge_strip)
                        end_faces.update(strip_end_faces(halfedge_strip))
        return all_edges

    def edge_strip_faces(self, edge_strip):
        edge_strip_faces = set()
        for u, v in edge_strip:
            face1, face2 = self.edge_faces(u, v)
            if face1 is not None:
                edge_strip_faces.add(face1)
            if face2 is not None:
                edge_strip_faces.add(face2)
        return list(edge_strip_faces)

    # ==========================================================================
    #   subdivision
    # ==========================================================================

    def divide_curve(curve, n):
        pass

    def subdivide_quad(self, face, nu, nv):
        pass

    def subdivide_nonquad(self, face, n):
        pass

    def subdivide_faces(self):

        subd_meshes = []

        for face in self.faces():

            self.subdivide_quad()

            self.subdivide_nonquad()

        return meshes_join(subd_meshes)
