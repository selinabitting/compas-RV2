from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rv2.rhino import get_scene
from compas_rv2.rhino import get_proxy
from compas.utilities import flatten
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import ErrorHandler


__commandname__ = "RV2pattern_smooth"


@ErrorHandler()
@rv2_undo
def RunCommand(is_interactive):
    scene = get_scene()
    if not scene:
        return

    proxy = get_proxy()
    if not proxy:
        return

    pattern = scene.get("pattern")[0]
    if not pattern:
        print("There is no Pattern in the scene.")
        return

    fixed = list(pattern.datastructure.vertices_where({'is_fixed': True}))

    if not fixed:
        print("Pattern has no fixed vertices! Smoothing requires fixed vertices.")
        return

    options = ['True', 'False']
    option = compas_rhino.rs.GetString("Press Enter to smooth or ESC to exit. Keep all boundaries fixed?", options[0], options)

    if option is None:
        print('Pattern smoothing aborted!')
        return

    if option == 'True':
        fixed = fixed + list(flatten(pattern.datastructure.vertices_on_boundaries()))

    pattern.datastructure.smooth_area(fixed=fixed)

    scene.update()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
