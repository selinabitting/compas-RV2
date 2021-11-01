from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino

import rhinoscriptsyntax as rs

from compas.datastructures import Mesh
from compas.datastructures import meshes_join

from compas_rhino.utilities import select_surface
from compas_rhino.geometry import RhinoSurface

from compas_rhino.artists import MeshArtist


# ------------------------------------------------------------------------------
# select rhino surface or polysurface
# ------------------------------------------------------------------------------
guid = select_surface()
rhinosurface = RhinoSurface.from_guid(guid)
mesh = rhinosurface.to_compas(cleanup=False)

rs.HideObjects(guid)


# ------------------------------------------------------------------------------
# surface boundaries
# ------------------------------------------------------------------------------
border = rs.DuplicateSurfaceBorder(guid, type=1)
curves = rs.ExplodeCurves(border, delete_input=True)
# rs.HideObjects(curves)


# ------------------------------------------------------------------------------
# map edges to corresponding boundary curves
# ------------------------------------------------------------------------------
edge_cruves = {}


# ------------------------------------------------------------------------------
# mesh edge strips
# ------------------------------------------------------------------------------
edge_strips = {}


# ------------------------------------------------------------------------------
# unify surface uv directions
# ------------------------------------------------------------------------------
# similar to compas.datastructures.mesh.orientation mesh_unify_cycles()
def unify_uv_direction(mesh, edge_curves):
    pass


# ------------------------------------------------------------------------------
# surface uv subdivision
# ------------------------------------------------------------------------------
def surface_to_uvmesh(surface, nu, nv=None, weld=False, facefilter=None, cls=None):

    nv = nv or nu
    cls = cls or Mesh

    if not surface.geometry.HasBrepForm:
        return

    brep = Rhino.Geometry.Brep.TryConvertBrep(surface.geometry)

    if facefilter and callable(facefilter):
        faces = [face for face in brep.Faces if facefilter(face)]
    else:
        faces = brep.Faces

    meshes = []
    for face in faces:
        domain_u = face.Domain(0)
        domain_v = face.Domain(1)
        du = (domain_u[1] - domain_u[0]) / (nu)
        dv = (domain_v[1] - domain_v[0]) / (nv)

        def point_at(i, j):
            return face.PointAt(i, j)

        quads = []
        for i in range(nu):
            for j in range(nv):
                a = point_at(domain_u[0] + (i + 0) * du, domain_v[0] + (j + 0) * dv)
                b = point_at(domain_u[0] + (i + 1) * du, domain_v[0] + (j + 0) * dv)
                c = point_at(domain_u[0] + (i + 1) * du, domain_v[0] + (j + 1) * dv)
                d = point_at(domain_u[0] + (i + 0) * du, domain_v[0] + (j + 1) * dv)
                quads.append([a, b, c, d])

        meshes.append(cls.from_polygons(quads))

    return meshes_join(meshes)


# ------------------------------------------------------------------------------
# run command
# ------------------------------------------------------------------------------
subd = surface_to_uvmesh(rhinosurface, nu=10, nv=10, weld=True)


# ------------------------------------------------------------------------------
# draw subdivide mesh
# ------------------------------------------------------------------------------
artist = MeshArtist(subd)
artist.draw_mesh()
