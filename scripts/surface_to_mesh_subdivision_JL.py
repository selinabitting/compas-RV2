from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino
import math
import rhinoscriptsyntax as rs

import compas_rhino

from compas.datastructures import Mesh
from compas.datastructures import meshes_join
from compas.datastructures.mesh.subdivision import mesh_fast_copy

from compas.geometry import normalize_vector
from compas.geometry import add_vectors
from compas.geometry import centroid_points

from compas.utilities import color_to_colordict, geometric_key

from compas_rhino.utilities import select_surface
from compas_rhino.objects import mesh_select_edge
from compas_rhino.geometry import RhinoSurface
from compas_rhino.artists import MeshArtist


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


# ==============================================================================
#  3. make a Mesh from the rhinosurface, then draw it
# ==============================================================================
mesh = rhinosurface.to_compas_mesh(cls=Mesh, cleanup=False)  # update to latest compas
coarse_mesh_artist = MeshArtist(mesh, layer='coarse_mesh')
coarse_mesh_artist.draw_edges(color=(255, 0, 0))

# ==============================================================================
#  x. default subdivision numbers
# ==============================================================================
default_nu_nv = 4  # for quads
default_n = 2  # for non-quads

# ==============================================================================
#  4. get the face geometry and u + v edges per face and keep track in faces_dict
# ==============================================================================
faces_dict = {}
edges_dict = {}

gkeys = {geometric_key(mesh.vertex_coordinates(vertex)): vertex for vertex in mesh.vertices()}

for brep_face, face in zip(brep.Faces, mesh.faces()):

    face_info = {'is_quad': False,
                 'u_edge': None,
                 'v_edge': None,
                 'nu': default_nu_nv,
                 'nv': default_nu_nv,
                 'n': default_n,
                 'brep_face': brep_face}

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
        face_info.update({'is_quad': True,
                          'u_edge': (u0, u1),
                          'v_edge': (v0, v1),
                          'brep_face': brep_face})

    else:
        k = len(segments)
        for seg in segments:
            sp = seg.PointAtStart
            ep = seg.PointAtEnd
            u0 = gkeys[geometric_key(sp)]
            u1 = gkeys[geometric_key(ep)]
            edge = (u0, u1)
            edges_dict[edge] = {'brep_edge': seg,
                                'brep_sp': u0,
                                'brep_ep': u1}

    faces_dict[face] = face_info


# ==============================================================================
#  x. our main surface subdivision functions
# ==============================================================================

# quads

def subdivide_quad(brep_face, nu, nv):
    """Subdivide a single quad brep_face"""

    domain_u = brep_face.Domain(0)
    domain_v = brep_face.Domain(1)

    du = (domain_u[1] - domain_u[0]) / (nu)
    dv = (domain_v[1] - domain_v[0]) / (nv)

    def point_at(i, j):
        return brep_face.PointAt(i, j)

    quads = []
    for i in range(nu):
        for j in range(nv):
            a = point_at(domain_u[0] + (i + 0) * du, domain_v[0] + (j + 0) * dv)
            b = point_at(domain_u[0] + (i + 1) * du, domain_v[0] + (j + 0) * dv)
            c = point_at(domain_u[0] + (i + 1) * du, domain_v[0] + (j + 1) * dv)
            d = point_at(domain_u[0] + (i + 0) * du, domain_v[0] + (j + 1) * dv)
            quads.append([a, b, c, d])

    return Mesh.from_polygons(quads)

# non-quads

def split_boundary(mesh):
    boundaries = mesh.vertices_on_boundaries()
    exterior = boundaries[0]
    opening = []
    openings = [opening]
    for vertex in exterior:
        opening.append(vertex)
        if mesh.vertex_degree(vertex) == 2:
            opening = [vertex]
            openings.append(opening)
    openings[-1] += openings[0]
    del openings[0]
    openings[:] = [opening for opening in openings if len(opening) > 2]
    return openings


def divide_curve(curve, n):
    params = curve.DivideByCount(n, True)
    pts = []
    for param in params:
        pt = curve.PointAt(param)
        pts.append(pt)
    return pts


def relocate_boundary_vertices(subdmesh):

    subd_edge_vertices = split_boundary(subdmesh)

    for subd_vertices in subd_edge_vertices:

        s_vertex = subd_vertices[0]
        e_vertex = subd_vertices[-1]
        edge = (s_vertex, e_vertex)

        if edge not in edges_dict:
            edge = (e_vertex, s_vertex)

        curve = edges_dict[edge]['brep_edge']
        brep_points = divide_curve(curve, 2 ** n)

        curve_sp = edges_dict[edge]['brep_sp']
        if s_vertex != curve_sp:
            brep_points = brep_points[::-1]

        subd1.vertices_attributes('xyz', brep_points[1:-1], subd_vertices[1:-1])


