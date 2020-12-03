from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rv2.rhino import get_scene
from compas.utilities import flatten
from compas_rv2.rhino import rv2_undo
from compas_rv2.rhino import ModifyAttributesForm


__commandname__ = "RV2form_modify_vertices"


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

    # show the form vertices
    form_vertices = "{}::vertices".format(form.settings['layer'])
    compas_rhino.rs.ShowGroup(form_vertices)

    if thrust:
        # hide the thrust vertices
        thrust_vertices_free = "{}::vertices_free".format(thrust.settings['layer'])
        thrust_vertices_anchor = "{}::vertices_anchor".format(thrust.settings['layer'])
        compas_rhino.rs.HideGroup(thrust_vertices_free)
        compas_rhino.rs.HideGroup(thrust_vertices_anchor)

    compas_rhino.rs.Redraw()

    # selection options
    options = ["All", "ByContinuousEdges", "Manual"]
    option = compas_rhino.rs.GetString("Selection Type.", strings=options)
    if not option:
        scene.update()
        return

    if option == "All":
        keys = list(form.datastructure.vertices())

    elif option == "ByContinuousEdges":
        temp = form.select_edges()
        keys = list(set(flatten([form.datastructure.vertices_on_edge_loop(key) for key in temp])))

    elif option == "Manual":
        keys = form.select_vertices()

    if keys:
        ModifyAttributesForm.from_sceneNode(form, 'vertices', keys)
        # public = [name for name in form.datastructure.default_vertex_attributes.keys() if not name.startswith('_')]
        # if form.update_vertices_attributes(keys, names=public):
        if thrust:
            thrust.settings['_is.valid'] = False

    # the scene needs to be updated
    # even if the vertices where not modified
    # to reset group visibility to the configuration of settings
    scene.update()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
