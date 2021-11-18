from collections import defaultdict

import compas_rhino

from compas_rhino.conversions import RhinoCurve
from compas_rhino.conversions import RhinoPoint
from compas.utilities import geometric_key
from compas.utilities import pairwise
from compas.geometry import Polyline
from compas.artists import Artist
from compas.datastructures import Mesh
from compas.datastructures import Network
from compas.datastructures import network_polylines
from compas.datastructures import trimesh_face_circle

from compas.rpc import Proxy

triangulation = Proxy('compas_cgal.triangulation')

# keep track of constraint curves

gkey_constraints = defaultdict(list)

# select outer boundary

guid = compas_rhino.select_curve('Select the outer boundary.')
compas_rhino.rs.UnselectAllObjects()
compas_rhino.redraw()

# compute discretisation length

bbox = compas_rhino.rs.BoundingBox([guid])
a = RhinoPoint.from_geometry(bbox[0]).to_compas()
b = RhinoPoint.from_geometry(bbox[2]).to_compas()

diagonal = b - a

D = 0.05 * diagonal.length

# explode and discretise

boundary = []
segments = compas_rhino.rs.ExplodeCurves([guid])
for segment in segments:
    curve = RhinoCurve.from_guid(segment).to_compas()
    N = max(int(curve.length() / D), 1)
    _, points = curve.divide_by_count(N, return_points=True)
    for point in points:
        gkey = geometric_key(point)
        gkey_constraints[gkey].append(segment)
    boundary.extend(points)

compas_rhino.rs.DeleteObjects(segments)

# select internal boundaries

guids = compas_rhino.select_curves('Select the inner boundaries.')
compas_rhino.rs.UnselectAllObjects()
compas_rhino.redraw()

holes = []
if guids:
    for guid in guids:
        segments = compas_rhino.rs.ExplodeCurves([guid])
        for segment in segments:
            curve = RhinoCurve.from_guid(segment).to_compas()
            N = max(int(curve.length() / D), 1)
            _, points = curve.divide_by_count(N, return_points=True)
            for point in points:
                gkey = geometric_key(point)
                gkey_constraints[gkey].append(segment)
            holes.append(points)
        compas_rhino.rs.DeleteObjects(segments)

# triangulate

vertices, faces = triangulation.constrained_delaunay_triangulation(boundary, holes=holes)
vertices[:] = [[float(x), float(y), float(z)] for x, y, z in vertices]

mesh = Mesh.from_vertices_and_faces(vertices, faces)

# print(mesh.is_valid())

artist = Artist(mesh, layer='CDT')
artist.clear_layer()
artist.draw_vertices()
artist.draw_edges()

Artist.redraw()

# face graph

facegraph = Network()

face_node = {}
gkey_face = {}

for face in mesh.faces_where({'face_degree': 3}):
    circle = trimesh_face_circle(mesh, face)
    point = circle[0]
    gkey = geometric_key(point)
    node = facegraph.add_node(x=point[0], y=point[1], z=point[2])
    gkey_face[gkey] = face
    face_node[face] = node

for face in mesh.faces():
    circle = trimesh_face_circle(mesh, face)
    point = circle[0]
    gkey = geometric_key(point)
    if gkey in gkey_face:
        face_node[face] = face_node[gkey_face[gkey]]
        continue
    node = facegraph.add_node(x=point[0], y=point[1], z=point[2])
    gkey_face[gkey] = face
    face_node[face] = node

for face in mesh.faces():
    a = face_node[face]
    for nbr in mesh.face_neighbors(face):
        b = face_node[nbr]
        if a == b:
            continue
        if not facegraph.has_edge(a, b, directed=False):
            facegraph.add_edge(a, b)

artist = Artist(facegraph, layer='FaceGraph')
artist.clear_layer()
artist.draw_nodes()
artist.draw_edges()

Artist.redraw()

# maps

cornerfaces = list(mesh.faces_where({'face_degree': 1}))
cornervertices = list(mesh.vertices_where({'vertex_degree': 2}))
singularfaces = list(mesh.faces_where({'face_degree': 3}))

singularcorners = []
for face in singularfaces:
    singularcorners += mesh.face_vertices(face)
