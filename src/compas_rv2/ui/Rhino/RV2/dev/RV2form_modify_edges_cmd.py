from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rv2.rhino import get_scene
from compas.utilities import flatten
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import ModifyAttributesForm


__commandname__ = "RV2form_modify_edges"


@rv2_undo
def RunCommand(is_interactive):

    scene = get_scene()
    if not scene:
        return

    form = scene.get("form")[0]
    if not form:
        print("There is no FormDiagram in the scene.")
        return

    thrust = scene.get("thrust")[0]

    options = ["All", "Continuous", "Parallel", "Manual"]
    option = compas_rhino.rs.GetString("Selection Type.", strings=options)
    if not option:
        return

    if option == "All":
        keys = list(form.datastructure.edges())

    elif option == "Continuous":
        temp = form.select_edges()
        keys = list(set(flatten([form.datastructure.edge_loop(key) for key in temp])))

    elif option == "Parallel":
        temp = form.select_edges()
        keys = list(set(flatten([form.datastructure.edge_strip(key) for key in temp])))

    elif option == "Manual":
        keys = form.select_edges()

    if keys:
        current = scene.settings['RV2']['show.angles']
        scene.settings['RV2']['show.angles'] = False
        scene.update()

        ModifyAttributesForm.from_sceneNode(form, 'edges', keys)
        
        scene.settings['RV2']['show.angles'] = current
        # public = [name for name in form.datastructure.default_edge_attributes.keys() if not name.startswith("_")]
        # if form.update_edges_attributes(keys, names=public):
        if thrust:
            thrust.settings['_is.valid'] = False
        scene.update()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
