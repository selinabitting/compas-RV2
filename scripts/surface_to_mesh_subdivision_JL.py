from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino

import rhinoscriptsyntax as rs
import Rhino.Geometry as rg

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
#rs.HideObjects(guid)


# ==============================================================================
# 2. convert selection to compas rhinosurface
# ==============================================================================

# here, rhinosurface could mean one or multiple joined surfaces ("polysurface")... from_guid will take care of it automatically.
rhinosurface = RhinoSurface.from_guid(guid)
brep = Rhino.Geometry.Brep.TryConvertBrep(rhinosurface.geometry)


# ==============================================================================
#  3. make a Mesh from the rhinosurface, then draw it
# ==============================================================================

mesh = rhinosurface.to_compas(cleanup=False)
coarse_mesh_artist = MeshArtist(mesh, layer='coarse_mesh')
coarse_mesh_artist.draw_edges(color=(0, 0, 0))

# select_surface() will already filter selection to surface or polysurface...
#
# crs = compas_rhino.rs
# guids = []
# if rs.IsPolysurface(guid):
#     guids = crs.ExplodePolysurfaces(guid)
# elif rs.IsSurface(guid):
#     guids = [guid]
# else:
#     raise Exception('Object is not a surface.')


# ==============================================================================
#  x. default subdivision numbers
# ==============================================================================

default_nu_nv = 10  # for quads
default_n = 4  # for non-quads


# ==============================================================================
#  4. get the face geometry and u + v edges per face and keep track in faces_dict
# ==============================================================================

# faces_dict will store per face, the following info:
#
# 'is_quad' : boolean, whether a brep_face is quad or not
# 'u_edge': u direction edge of the brep_face
# 'v_edge': v direction edge of the brep_face
# 'nu': subdivision number in the u direction
# 'nv': subdivision number in the v direction
# 'n': subdivision number for a non-quad (catmull clark subdivision count)
# 'brep_face': the geometry of the corresponding surface
#
# faces_dict will eventually be stored as face attributes in our surfacemesh datastructure

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
                 'brep_face': brep_face
                 }

    # check whether the brep_face is a quad or not (we can think of a shorter, more elegant solution...)
    loop = brep_face.OuterLoop
    curve = loop.To3dCurve()
    segments = curve.Explode()

    if len(segments) == 4:  # if brep_face is a quad, determine uv info

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
                          
        faces_dict[face] = face_info
        
    else:
        n = len(segments)
        
        brep_points = []
        for seg , edge in zip(segments, mesh.face_halfedges(face)):

            edge_info = {
                         'brep_edge' : seg,
                         'brep_sp' : None,
                         'brep_ep': None,
                         'curves': segments,
                         'points' : [],
                         'subd_points' : []
                         }
            sp = seg.PointAtStart
            ep = seg.PointAtEnd
            
            u0 = gkeys[geometric_key(sp)]
            u1 = gkeys[geometric_key(ep)]
            brep_points.append(sp)
            
            edge_info.update({
                              'brep_sp' : u0,
                              'brep_ep' : u1,
                              'points' : brep_points
                              })
            edges_dict[edge] = edge_info

# ==============================================================================
#  5. draw uv information per face (just for our visual reference)
# ==============================================================================

def draw_uv_vectors(mesh, faces_dict):
    lines = []
    for face in faces_dict:
        sp = mesh.face_centroid(face)
        u0, u1 = faces_dict[face]['u_edge']
        v0, v1 = faces_dict[face]['v_edge']
        u_vec = normalize_vector(mesh.edge_vector(u0, u1))
        v_vec = normalize_vector(mesh.edge_vector(v0, v1))
        u_ep = add_vectors(sp, u_vec)
        v_ep = add_vectors(sp, v_vec)
        lines.append({'start': sp, 'end': u_ep, 'color': (0, 255, 0), 'arrow': "end"})
        lines.append({'start': sp, 'end': v_ep, 'color': (255, 0, 0), 'arrow': "end"})
    compas_rhino.draw_lines(lines, layer='uv_vectors', clear=False, redraw=False)


draw_uv_vectors(mesh, faces_dict)


