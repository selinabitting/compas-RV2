from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_rv2.rhino import get_scene
from compas_rv2.rhino import AttributesForm
from compas_rv2.rhino import ErrorHandler


__commandname__ = "RV2force_attributes"


@ErrorHandler()
def RunCommand(is_interactive):

    scene = get_scene()
    if not scene:
        return

    force = scene.get("force")[0]
    if not force:
        print("There is no ForceDiagram in the scene.")
        return

    AttributesForm.from_sceneNode(force)


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
