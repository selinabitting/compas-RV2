from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino

from compas.datastructures import Mesh

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
            'nu': 0,
            'nv': 0,
            'n': 0,
            'brep_face': None
        })
        self._edge_strips = {}

    @classmethod
    def from_guid(cls, guid):
        rhinosurface = RhinoSurface.from_guid(guid)
        brep = Rhino.Geometry.Brep.TryConvertBrep(rhinosurface.geometry)
        subdmesh = rhinosurface.to_compas_mesh(nu=1, nv=1, cls=cls)

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

    def subd_edge_strips(self, edge):
        pass

    # ==========================================================================
    #   subdivision
    # ==========================================================================

    def subdivide_quad(self, face, nu, nv):
        pass

    def subdivide_ngon(self, face, n):
        pass

    def subdivide_faces(self):
        pass
