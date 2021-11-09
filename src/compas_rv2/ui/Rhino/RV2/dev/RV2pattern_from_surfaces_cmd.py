from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_rv2.rhino import get_scene
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import rv2_error

# import artemis stuff


__commandname__ = "RV2pattern_from_surfaces"


@rv2_error()
@rv2_undo
def RunCommand(is_interactive):

    # 0. checks to see if there is a scene in rhino
    scene = get_scene()
    if not scene:
        return

    # 1. select rhino surface or polysurfaces ...
    # guid = compas_rhino.select_surface(message='select a surface or a polysurface')
    # if not guid:
    #     return

    # 2. make mesh
    # mesh = artemis.function(guid)
    # or
    # vertices = [ ... ]
    # faces = [ ... ]

    # 3. turn mesh into a pattern object
    # pattern = Pattern.from_...

    # 4. hide input surface / polysurface ...
    # compas_rhino.rs.HideObject (guid)

    # 5. add the Pattern object to the Scene, then update/redraw
    # scene.clear()
    # scene.add(pattern, name='pattern')
    # scene.update()

    print("This function is not ready yet!")

    # print("Pattern object successfully created. Input surface or polysurface has been hidden.")


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
