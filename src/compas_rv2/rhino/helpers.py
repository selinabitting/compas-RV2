from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import json
from ast import literal_eval

import scriptcontext as sc

import compas_rhino
from compas_rhino.forms import TextForm

from compas_rv2.datastructures import Pattern
from compas_rv2.datastructures import FormDiagram
from compas_rv2.datastructures import ForceDiagram
from compas_rv2.datastructures import ThrustDiagram


def match_vertices(diagram, keys):
    temp = compas_rhino.get_objects(name="{}.vertex.*".format(diagram.name))
    names = compas_rhino.get_object_names(temp)
    guids = []
    for guid, name in zip(temp, names):
        parts = name.split('.')
        key = literal_eval(parts[2])
        if key in keys:
            guids.append(guid)
    return guids


def match_edges(diagram, keys):
    temp = compas_rhino.get_objects(name="{}.edge.*".format(diagram.name))
    names = compas_rhino.get_object_names(temp)
    guids = []
    for guid, name in zip(temp, names):
        parts = name.split('.')[2].split('-')
        u = literal_eval(parts[0])
        v = literal_eval(parts[1])
        if (u, v) in keys or (v, u) in keys:
            guids.append(guid)
    return guids


def match_faces(diagram, keys):
    temp = compas_rhino.get_objects(name="{}.face.*".format(diagram.name))
    names = compas_rhino.get_object_names(temp)
    guids = []
    for guid, name in zip(temp, names):
        parts = name.split('.')
        key = literal_eval(parts[2])
        if key in keys:
            guids.append(guid)
    return guids


def select_vertices(diagram, keys):
    guids = match_vertices(diagram, keys)
    compas_rhino.rs.EnableRedraw(False)
    compas_rhino.rs.SelectObjects(guids)
    compas_rhino.rs.EnableRedraw(True)


def select_edges(diagram, keys):
    guids = match_edges(diagram, keys)
    compas_rhino.rs.EnableRedraw(False)
    compas_rhino.rs.SelectObjects(guids)
    compas_rhino.rs.EnableRedraw(True)


def select_faces(diagram, keys):
    guids = match_faces(diagram, keys)
    compas_rhino.rs.EnableRedraw(False)
    compas_rhino.rs.SelectObjects(guids)
    compas_rhino.rs.EnableRedraw(True)


def is_valid_file(filepath, ext):
    """Is the selected path a valid file.

    Parameters
    ----------
    filepath
    """
    if not filepath:
        return False
    if not os.path.exists(filepath):
        return False
    if not os.path.isfile(filepath):
        return False
    if not filepath.endswith(".{}".format(ext)):
        return False
    return True


def select_filepath_open(root, ext):
    """Select a filepath for opening a session.

    Parameters
    ----------
    root : str
        Base directory from where the file selection is started.
        If no directory is provided, the parent folder of the current
        Rhino document will be used
    ext : str
        The type of file that can be openend.

    Returns
    -------
    tuple
        The parent directory.
        The file name.
    None
        If the procedure fails.

    Notes
    -----
    The file extension is only used to identify the type of session file.
    Regardless of the provided extension, the file contents should be in JSON format.

    """
    ext = ext.split('.')[-1]
    filepath = compas_rhino.select_file(folder=root, filter=ext)
    if not is_valid_file(filepath, ext):
        print("This is not a valid session file: {}".format(filepath))
        return
    return filepath


def select_filepath_save(root, ext):
    """Select a filepath for saving a session."""
    filepath = compas_rhino.rs.SaveFileName('save', filter=ext, folder=root)
    if not filepath:
        return
    if filepath.split('.')[-1] != ext:
        filepath = "%s.%s" % (filepath, ext)
    return filepath


def get_rv2():
    if "RV2" not in sc.sticky:
        form = TextForm('Initialise the plugin first!', 'RV2')
        form.show()
        return None
    return sc.sticky["RV2"]


def get_scene():
    rv2 = get_rv2()
    if rv2:
        return rv2['scene']


def get_proxy():
    if "RV2.proxy" not in sc.sticky:
        form = TextForm('Initialise the plugin first!', 'RV2')
        form.show()
        return None
    return sc.sticky["RV2.proxy"]


