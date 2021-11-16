from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rv2.datastructures import SubdMesh
from compas_rv2.datastructures import Pattern

from compas_rv2.rhino import get_scene
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import rv2_error


__commandname__ = "RV2pattern_from_surfaces"


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

    # 2. make mesh and add it to the scene
    subdmesh = SubdMesh.from_guid(guid)
    scene.add(subdmesh, name='subd')
    scene.update()

    subd = scene.get("subd")[0]
    subd.artist.draw_vertexlabels()
    subd.artist.draw_facelabels(color=(0, 0, 0))

    # 3. select edge
    edge = subd.select_edge()
    compas_rhino.rs.UnselectAllObjects()
    compas_rhino.rs.Redraw()

    # 4. edge strip
    strip_edge = subd.datastructure.subd_edge_strip(edge)

    # 5. update nu, nv and/or n using strip_edge

    # 6. subdivide

    # 7. turn mesh into a pattern object
    # pattern = Pattern.from_...

    # 8. add the Pattern object to the Scene, then update/redraw
    # scene.clear()
    # scene.add(pattern, name='pattern')
    scene.update()

    # print("Pattern object successfully created. Input surface or polysurface has been hidden.")

    print("This function is not ready yet!")


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
