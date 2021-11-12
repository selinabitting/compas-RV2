from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino

import rhinoscriptsyntax as rs

import compas_rhino

from compas.datastructures import Mesh

from compas_rhino.utilities import select_surface
from compas_rhino.objects import mesh_select_edge
from compas_rhino.geometry import RhinoSurface
from compas_rhino.artists import MeshArtist


# ==============================================================================
# 0. find edge strip thorugh quads and nonquads
# ==============================================================================
def subd_edge_strip(mesh, edge):

    def strip_end_faces(strip):
        # return nonquads at the end of edge strips
        faces1 = mesh.edge_faces(strip[0][0], strip[0][1])
        faces2 = mesh.edge_faces(strip[-1][0], strip[-1][1])
        nonquads = []
        for face in faces1 + faces2:
            if face is not None and len(mesh.face_vertices(face)) != 4:
                nonquads.append(face)
        return nonquads

    strip = mesh.edge_strip(edge)

    all_edges = list(strip)

    end_faces = set(strip_end_faces(strip))
    seen = set()

    while len(end_faces) > 0:
        face = end_faces.pop()
        if face not in seen:
            seen.add(face)
            for u, v in mesh.face_halfedges(face):
                halfedge = (u, v)
                if halfedge not in all_edges:
                    rev_hf_face = mesh.halfedge_face(v, u)
                    if rev_hf_face is not None:
                        if len(mesh.face_vertices(rev_hf_face)) != 4:
                            end_faces.add(mesh.halfedge_face(v, u))
                            all_edges.append(halfedge)
                            continue
                    halfedge_strip = mesh.edge_strip(halfedge)
                    all_edges.extend(halfedge_strip)
                    end_faces.update(strip_end_faces(halfedge_strip))
    return all_edges


# ==============================================================================
# 1. select rhino surface or polysurface
# ==============================================================================
guid = select_surface()
rs.HideObjects(guid)


# ==============================================================================
# 2. convert selection to compas rhinosurface
# ==============================================================================

rhinosurface = RhinoSurface.from_guid(guid)
brep = Rhino.Geometry.Brep.TryConvertBrep(rhinosurface.geometry)

mesh = rhinosurface.to_compas_mesh(cls=Mesh)


artist = MeshArtist(mesh, layer='subd')
artist.draw_edges()
compas_rhino.rs.Redraw()


# ==============================================================================
# 3. get edge strip from an edge
# ==============================================================================
edge = mesh_select_edge(mesh)
edge_strip = subd_edge_strip(mesh, edge)


# ==============================================================================
# 4. draw results
# ==============================================================================
artist.draw_vertexlabels()
artist.draw_facelabels(color=(0, 0, 0))

artist.clear_edges()

edge_colors = {edge: (120, 120, 120) for edge in mesh.edges()}
for edge in edge_strip:
    edge_colors.update({edge: (255, 0, 0)})
artist.draw_edges(edge_strip, color=edge_colors)
artist.draw_vertexlabels()
artist.draw_facelabels(color=(0, 0, 0))
