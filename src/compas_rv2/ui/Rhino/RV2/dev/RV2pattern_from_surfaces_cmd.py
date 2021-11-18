from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rv2.datastructures import SubdMesh
from compas_rv2.datastructures import Pattern

from compas_rv2.rhino import get_scene
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import rv2_error

from compas_rhino.conduits import LinesConduit


__commandname__ = "RV2pattern_from_surfaces"


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

    # 4. select edge
    edge = subd.select_edge()
    compas_rhino.rs.UnselectAllObjects()

    # 5. edge strip

    # 6. update nu, nv and/or n using strip_edge

    # 7. subdivide

    # ==========================================================================

    # 8. make pattern from subdmesh
    conduit.disable()
    pattern = Pattern.from_data(subd1.data)

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
