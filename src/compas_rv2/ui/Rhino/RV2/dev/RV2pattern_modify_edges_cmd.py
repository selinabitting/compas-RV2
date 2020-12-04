from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rv2.rhino import get_scene
from compas.utilities import flatten
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import ModifyAttributesForm


__commandname__ = "RV2pattern_modify_edges"


@rv2_undo
def RunCommand(is_interactive):

    scene = get_scene()
    if not scene:
        return

    pattern = scene.get("pattern")[0]
    if not pattern:
        print("There is no Pattern in the scene.")
        return

    options = ["All", "Continuous", "Parallel", "Manual"]
    option = compas_rhino.rs.GetString("Selection Type", strings=options)

    if not option:
        return

    if option == "All":
        keys = keys = list(pattern.datastructure.edges())

    elif option == "Continuous":
        temp = pattern.select_edges()
        keys = list(set(flatten([pattern.datastructure.edge_loop(key) for key in temp])))

    elif option == "Parallel":
        temp = pattern.select_edges()
        keys = list(set(flatten([pattern.datastructure.edge_strip(key) for key in temp])))

    elif option == "Manual":
        keys = pattern.select_edges()

    if keys:
        ModifyAttributesForm.from_sceneNode(pattern, 'edges', keys)
        # public = [name for name in pattern.datastructure.default_edge_attributes.keys() if not name.startswith('_')]
        # if pattern.update_edges_attributes(keys, names=public):
        scene.update()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
