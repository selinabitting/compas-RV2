import compas
import compas_rhino
from compas_rhino.install import install
from compas_rhino.uninstall import uninstall
from compas_rhino.install_plugin import install_plugin
from compas_rhino.uninstall_plugin import uninstall_plugin
import argparse
import os
import json
import sys
import importlib
from shutil import copyfile
from subprocess import call


PLUGIN_NAME = "RV2"
PACKAGES = ['compas', 'compas_rhino', 'compas_tna', 'compas_cloud', 'compas_skeleton', 'compas_rv2']


@compas.plugins.plugin(category='install', pluggable_name='installable_rhino_packages', tryfirst=True)
def default_installable_rhino_packages():
    return PACKAGES


def is_editable(project_name):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, "%s.egg-link" % project_name)
        if os.path.isfile(egg_link):
            return True
    return False


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='RhinoVault2 Installation command-line utility.')

    parser.add_argument('--remove_plugins', action='store_true', help="remove all existing plugins")
    parser.add_argument('--remove_packages', action='store_true', help="remove all existing compas packages")
    parser.add_argument('--version', default='7.0', choices=['6.0', '7.0'], help="remove all existing compas packages")
    args = parser.parse_args()

    print("\n", "-"*10, "Checking packages", "-"*10)

    for p in PACKAGES:
        try:
            importlib.import_module(p)
        except ImportError:
            print(p, "ERROR: cannot be imported, make sure it is installed")
            raise
        else:
            print('   {} {}'.format(p.ljust(20), "OK"))

    is_dev = is_editable("compas-RV2")
    print("RV2 is editable install: ", is_dev)

    if args.remove_plugins:
        print("\n", "-"*10, "Removing existing plugins", "-"*10)
        python_plugins_path = compas_rhino._get_rhino_pythonplugins_path(args.version)
        print("Plugin location: ", python_plugins_path)
        plugins = os.listdir(python_plugins_path)
        for p in plugins:
            uninstall_plugin(p, version=args.version)

    if args.remove_packages:
        print("\n", "-"*10, "Removing existing packages", "-"*10)
        uninstall()

    print("\n", "-"*10, "Installing RV2 python plugin", "-"*10)

    plugin_path = os.path.dirname(__file__)
    plugin_path = os.path.join(plugin_path, 'ui/Rhino/RV2')
    plugin_path = os.path.abspath(plugin_path)

    if os.path.exists(plugin_path):
        python_plugins_path = compas_rhino._get_rhino_pythonplugins_path(args.version)
        print("Plugin path:", python_plugins_path)
        install_plugin(plugin_path, version=args.version)
    else:
        raise RuntimeError("%s does not exist" % plugin_path)

    print("\n", "-"*10, "Installing COMPAS packages", "-"*10)

    if not is_dev:
        os.environ["CONDA_PREFIX"] = ""
        os.environ["CONDA_DEFAULT_ENV"] = ""
        os.environ["CONDA_EXE"] = ""

    print("CONDA_PREFIX", os.environ.get("CONDA_PREFIX"))
    print("CONDA_DEFAULT_ENV", os.environ.get("CONDA_DEFAULT_ENV"))
    print("CONDA_EXE", os.environ.get("CONDA_EXE"))

    install(version=args.version)

    if compas.WINDOWS:
        call(sys.executable + " " + os.path.join(plugin_path, 'dev', 'rui.py'), shell=True)
        copyfile(os.path.join(plugin_path, 'dev', 'RV2.rui'), os.path.join(python_plugins_path, '..', '..', 'UI', 'RV2.rui'))

    print("\n", "-"*10, "Installation is successful", "-"*10)

    print("\n", "-"*10, "Registering Installation", "-"*10)

    os.makedirs(compas.APPDATA, exist_ok=True)
    register_json_path = os.path.join(compas.APPDATA, "compas_plugins.json")

    if os.path.exists(register_json_path):
        register_json = json.load(open(register_json_path))
        if not isinstance(register_json["Plugins"], dict):
            register_json["Plugins"] = {}
    else:
        register_json = {"Plugins": {}, "Current": None}

    plugin_info = {
        "dev": is_dev,
        "path": plugin_path,
        "python": sys.executable,
        "packages": {},
    }

    for name in PACKAGES:
        package = importlib.import_module(name)
        plugin_info["packages"][name] = {"version": package.__version__}

    print(plugin_info)

    print("registering to", register_json_path)

    register_json["Plugins"][PLUGIN_NAME] = plugin_info
    register_json["Current"] = PLUGIN_NAME

    print(" "*4, plugin_path, "is registered")

    for name in dict(register_json["Plugins"]):
        plugin = register_json["Plugins"][name]
        if not os.path.exists(plugin["path"]):
            del register_json["Plugins"][name]
            print("    Removed un-existed path: ", plugin_path)

    json.dump(register_json, open(register_json_path, "w"), indent=4)

    print("\n", "-"*10, "Installation is Registered", "-"*10)
