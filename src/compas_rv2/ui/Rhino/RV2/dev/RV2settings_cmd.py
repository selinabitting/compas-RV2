from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_rv2.rhino import get_scene
from compas_rv2.rhino import SettingsForm


__commandname__ = "RV2settings"


def RunCommand(is_interactive):

    scene = get_scene()
    if not scene:
        return

    SettingsForm.from_scene(scene, object_types=["PatternObject", "FormObject", "ForceObject", "ThrustObject"], global_settings=["RV2", "Solvers"])

    scene.update()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    RunCommand(True)
