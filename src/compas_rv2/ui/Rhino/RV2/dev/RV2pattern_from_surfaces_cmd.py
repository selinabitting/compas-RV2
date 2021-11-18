from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from compas.datastructures import attributes

import compas_rhino
import math
from compas_rv2.datastructures import SubdMesh
from compas_rv2.datastructures import Pattern

from compas_rv2.rhino import get_scene
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import rv2_error

from compas_rhino.conduits import LinesConduit
from rhinoscript.userdata import SetDocumentUserText


__commandname__ = "RV2pattern_from_surfaces"


def divide_edge_strip_faces(mesh, edge):

    is_strip_quad = True  # check whether the edge_strip contains quads or not
    
    strip_edge = mesh.subd_edge_strip(edge)
    edge_strip_faces = mesh.edge_strip_faces(strip_edge)

    for face in edge_strip_faces:
        if not mesh.face_attributes(face, 'is_quad'):
            is_strip_quad = False

    # entering subdivision number
    if is_strip_quad:
        nu_or_nv = compas_rhino.rs.GetInteger('divide into?', minimum=2)

    else:
        while True:
            nu_or_nv = compas_rhino.rs.GetInteger('choose an even integer', minimum=2)
            if (nu_or_nv & (nu_or_nv - 1) == 0) and nu_or_nv != 0:
                break
            else:
                print('division number has to be power of 2!')

    for face in edge_strip_faces:
        quad = mesh.face_attributes(face, 'is_quad')

        if quad:
            u_edge = mesh.face_attributes(face, 'u_edge')
            if frozenset(u_edge) in strip_edge:
                mesh.face_attribute(face, 'nu', nu_or_nv)
            else:
                mesh.face_attributes(face,'nv', nu_or_nv)

        else:
            n = math.log(nu_or_nv) / math.log(2)
            mesh.face_attributes(face, 'n', int(n))
            
    return edge_strip_faces


def update_nu_nv(mesh):
    
    quad_mesh = True  # check whether the mesh contains nonquads or not

    for face in mesh.faces():
        if not mesh.face_attributes(face, 'is_quad'):
            quad_mesh = False

    if quad_mesh:
        nu = compas_rhino.rs.GetInteger('divide U into?', minimum=2)
        mesh.face_attribute(face, 'nu', nu)
        nv = compas_rhino.rs.GetInteger('divide V into?', minimum=2)
        mesh.face_attribute(face, 'nv', nv)
    else:
        while True:
            nu_or_nv = compas_rhino.rs.GetInteger('choose an even integer', minimum=2)
            if (nu_or_nv & (nu_or_nv - 1) == 0) and nu_or_nv != 0:
                break
            else:
                print('division number has to be power of 2!')

        for face in mesh.faces():
            quad = mesh.face_attributes(face, 'is_quad')
            if quad:
                mesh.face_attribute(face, 'nu', nu_or_nv)
                mesh.face_attributes(face,'nv', nu_or_nv)
            else:
                n = math.log(nu_or_nv) / math.log(2)
                mesh.face_attributes(face, 'n', int(n))

def interior_edge_lines(mesh):
    interior_edges = set(list(mesh.edges())) - set(list(mesh.edges_on_boundary()))

    lines = []
    for u, v in interior_edges:
        u_xyz = mesh.vertex_coordinates(u)
        v_xyz = mesh.vertex_coordinates(v)
        lines.append([u_xyz, v_xyz])
    return lines


@rv2_error()
@rv2_undo
def RunCommand(is_interactive):

    # 0. checks to see if there is a scene in rhino
    scene = get_scene()
    if not scene:
        return

    # 1. select rhino surface or polysurfaces ...
    guid = compas_rhino.select_surface()
    compas_rhino.rs.HideObjects(guid)

    # 2. make subdmesh and add it to the scene
    subdmesh = SubdMesh.from_guid(guid)

    scene.add(subdmesh, name='subd')
    subd = scene.get("subd")[0]

    # default subdivision
    subd1 = subd.datastructure.subdivide_all_faces()

    # 3. setup conduit to temporarily display subdmeshes
    conduit = LinesConduit([])
    conduit.enable()
    conduit.lines = interior_edge_lines(subd1)
    conduit.thickness = 0
    conduit.color = (125, 125, 125)
    scene.update()

    # ==========================================================================
    #   iterative subdivision
    # ==========================================================================
    options = ["Subdivide Mesh", "Subdivide edge strip", "Finish Subdivision"]
    
    while True:
        option = compas_rhino.rs.GetString("Modify Subdivision", strings=options)

        if not option:
            return

        if option == "Subdivide Mesh":
            subd1 = subd.datastructure
            subd = update_nu_nv(subd1)
            subd1 = subd.datastructure.subdivide_all_faces()
            
        elif option == "Subdivide edge strip":
            edge = subd1.select_edge()
            compas_rhino.rs.UnselectAllObjects()
            compas_rhino.rs.Redraw()
            subd1 = subd.datastructure
            strip_faces = divide_edge_strip_faces(subd1, edge)
            subd1 = subd1.subdivide_all_faces(strip_faces)

        elif option == "Finish Subdivision":
            break

    conduit.lines = interior_edge_lines(subd1)
    scene.update()

    # ==========================================================================

    # 8. make pattern from subdmesh
    
    xyz = subd1.vertices_attributes('xyz')
    faces = [subd1.face_vertices(fkey) for fkey in subd1.faces()]
    pattern = Pattern.from_vertices_and_faces(xyz, faces)
    conduit.disable()
    #pattern = Pattern.from_data(subd1.data)

    # 9. update scene
    scene.clear()
    scene.add(pattern, name='pattern')
    scene.update()

    # print("Pattern object successfully created. Input surface or polysurface has been hidden.")

    print("This function is not ready yet!")


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