# ==============================================================================
#  x. our main surface subdivision functions
# ==============================================================================

# 1. for quads
def subdivide_quad(brep_face, nu, nv):
    """Subdivide a single quad brep_face"""

    # unlike the previous version, we input a single brep_face

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

# ------------------------------------------------------------------------------
# non-quads
# ------------------------------------------------------------------------------
def divide_curve(curve, n):
    params = curve.DivideByCount(n)
    pts = []
    for param in params:
        pt = curve.PointAt(param)
        pts.append(pt)
    return pts

# 2.  for non-quads
def subdivide_nonquad(face, brep_face, n):
    """subdivide a single non-quad brep_face"""
    mesh = face

    #subdivide brep_face edges 
    # ----------------------------------------------------------------------
    subd_points = []
    for edge in mesh.face_halfedges():
        subd_pts = divide_curve(seg,n)
        up_dict = {'subd_points' : subd_points}
        edges_dict[edge].update(up_dict)
        subd_points.extend(subd_pts)

    #subdivide based on catmull clark without smoothing
    # ----------------------------------------------------------------------
    initial_mesh_corners = mesh.vertices_on_boundary()
    fixed=initial_mesh_corners

    cls = type(mesh)

    if not fixed:
        fixed = []
    fixed = set(fixed)

    for _ in range(n):
        subd = mesh_fast_copy(mesh)

        # at each iteration, keep track of original connectivity and vertex locations

        # keep track of the created edge points that are not on the boundary
        # keep track track of the new edge points on the boundary
        # and their relation to the previous boundary points

        # ----------------------------------------------------------------------
        # split all edges

        edgepoints = []

        for u, v in mesh.edges():

            w = subd.split_edge(u, v, allow_boundary=True)
            # here, the location of w needs to lie on the boundary curve of the surface, not the midpoint of u and v.

            # crease = mesh.edge_attribute((u, v), 'crease') or 0
            crease = n + 1 # this ensures that boundary vertices remain fixed

            if crease:
                edgepoints.append([w, True])
                subd.edge_attribute((u, w), 'crease', crease - 1)
                subd.edge_attribute((w, v), 'crease', crease - 1)
            else:
                edgepoints.append([w, False])

        # ----------------------------------------------------------------------
        # subdivide

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

        # ----------------------------------------------------------------------
        # update vertex coordinates

        # these are the coordinates before updating
        key_xyz = {key: subd.vertex_coordinates(key) for key in subd.vertex}

        # move each edge point to the average of the neighboring centroids and
        # the original end points
        boundary_verts = []
        for w, crease in edgepoints:
            #boundary_verts.append(w)
            #print('the number of fixed vertices is', len(boundary_verts))
            if not crease:
                x, y, z = centroid_points(
                    [key_xyz[nbr] for nbr in subd.halfedge[w]])
                subd.vertex[w]['x'] = x
                subd.vertex[w]['y'] = y
                subd.vertex[w]['z'] = z

        #mesh = subd
    subd1 = cls.from_data(subd.data)

    # map edges to corresponding boundary curves
    # ------------------------------------------------------------------------------

    subd_gkeys = {geometric_key(subd1.vertex_coordinates(vertex)): vertex for vertex in subd1.vertices()}
    
    mesh_edge_vertices = list(subd.vertices_on_boundaries())

    #update vertex position to corresponding brep_edge
    map_boundary_vertices = [] #list of mapped vertices
    for vert, pt in zip(mesh_edge_vertices, subd_points):
        #not sure which is the right way of the following
        map_vert = subd1.update_default_vertex_attributes(vert, {'x','y','z'}, {pt[0], pt[1], pt[2]})
        map_vert = subd1.update_default_vertex_attributes({(x,y,z) : vert}, {(pt[0], pt[1], pt[2])})
        map_vert = subd1.vertex_attributes(vert, ('x','y','z'), (pt[0], pt[1], pt[2]))
        map_boundary_vertices.append(map_vert)
        subd.edge_attribute((u, w), 'crease', crease - 1)
    # smooth
    # ------------------------------------------------------------------------------
    subd2 = subd1.smooth_area(fixed=map_boundary_vertices, kmax=100, damping=0.5, callback=None, callback_args=None)

    return subd2

