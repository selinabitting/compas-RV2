from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino

from compas_rv2.rhino import get_scene
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import ErrorHandler


__commandname__ = "RV2clear_all"

@ErrorHandler()
@rv2_undo
def RunCommand(is_interactive):

    scene = get_scene()
    if not scene:
        return

    options = ["Yes", "No"]
    option = compas_rhino.rs.GetString("Clear all RV2 objects?", strings=options, defaultString="No")
    if not option:
        return

    if option == "Yes":
        scene.clear()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    RunCommand(True)