def subdivide_nonquad(coarse_mesh, face, brep_face, n):
    """subdivide a single non-quad brep_face"""

    # make a mesh from the face ------------------------------------------------
    mesh = Mesh()
    vertices = coarse_mesh.face_vertices(face)
    for vertex in vertices:
        x, y, z = coarse_mesh.vertex_coordinates(vertex)
        mesh.add_vertex(vertex, {'x': x, 'y': y, 'z': z})
    mesh.add_face(vertices)

    cls = type(mesh)

    # subdivide mesh -----------------------------------------------------------
    for _ in range(n):
        subd = mesh_fast_copy(mesh)

        edgepoints = []
        for u, v in mesh.edges():
            w = subd.split_edge(u, v, allow_boundary=True)
            edgepoints.append([w, True])

        fkey_xyz = {fkey: mesh.face_centroid(fkey) for fkey in mesh.faces()}

        for fkey in mesh.faces():
            descendant = {i: j for i, j in subd.face_halfedges(fkey)}
            ancestor = {j: i for i, j in subd.face_halfedges(fkey)}

            x, y, z = fkey_xyz[fkey]
            c = subd.add_vertex(x=x, y=y, z=z)

            for key in mesh.face_vertices(fkey):
                a = ancestor[key]
                d = descendant[key]
                subd.add_face([a, key, d, c])

            del subd.face[fkey]

        mesh = subd

    subd1 = cls.from_data(mesh.data)

    # relocate boundary vertices -----------------------------------------------
    subd_edge_vertices = split_boundary(mesh)

    for subd_vertices in subd_edge_vertices:

        s_vertex = subd_vertices[0]
        e_vertex = subd_vertices[-1]
        edge = (s_vertex, e_vertex)

        if edge not in edges_dict:
            edge = (e_vertex, s_vertex)

        curve = edges_dict[edge]['brep_edge']
        brep_points = divide_curve(curve, 2 ** n)

        curve_sp = edges_dict[edge]['brep_sp']
        if s_vertex != curve_sp:
            brep_points = brep_points[::-1]

        for pt, key in zip(brep_points[1:-1], subd_vertices[1:-1]):
            subd1.vertex_attribute(key, 'x', pt.X)
            subd1.vertex_attribute(key, 'y', pt.Y)
            subd1.vertex_attribute(key, 'z', pt.Z)

    # relocate boundary vertices -----------------------------------------------


    return subd1


# quad + nonquad

def subdivide_surfacemesh(mesh, faces_dict):

    subd_meshes = []

    for face in mesh.faces():

        brep_face = faces_dict[face]['brep_face']
        quad = faces_dict[face]['is_quad']

        if quad:
            nu = faces_dict[face]['nu']
            nv = faces_dict[face]['nv']
            subd_mesh = subdivide_quad(brep_face, nu, nv)


        else:
            n = faces_dict[face]['n']
            subd_mesh = subdivide_nonquad(mesh, face, brep_face, n)

        subd_mesh.smooth_area(fixed=subd_mesh.vertices_on_boundary(), kmax=10, damping=0.5)
        subd_meshes.append(subd_mesh)

    return meshes_join(subd_meshes)


# ==============================================================================
#  6. subdivide surfaces with default subdivsion nu and nv
# ==============================================================================
subd1 = subdivide_surfacemesh(mesh, faces_dict)
subd1_artist = MeshArtist(subd1, layer='subd1_mesh', color=(130, 130, 130))
subd1_artist.draw_mesh()
rs.EnableRedraw(True)


# ==============================================================================
# steps 7 through 10 can be wrapped into an iterative/interactive loop
# ==============================================================================
# ----- need to make interactive......!!! -------


# ==============================================================================
#  7. pick an edge and its edge_strip
# ==============================================================================
pick_edge = mesh_select_edge(mesh)


# ==============================================================================
#  8. get subdivision number
# ==============================================================================
nu_or_nv = compas_rhino.rs.GetInteger('divide into?', minimum=2)

# ==============================================================================
#  9. edge strip subdivision functions
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

def edge_strip_faces(mesh, edge_strip):
    edge_strip_faces = set()
    for u, v in edge_strip:
        face1, face2 = mesh.edge_faces(u, v)
        if face1 is not None:
            edge_strip_faces.add(face1)
        if face2 is not None:
            edge_strip_faces.add(face2)
    return list(edge_strip_faces)

# ==============================================================================
#  10. update nu or nv information for the faces of the edge_strip
# ==============================================================================

edge_strip = set(frozenset(edge) for edge in subd_edge_strip(mesh, pick_edge))
edge_strip_faces = edge_strip_faces(mesh, edge_strip)

for face in edge_strip_faces:
    quad = faces_dict[face]['is_quad']

    if quad:
        u_edge = faces_dict[face]['u_edge']
        if frozenset(u_edge) in edge_strip:
            faces_dict[face]['nu'] = nu_or_nv
        else:
            faces_dict[face]['nv'] = nu_or_nv

    else:
        n = math.sqrt(nu_or_nv)
        half = nu_or_nv/2
        print (int)
        if nu_or_nv == 2:
            faces_dict[face]['n'] = 1
        elif n.is_integer()==True:
            faces_dict[face]['n'] = n
        elif n>half:
            faces_dict[face]['n'] = int(n)-1
        else:
            faces_dict[face]['n'] = int(n)+1

# ==============================================================================
#  11. subdivide the surfaces again with the updated nu_nv
# ==============================================================================
subd2 = subdivide_surfacemesh(mesh, faces_dict)


# ==============================================================================
#  12. draw the newly subdivided mesh
# ==============================================================================
coarse_mesh_artist.clear()
subd1_artist.clear()
subd2_artist = MeshArtist(subd2, layer='subd2_mesh')
subd2_artist.draw_mesh()