# ------------------------------------------------------------------------------
# 1 + 2. combination
# ------------------------------------------------------------------------------
# here, we don't actually need the mesh to run the function as it is written, but putting it in here anyway for now, as our eventual setup will all operate entirely around/on the mesh (which we will call the surfacemesh), and faces_dict will come from the face attributes of that mesh

def subdivide_surfacemesh(mesh, faces_dict):

    subd_meshes = []

    for face in mesh.faces():

        brep_face = faces_dict[face]['brep_face']
        quad = faces_dict[face]['is_quad']

        if quad:  # if face is a quad
            nu = faces_dict[face]['nu']
            nv = faces_dict[face]['nv']

            quad_subd_mesh = subdivide_quad(brep_face, nu, nv)
            subd_meshes.append(quad_subd_mesh)

        else:  # if face is a non-quad
            n = faces_dict[face]['n']
            nonquad_subd_mesh = subdivide_nonquad(face, brep_face, n)
            subd_meshes.append(nonquad_subd_mesh)

    return meshes_join(subd_meshes)


# ==============================================================================
# x. edge subdivision
# ==============================================================================

# def subdivide_edge_strip(mesh, pick_edge, n):
#
# def mesh_split_edge(mesh, u, v, n=2):
#
# since we can now just divide the individual surfaces through nu and nv, we no longer need to subdivide the edge strip or split edges... this was needed for the old subdobject, where the subdivision was happening through the edges, not the surfaces geometry (which we now have)...


# ==============================================================================
#  6. subdivide surfaces with default subdivsion nu and nv
# ==============================================================================

# subdivide the face with default subdivision values
subd1 = subdivide_surfacemesh(mesh, faces_dict)
subd1_artist = MeshArtist(subd1, layer='subd1_mesh')
subd1_artist.draw_edges(color=(130, 130, 130))
rs.EnableRedraw(True)


# ==============================================================================
# steps 7 through 10 can be wrapped into an iterative/interactive loop
# ==============================================================================
# ----- need to make interactive......!!! -------

# YES !!! next step :)


# ==============================================================================
#  7. pick an edge and its edge_strip
# ==============================================================================
# user chooses an edge
pick_edge = mesh_select_edge(mesh)


# ==============================================================================
#  8. get subdivision number
# ==============================================================================
# setting the minimum here will force users to enter a minimum integer of 2
nu_or_nv = compas_rhino.rs.GetInteger('divide into?', minimum=2)

# ==============================================================================
#  8. update nu or nv information for the faces of the edge_strip
# ==============================================================================

# get the faces of the edge_strip
edge_strip = set(frozenset(edge) for edge in mesh.edge_strip(pick_edge))
edge_strip_faces = set()

# we will need to modify the edge_strip function to incorporate non-quads...
for u, v in edge_strip:
    face1, face2 = mesh.edge_faces(u, v)
    if face1 is not None:
        edge_strip_faces.add(face1)
    if face2 is not None:
        edge_strip_faces.add(face2)

# update the nu or nv for quads, and n for non-quads
for face in edge_strip_faces:
    quad = faces_dict[face]['is_quad']

    # the nu_or_nv and the the count for catmull clark subdivision will need to be coordinated...

    if quad:  # if the face is a quad
        u_edge = faces_dict[face]['u_edge']
        if frozenset(u_edge) in edge_strip:
            faces_dict[face]['nu'] = nu_or_nv
        else:
            faces_dict[face]['nv'] = nu_or_nv

    else:  # if the face is a non-quad
        faces_dict[face]['n'] = nu_or_nv

# uncomment below to see results!


# ==============================================================================
#  9. subdivide the surfaces again with the updated nu_nv
# ==============================================================================

subd2 = subdivide_surfacemesh(mesh, faces_dict)


# ==============================================================================
#  10. draw the newly subdivided mesh
# ==============================================================================

coarse_mesh_artist.clear_layer() # delete the coarse mesh
subd1_artist.clear_layer() # delete the default subd mesh

subd2_artist = MeshArtist(subd2, layer='subd2_mesh')
subd2_artist.draw_mesh()