def get_system():
    if "RV2.system" not in sc.sticky:
        form = TextForm('Initialise the plugin first!', 'RV2')
        form.show()
        return None
    return sc.sticky["RV2.system"]


def save_session():
    scene = get_scene()
    session = {
        "data": {"pattern": None, "form": None, "force": None},
        "settings": scene.settings,
    }
    pattern = scene.get('pattern')[0]
    if pattern:
        session['data']['pattern'] = pattern.datastructure.to_data()
    form = scene.get('form')[0]
    if form:
        session['data']['form'] = form.datastructure.to_data()
    force = scene.get('force')[0]
    if force:
        session['data']['force'] = force.datastructure.to_data()
    return session


def save_session_thrust():
    scene = get_scene()
    session = {
        "data": {
            "thrust": None
        },
        "settings": scene.settings,
    }
    thrust = scene.get('thrust')[0].datastructure

    faces = list(thrust.faces_where({'_is_loaded': False}))

    for face in faces:
        thrust.delete_face(face)

    if thrust:
        session['data']['thrust'] = thrust.to_data()

    return session


def load_session(session):
    print("loading session")
    scene = get_scene()
    scene.clear()
    if 'settings' in session:
        scene.settings = session['settings']
    if 'data' in session:
        data = session['data']
        if 'pattern' in data and data['pattern']:
            pattern = Pattern.from_data(data['pattern'])
            scene.add(pattern, name="pattern")
        else:
            if 'form' in data and data['form']:
                form = FormDiagram.from_data(data['form'])
                thrust = form.copy(cls=ThrustDiagram)  # this is not a good idea
                scene.add(form, name="form")
                scene.add(thrust, name="thrust")

            if 'force' in data and data['force']:
                force = ForceDiagram.from_data(data['force'])
                force.primal = form
                form.dual = force
                force.update_angle_deviations()
                scene.add(force, name="force")
    scene.update()


def record():
    session = json.loads(json.dumps(save_session()))
    sc.sticky["RV2.sessions"] = sc.sticky["RV2.sessions"][:sc.sticky["RV2.sessions.current"]+1]
    sc.sticky["RV2.sessions"].append(session)
    if len(sc.sticky["RV2.sessions"]) > 10:
        sc.sticky["RV2.sessions"] = sc.sticky["RV2.sessions"][-10:]
    sc.sticky["RV2.sessions.current"] = len(sc.sticky["RV2.sessions"]) - 1


def undo(sender, e):
    if e.Tag == "undo":
        if sc.sticky["RV2.sessions.current"] - 1 < 0:
            print("no more recorded sessions to undo")
            return
        sc.sticky["RV2.sessions.current"] -= 1
        session = sc.sticky["RV2.sessions"][sc.sticky["RV2.sessions.current"]]
        load_session(session)
        e.Document.AddCustomUndoEvent("RV2 Redo", undo, "redo")
    if e.Tag == "redo":
        if sc.sticky["RV2.sessions.current"] + 1 >= len(sc.sticky["RV2.sessions"]):
            print("no more recorded sessions to redo")
            return
        sc.sticky["RV2.sessions.current"] += 1
        session = sc.sticky["RV2.sessions"][sc.sticky["RV2.sessions.current"]]
        load_session(session)
        e.Document.AddCustomUndoEvent("RV2 Redo", undo, "undo")
    print("current sessions:", sc.sticky["RV2.sessions.current"]+1)
    print("total sessions:", len(sc.sticky["RV2.sessions"]))


def rv2_undo(command):
    def wrapper(*args, **kwargs):
        if not get_rv2():
            return
        sc.doc.EndUndoRecord(sc.doc.CurrentUndoRecordSerialNumber)
        undoRecord = sc.doc.BeginUndoRecord("RV2 Undo")
        if undoRecord == 0:
            print("undo record did not start")
        else:
            print("Custom undo recording", undoRecord)

        if len(sc.sticky["RV2.sessions"]) == 0:
            sc.sticky["RV2.sessions.current"] = 0
            record()
        command(*args, **kwargs)
        record()
        sc.doc.AddCustomUndoEvent("RV2 Undo", undo, "undo")
        if undoRecord > 0:
            sc.doc.EndUndoRecord(undoRecord)
    return wrapper
