from __future__ import print_function
from __future__ import absolute_import
from __future__ import division


import rhinoscriptsyntax as rs

from compas.datastructures import Mesh
from compas.datastructures.mesh.subdivision import mesh_fast_copy

from compas.geometry import centroid_points

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
# modified catmull clark
# ------------------------------------------------------------------------------
def mesh_subdivide_catmullclark(mesh, k=2, fixed=None):

    cls = type(mesh)

    if not fixed:
        fixed = []
    fixed = set(fixed)

    def project_to_surface(surface_guid, (x, y, z)):
        px, py, pz = rs.BrepClosestPoint(guid, (x, y, z))[0]
        return px, py, pz

    for _ in range(k):
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
            # crease = mesh.edge_attribute((u, v), 'crease') or 0
            crease = k + 1 # this ensures that boundary vertices remain fixed

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

        for w, crease in edgepoints:
            if not crease:
                x, y, z = centroid_points(
                    [key_xyz[nbr] for nbr in subd.halfedge[w]])
                subd.vertex[w]['x'] = x
                subd.vertex[w]['y'] = y
                subd.vertex[w]['z'] = z

        # ----------------------------------------------------------------------
        # smooth

        # move each vertex to the weighted average of itself, the neighboring
        # centroids and the neighboring mipoints

        for key in mesh.vertices():

            if key in fixed:
                continue

            nbrs = mesh.vertex_neighbors(key)
            creases = mesh.edges_attribute('crease', keys=[(key, nbr) for nbr in nbrs])

            C = sum(1 if crease else 0 for crease in creases)

            if C < 2:
                fnbrs = [mesh.face_centroid(fkey) for fkey in mesh.vertex_faces(key) if fkey is not None]
                enbrs = [key_xyz[nbr] for nbr in subd.halfedge[key]]  # this should be the location of the original neighbour
                n = len(enbrs)
                v = n - 3.0
                F = centroid_points(fnbrs)
                E = centroid_points(enbrs)
                V = key_xyz[key]
                x = (F[0] + 2.0 * E[0] + v * V[0]) / n
                y = (F[1] + 2.0 * E[1] + v * V[1]) / n
                z = (F[2] + 2.0 * E[2] + v * V[2]) / n

                subd.vertex[key]['x'] = x
                subd.vertex[key]['y'] = y
                subd.vertex[key]['z'] = z

            elif C == 2:
                V = key_xyz[key]
                E = [0, 0, 0]
                for nbr, crease in zip(nbrs, creases):
                    if crease:
                        x, y, z = key_xyz[nbr]
                        E[0] += x
                        E[1] += y
                        E[2] += z
                x = (6 * V[0] + E[0]) / 8
                y = (6 * V[1] + E[1]) / 8
                z = (6 * V[2] + E[2]) / 8

                subd.vertex[key]['x'] = x
                subd.vertex[key]['y'] = y
                subd.vertex[key]['z'] = z

            else:
                pass

        mesh = subd

    subd2 = cls.from_data(mesh.data)
    return subd2


# ------------------------------------------------------------------------------
# run command
# ------------------------------------------------------------------------------
subd = mesh_subdivide_catmullclark(mesh, k=3)


# ------------------------------------------------------------------------------
# draw subdivide mesh
# ------------------------------------------------------------------------------
artist = MeshArtist(subd)
artist.draw_mesh()
