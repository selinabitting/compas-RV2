from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rhino.ui import CommandMenu
from compas_rv2.rhino import get_scene
from compas_rv2.datastructures import Pattern
from compas_rv2.rhino import SubdObject
from compas_rv2.rhino import rv2_undo


__commandname__ = "RV2pattern_from_polysurface"


def change_subdivision(subdobject):
    subdobject.change_draw_subd()


config = {
    "name": "modify",
    "message": "Modify",
    "options": [
        {
            "name": "Finish",
            "message": "Finish",
            "action": None
        },
        {
            "name": "ChangeSubdivision",
            "message": "Change_subdivision",
            "action": change_subdivision
        }
    ]
}


@rv2_undo
def RunCommand(is_interactive):
    scene = get_scene()
    if not scene:
        return

    # get untrimmed surface(s) -------------------------------------------------
    guid = compas_rhino.select_surface(message='select an untrimmed surface or a polysurface')

    if not guid:
        return

    compas_rhino.rs.HideObjects(guid)

    # make subd object ---------------------------------------------------------
    subdobject = SubdObject.from_guid(guid)

    if not subdobject:
        return

    compas_rhino.rs.HideObjects(guid)
    subdobject.draw_coarse()
    subdobject.get_draw_default_subd()
    subdobject.draw_subd()

    # interactively  modify subdivision ----------------------------------------
    while True:
        menu = CommandMenu(config)
        action = menu.select_action()

        if not action or action is None:
            subdobject.clear()
            print("Pattern from surface(s) aborted!")
            compas_rhino.rs.ShowObjects(guid)
            return

        if action['name'] == 'Finish':
            break

        action['action'](subdobject)

    # make pattern -------------------------------------------------------------
    mesh = subdobject.subd
    xyz = mesh.vertices_attributes('xyz')
    faces = [mesh.face_vertices(fkey) for fkey in mesh.faces()]
    pattern = Pattern.from_vertices_and_faces(xyz, faces)

    # clear skeleton
    layer = subdobject.settings['layer']
    subdobject.clear()
    compas_rhino.delete_layers([layer])

    scene.clear()
    scene.add(pattern, name='pattern')
    scene.update()

    print("Pattern object successfully created. Input surface(s) have been hidden.")


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
