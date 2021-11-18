from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino

import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import compas_rhino

from compas.datastructures import Mesh
from compas.datastructures import meshes_join

from compas.geometry import normalize_vector
from compas.geometry import add_vectors

from compas.utilities import color_to_colordict, geometric_key

from compas_rhino.utilities import select_surface
from compas_rhino.objects import mesh_select_edge
from compas_rhino.geometry import RhinoSurface


from compas_rhino.artists import MeshArtist


# select rhino surface or polysurface
guid = select_surface()
rhinosurface = RhinoSurface.from_guid(guid)
mesh = rhinosurface.to_compas(cleanup=False)

rs.HideObjects(guid)
artist = MeshArtist(mesh)
artist.draw_edges(color=(100, 100, 100))

# create a list of guids from selected surfaces if polysurface was selected
crs = compas_rhino.rs
guids = []
if rs.IsPolysurface(guid):
    guids = crs.ExplodePolysurfaces(guid)
elif rs.IsSurface(guid):
    guids = [guid]
else:
    raise Exception('Object is not a surface.')

# surface's u and v directions from the surface's udomain and vdomain vectors

#faces_uv_vectors = {}
#for face in mesh.faces():
#    u, w, v = mesh.face_vertices(face)[:3]
#    faces_uv_vectors[face] = {'u_edge': (w, u),
#                              'v_edge': (w, v)}


gkeys = {geometric_key(mesh.vertex_coordinates(vertex)): vertex for vertex in mesh.vertices()}

##1st way 
#surfaces_uv_vectors ={}
#surfaces=[]
#for guid,face in zip(guids, mesh.faces()):
#    domain_u = rs.SurfaceDomain(guid, 0)
#    domain_v = rs.SurfaceDomain(guid, 1)
#    print(domain_u)
#    u0_xyz = rg.Point3d(domain_u[0], domain_v[0],0)
#    u1_xyz = rg.Point3d(domain_u[1], domain_v[0],0)
#    v0_xyz = rg.Point3d(domain_v[0], domain_u[0],0)
#    v1_xyz = rg.Point3d(domain_v[1], domain_u[0],0)
#    print(u0_xyz)
#    u0 = gkeys[geometric_key(tuple(u0_xyz))]
#    u1 = gkeys[geometric_key(tuple(u1_xyz))]
#    v0 = gkeys[geometric_key(tuple(v0_xyz))]
#    v1 = gkeys[geometric_key(tuple(v1_xyz))]
#    rhinosurface = RhinoSurface.from_guid(guid)
#    surfaces.append(rhinosurface)
#    surfaces_uv_vectors[face] = {'u_edge': (u0, u1),
#                                 'v_edge': (v0, v1),
#                                 'surface': rhinosurface}

#2nd way
faces_uv_vectors = {}
brep = Rhino.Geometry.Brep.TryConvertBrep(rhinosurface.geometry)
brep_faces = brep.Faces
for brep_face, face in zip(brep_faces, mesh.faces()):
    domain_u = brep_face.Domain(0)
    domain_v = brep_face.Domain(1)
    u0_xyz = brep_face.PointAt(domain_u[0], domain_v[0])
    u1_xyz = brep_face.PointAt(domain_u[1], domain_v[0])
    v0_xyz = brep_face.PointAt(domain_u[0], domain_v[0])
    v1_xyz = brep_face.PointAt(domain_u[0], domain_v[1])
    u0 = gkeys[geometric_key(tuple(u0_xyz))]
    u1 = gkeys[geometric_key(tuple(u1_xyz))]
    v0 = gkeys[geometric_key(tuple(v0_xyz))]
    v1 = gkeys[geometric_key(tuple(v1_xyz))]
    faces_uv_vectors[face] = {'u_edge': (u0, u1),
                              'v_edge': (v0, v1),
                              'surface' : brep_face}


def draw_uv_vectors(mesh, vector_dict):
    lines = []
    for face in vector_dict:
        sp = mesh.face_centroid(face)
        u0, u1 = vector_dict[face]['u_edge']
        v0, v1 = vector_dict[face]['v_edge']
        u_vec = normalize_vector(mesh.edge_vector(u0, u1))
        v_vec = normalize_vector(mesh.edge_vector(v0, v1))
        u_ep = add_vectors(sp, u_vec)
        v_ep = add_vectors(sp, v_vec)
        lines.append({'start': sp, 'end': u_ep, 'color': (0, 255, 0), 'arrow': "end"})
        lines.append({'start': sp, 'end': v_ep, 'color': (255, 0, 0), 'arrow': "end"})
    compas_rhino.draw_lines(lines, layer='uv_vectors', clear=False, redraw=False)


# draw uv information per face
draw_uv_vectors(mesh, faces_uv_vectors)
rs.EnableRedraw(True)


# user chooses an edge
pick_edge = mesh_select_edge(mesh)

# ?????? do we always consider that we work with 1 mesh each time that derives from 1 surface, therefore 1 face and 2 edges?
# get all the faces of the edge strip
edge_strip = set(frozenset(edge) for edge in mesh.edge_strip(pick_edge))
edge_strip_faces = set()

for u, v in edge_strip:
    face1, face2 = mesh.edge_faces(u, v)
    if face1 is not None:
        edge_strip_faces.add(face1)
    if face2 is not None:
        edge_strip_faces.add(face2) # ?????? doesn't it add the same face twice?


# determine whether the face's u or v domain is aligned with the edge strip
face_division_direction = {}
for face in edge_strip_faces:
    u_edge = faces_uv_vectors[face]['u_edge']
    surface = faces_uv_vectors[face]['surface']
    if frozenset(u_edge) in edge_strip:
        face_division_direction[face] = 'divide_u'
    else:
        suface = rg.Surface.Transpose(surface)
        face_division_direction[face] = 'divide_v'





artist.clear()

# draw edge strip in black
facelabels = {face: str(face) for face in edge_strip_faces}
artist.draw_facelabels(text=facelabels)


# draw edges (edge strip in black)
edge_colors = {edge: (100, 100, 100) for edge in mesh.edges()}
for edge in list(tuple(edge) for edge in edge_strip):
    edge_colors.update({edge: (0, 0, 0)})
artist.draw_edges(color=edge_colors)


# tells us which direction to divide the face
print(face_division_direction)