singularcorners = list(set(singularcorners))

# skeleton branches

polylines = network_polylines(facegraph)

branches = []

# singularity - singularity

for polyline in polylines:
    a = polyline[0]
    b = polyline[-1]
    a_face = gkey_face[geometric_key(a)]
    b_face = gkey_face[geometric_key(b)]
    if a_face in singularfaces and b_face in singularfaces:
        branches.append(polyline)

# singularity - boundary

for face in singularfaces:
    a = trimesh_face_circle(mesh, face)[0]
    for vertex in mesh.face_vertices(face):
        b = mesh.vertex_coordinates(vertex)
        branches.append([a, b])

# boundaries

splitvertices = set(cornervertices + singularcorners)

for boundary in mesh.vertices_on_boundaries():
    splits = set(boundary).intersection(splitvertices)
    if not splits:
        continue
    splits = sorted(splits, key=lambda x: boundary.index(x))
    for a, b in pairwise(splits):
        i = boundary.index(a)
        j = boundary.index(b)
        vertices = boundary[i:j + 1]
        points = [mesh.vertex_coordinates(vertex) for vertex in vertices]
        branches.append(points)
    i = boundary.index(splits[-1])
    j = boundary.index(splits[0])
    vertices = boundary[i:] + boundary[:j + 1]
    points = [mesh.vertex_coordinates(vertex) for vertex in vertices]
    if points:
        branches.append(points)

compas_rhino.clear_layer('Branches')

for polyline in branches:
    artist = Artist(Polyline(polyline), layer='Branches')
    artist.draw()

Artist.redraw()

# coarse mesh

lines = []
for polyline in branches:
    a = polyline[0]
    b = polyline[-1]
    lines.append([a, b])

coarse = Mesh.from_lines(lines, delete_boundary_face=False)

for face in list(coarse.faces()):
    points = coarse.face_coordinates(face)
    if any(geometric_key(point) not in gkey_constraints for point in points):
        continue
    coarse.delete_face(face)

artist = Artist(coarse, layer='CoarseMesh')
artist.clear_layer()
artist.draw_vertices()
artist.draw_faces()

Artist.redraw()

# constraints

coarse.update_default_vertex_attributes(constraint=None, is_fixed=False)
coarse.update_default_edge_attributes(constraint=None)

for vertex in coarse.vertices():
    gkey = geometric_key(coarse.vertex_coordinates(vertex))
    constraints = gkey_constraints.get(gkey)
    if not constraints:
        continue
    if len(constraints) > 1:
        coarse.vertex_attribute(vertex, 'is_fixed', True)
    else:
        coarse.vertex_attribute(vertex, 'constraint', constraints[0])

for edge in coarse.edges():
    a, b = coarse.vertices_attribute('constraint', keys=edge)
    if a == b:
        coarse.edge_attribute(edge, 'constraint', a)

# dense mesh

edges = []
for edge in coarse.edges():
    if not coarse.is_edge_on_boundary(*edge):
        edges.append(edge)

strips = []
while edges:
    strip = coarse.edge_strip(edge)
    for u, v in strip:
        if (u, v) in edges:
            edges.remove((u, v))
        elif (v, u) in edges:
            edges.remove((v, u))
    strips.append(strip)
    break

dense = coarse.copy()

# subd mesh

# subd = coarse.subdivide(scheme='quad', k=2)

# subd.update_default_vertex_attributes(constraint=None, is_fixed=False)
# subd.update_default_edge_attributes(constraint=None)

# for vertex in coarse.vertices():
#    subd.vertex_attribute(vertex, 'constraint', coarse.vertex_attribute(vertex, 'constraint'))
#    subd.vertex_attribute(vertex, 'is_fixed', coarse.vertex_attribute(vertex, 'is_fixed'))

# color = {}
# color.update({vertex: (0, 255, 0) for vertex in subd.vertices_where_predicate(lambda key, attr: attr['constraint'] is not None)})
# color.update({vertex: (255, 0, 0) for vertex in subd.vertices_where({'is_fixed': True})})

# artist = Artist(subd, layer='SubdMesh')
# artist.clear_layer()
# artist.draw_vertices(color=color)
# artist.draw_faces()

# Artist.redraw()
