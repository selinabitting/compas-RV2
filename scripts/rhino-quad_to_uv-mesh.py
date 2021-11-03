from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import Rhino

import compas_rhino
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg

from compas.datastructures import Mesh
from compas.datastructures import meshes_join
from compas.utilities import geometric_key
from compas_rhino.utilities import select_surface
from compas_rhino.geometry import RhinoSurface

from compas_rhino.artists import MeshArtist

from Rhino.Geometry import Surface


# ------------------------------------------------------------------------------
# select rhino surface or polysurface
# ------------------------------------------------------------------------------
guid = select_surface()
rhinosurface = RhinoSurface.from_guid(guid)
mesh = rhinosurface.to_compas(cleanup=False)
print (type(rhinosurface))
#rs.HideObjects(guid)

#works but takes only for the outline of polysurface?
brep = Rhino.Geometry.Brep.TryConvertBrep(rhinosurface.geometry)
faces = brep.Faces
for face in faces:
    domain_u = face.Domain(0)
    domain_v = face.Domain(1)
    u0 = face.PointAt(domain_u[0], domain_v[0])
    u1 = face.PointAt(domain_u[1], domain_v[0])

#==========================
crs = compas_rhino.rs

surfaces = []
if rs.IsPolysurface(guid):
    surfaces = crs.ExplodePolysurfaces(guid)
elif rs.IsSurface(guid):
    surfaces = [guid]
else:
    raise Exception('Object is not a surface.')


mesh = Mesh()
for surface in surfaces:
    #brep = Rhino.Geometry.Brep.TryConvertBrep(surface.geometry)
    
    domain_u = rs.SurfaceDomain(surface, 0)
    domain_v = rs.SurfaceDomain(surface, 1)
    u0 = rg.Point2d(domain_u[1], domain_u[0])
    u1= rg.Point2d(domain_u[1], domain_v[0])
    u_vector = u1 - u0
    
    face = []
    face_vertices = []
    for loop in brep.Loops:
        curve = loop.To3dCurve()
        segments = curve.Explode()
        face_vertices.append(segments[0].PointAtStart)
    face = mesh.add_face(face_vertices)
    #mesh.update_face_attribute('surface', brep.Faces[0])
    
    u_edge = mesh.halfedge[u0][u1]
    halfedge_strip = mesh.halfedge_strip(u_edge)
    for edge in halfedge_strip:
        pt0 = rg.Point2d(edge[o])
        pt1 = rg.Point2d(edge[1])
        vector= pt1 - pt0
        if dot(u_vector,vector)==0:
            sueface = rg.Surface.Transpose(surface)
            #mesh.update_face_attribute('surface', brep.Faces[0])
            

for guid in surfaces:
    domain_u = rs.SurfaceDomain(guid, 0)
    domain_v = rs.SurfaceDomain(guid, 1)
    U_vector = domain_u[1] - domain_u[0] 
    V_vector = domain_v[1] - domain_v[0]
    surface = RhinoSurface.from_guid(guid)




for face in faces:
    domain_u = face.Domain(0)
    domain_v = face.Domain(1)
    u0 = face.PointAt(domain_u[0], domain_v[0])
    u1 = face.PointAt(domain_u[1], domain_v[0])
    


#surface= rg.Surface.Transpose(surface)

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
#start = u,v
#str_edges = mesh.edge_strip(start)
#str_halfedges = mesh.halfedge_strip(start)


# ------------------------------------------------------------------------------
# unify surface uv directions
# ------------------------------------------------------------------------------
# similar to compas.datastructures.mesh.orientation mesh_unify_cycles()
def unify_uv_direction(mesh, edge_curves):
    pass

center, cent_vector = rs.SurfaceAreaCentroid(guid)
#u = center[0]
#v = center[1]
#geo_surface = rs.coercesurface(rhinosurface)
#srf = rg.NurbsSurface.UVNDirectionsAt(geo_surface,u,v)
#bool, pt, vector = rg.Surface.Evaluate(geo_surface,u,v,numberderivatives)


# ------------------------------------------------------------------------------
# option 1: compare U,V with dot and Uvector
# ------------------------------------------------------------------------------

domain_u = rs.SurfaceDomain(surfaces[0], 0)
domain_v = rs.SurfaceDomain(surfaces[0], 1)
U_vector = domain_u[1] - domain_u[0] 
V_vector = domain_v[1] - domain_v[0]

for i,surface in enumerate(surfaces,1):
    dom_u = surface.Domain(0)
    U_vect = (dom_u[1] - dom_u[0]) 
    
    if dot(U_vector, U_vect)==0 :
        surface , swap = rg.Surface.Transpose(surface) #i think returns only 1 param=surface
    
    if swap==True:
        print ('Surface U,V succesfully swapped')
    else:
        print ('Surface U,V could not be swapped')
        
#---second way------------------------------------------

uvects = []
for surface in surfaces:
    domain_u = rs.SurfaceDomain(surface, 0)
    domain_v = rs.SurfaceDomain(surface, 1)
    Uvect = domain_u[1] - domain_u[0] 
    Vvect = domain_v[1] - domain_v[0]
    uvets.append(Uvect)

for uvect,surf in zip(uvects,surfaces):
    if dot(uvect[i],vect[i+1])==0:
        surf = rg.Surface.Transpose(surf)
        
# ------------------------------------------------------------------------------
# curve division by count number n
# ------------------------------------------------------------------------------

n = compas_rhino.rs.GetInteger('divide into?')
if not n or n < 2:
    print('has to be larger than 2!!')


def divide_curve(curve,n):
    params = curve.DivideByCount(n,True)
    crv_pts=[]
    for param in params:
        crv_pts.append(curve.PointAt(param))
    new_edges =[]
    for i in range(len(crv_pts)[1::]):
        crv = rs.AddLine(crv_pts[i-1],crv_pts[i])
        new_edges.append(crv)
    return crv_pts, new_edges

#get vertices of quad mesh
#add crv_pts on vertices list
#need to create faces. or mesh from polygon
#mesh.from_vertices_and_faces(pts,faces)

for crv in curves:
    points = divide_curve(crv,n)

new_edges = []


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
subd = surface_to_uvmesh(rhinosurface, nu=10, nv=5, weld=True)


# ------------------------------------------------------------------------------
# draw subdivide mesh
# ------------------------------------------------------------------------------
artist = MeshArtist(subd)
artist.draw_mesh()
