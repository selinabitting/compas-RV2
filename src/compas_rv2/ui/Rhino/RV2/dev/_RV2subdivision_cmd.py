from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from copy import deepcopy
import compas_rhino
from compas_rhino.ui import CommandMenu
from compas_rhino.geometry import RhinoSurface
from compas_rhino.artists import MeshArtist
from compas_rv2.rhino import get_scene
from compas_rv2.datastructures import Pattern
from compas_rv2.rhino import SurfaceObject
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import rv2_error

from compas.geometry import Vector
from compas.geometry import add_vectors
from compas.geometry import scale_vector
from compas.datastructures import mesh_flip_cycles , Mesh, meshes_join_and_weld
from compas.datastructures import meshes_join
from compas.utilities import pairwise

vertices = [
    [0, 0.0, 0.0],
    [5, 0, 0.0],
    [5, 5, 0],
    [0, 5, 0.0]
]

faces = [
        [0, 1, 2,3]
]

mesh = Mesh.from_vertices_and_faces(vertices, faces)

def mesh_fast_copy(other):
    subd = Mesh()
    subd.vertex = deepcopy(other.vertex)
    subd.face = deepcopy(other.face)
    subd.facedata = deepcopy(other.facedata)
    subd.halfedge = deepcopy(other.halfedge)
    subd._max_face = other._max_face
    subd._max_vertex = other._max_vertex
    return subd

def subdivide_face(mesh, fkey):

    subd = mesh_fast_copy(mesh)
    subd.clear()

    centroid = mesh.face_centroid(fkey)
    centr_vert = mesh.add_vertex(centroid)
    face_verts = mesh.face_vertices(fkey)

    #find midpoints of edges-------------------------------------------------------------
    mid_verts = []
    for u,v in pairwise(face_verts()):

        t = 0.5
        # coordinates
        x, y, z = mesh.edge_point(u, v, t)

        # the split vertex
        subd.add_vertex(u)
        mid_vert = subd.add_vertex(x=x, y=y, z=z)
        subd.add_vertex(v)
        mid_verts.append(mid_vert)

    #create new faces----------------------------------------------------------------------
    new_faces = []
    new_vertices = []
    for i in zip(face_verts, mid_verts):
        new_face = subd.add_face([face_verts[i], mid_verts[i], centr_vert, mid_verts[(len(mid_verts)-1)-i]])
        new_faces.append(new_face)
        new_vertices.extend ([face_verts[i], mid_verts[i], mid_verts[(len(mid_verts)-1)-i]])

    new_vertices.insert(2, centr_vert)
    #mesh.delete_face(fkey)
    
    return subd , new_vertices, new_faces 


def mesh_subdivide_faces(mesh):
    new_meshes = []
    #faces = list(mesh.faces())
    for face in mesh.faces():
        new_mesh, new_verts, new_faces = subdivide_face(mesh, face)
        new_meshes.append(new_mesh)
    subd_mesh = meshes_join_and_weld(new_meshes, precision=None)
    return subd_mesh

subd = mesh_subdivide_faces(mesh)

def mesh_split_edge(mesh, u, v, n=2):

    fkey_uv = mesh.halfedge[u][v]
    fkey_vu = mesh.halfedge[v][u]

    insert_keys = [u]
    for i in range(n)[1:]:
        t = 1/n * i

        # coordinates
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
def tri_face(mesh, fkey):
    centroid = mesh.face_centroid(fkey)
    centroid_vector = Vector(*centroid)
    normal = mesh.face_normal(fkey)
    normal_vector = Vector(*normal)
    new_vertex = centroid_vector
    #new_keys = mesh.insert_vertex(fkey, xyz=new_vertex, return_fkeys=True)[1]

    face_verts = mesh.face_vertices(fkey)

    new_keys = []
    for i, v in enumerate(face_verts):
        next_v = face_verts[(i+1) % len(face_verts)]
        new_v = new_vertex
        new_face_key = mesh.add_face([v, next_v, new_v])
        new_keys.append(new_face_key)

    mesh.delete_face(fkey)
    return new_keys

#=====================================================================================
#subd = mesh.copy()
#fkeys = list(subd.faces())

for f in fkeys[:-1]:
    new_keys = tri_face(subd, f)
    for k in new_keys:
        newkeys = tri_face(subd, k)

artist = MeshArtist(subd, layer="aa_mesh")
artist.clear_layer()
artist.draw_faces(join_faces=True)
