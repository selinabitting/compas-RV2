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


#===============================================================================
# surface's u and v directions from the surface's udomain and vdomain vectors
#===============================================================================

gkeys = {geometric_key(mesh.vertex_coordinates(vertex)): vertex for vertex in mesh.vertices()}

surfaces_uv_vectors = {}
brep_surfaces_dic = {}
brep = Rhino.Geometry.Brep.TryConvertBrep(rhinosurface.geometry)
brep_surfaces = brep.Faces
for brep_surface, face in zip(brep_surfaces, mesh.faces()):
    domain_u = brep_surface.Domain(0)
    domain_v = brep_surface.Domain(1)
    u0_xyz = brep_surface.PointAt(domain_u[0], domain_v[0])
    u1_xyz = brep_surface.PointAt(domain_u[1], domain_v[0])
    v0_xyz = brep_surface.PointAt(domain_u[0], domain_v[0])
    v1_xyz = brep_surface.PointAt(domain_u[0], domain_v[1])
    u0 = gkeys[geometric_key(tuple(u0_xyz))]
    u1 = gkeys[geometric_key(tuple(u1_xyz))]
    v0 = gkeys[geometric_key(tuple(v0_xyz))]
    v1 = gkeys[geometric_key(tuple(v1_xyz))]
    surfaces_uv_vectors[face] = {'u_edge': (u0, u1),
                                 'v_edge': (v0, v1),
                                 'surface': brep_surface}
    brep_surfaces_dic[brep_surface] = {'u0': u0,
                                    'u1': u1,
                                    'v0': v0,
                                    'v1': v1}


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
draw_uv_vectors(mesh, surfaces_uv_vectors)
rs.EnableRedraw(True)

# ------------------------------------------------------------------------------
# surface uv subdivision
# ------------------------------------------------------------------------------

"""
#--------- Get integer division number for U,V  ---------------

nu = compas_rhino.rs.GetInteger('divide U into?')
if not nu or nu < 2:
    print('has to be larger than 2!!')
    #need to add a break point here or should we give a default n division anyways?
elif nu and nu > 2:
    nv = compas_rhino.rs.GetInteger('divide V into?')
    if not nv:
        nv=nu
    elif nv < 2:
        print('has to be larger than 2!!')
#--------------------------------------------------------------
"""

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
# edge subdivision
# ------------------------------------------------------------------------------


def subdivide_edge_strip(mesh, pick_edge, n):
    
    # get all the faces of the edge strip
    edge_strip = set(frozenset(edge) for edge in mesh.edge_strip(pick_edge))
    edge_strip_faces = set()
    
    for u, v in edge_strip:
        face1, face2 = mesh.edge_faces(u, v)
        if face1 is not None:
            edge_strip_faces.add(face1)
        if face2 is not None:
            edge_strip_faces.add(face2)
    
    # determine whether the face's u or v domain is aligned with the edge strip
    face_division_direction = {}
    for face in edge_strip_faces:
        u_edge = surfaces_uv_vectors[face]['u_edge']
        surface = surfaces_uv_vectors[face]['surface']
        if frozenset(u_edge) in edge_strip:
            face_division_direction[face] = 'divide_u'
            surface_to_uvmesh(surface, n, default)
        else:
            face_division_direction[face] = 'divide_v'
            surface_to_uvmesh(surface, default, n)
            
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
    
    return 


#add subdivision for one direction
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

# ------------------------------------------------------------------------------
# run command
# ------------------------------------------------------------------------------
default = 10
subd = surface_to_uvmesh(rhinosurface, default, default, weld=True)

artist1 = MeshArtist(subd)
artist1.draw_mesh()
artist.draw_edges(color=(100, 100, 0))

#----- need to make interactive......!!! -------

#Get subdivision number
n = compas_rhino.rs.GetInteger('divide into?')
if not n or n < 2:
    print('has to be larger than 2!!')
else:
    # user chooses an edge
    pick_edge = mesh_select_edge(mesh)
    subd2 = subdivide_edge_strip(subd, pick_edge, n)
    
    artist2 = MeshArtist(subd2)
    artist2.draw_mesh()
    artist.draw_edges(color=(0, 100, 100))

artist.clear()

# ------------------------------------------------------------------------------
# draw subdivide mesh
# ------------------------------------------------------------------------------
#artist = MeshArtist(subd)
#artist.draw_mesh()
