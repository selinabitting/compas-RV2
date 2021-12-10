import compas
import compas_rhino
from compas_rhino.install import install
from compas_rhino.install_plugin import install_plugin
import argparse
import os
import sys
from shutil import copyfile
from subprocess import call

PACKAGES = ['compas', 'compas_rhino', 'compas_tna', 'compas_cloud', 'compas_skeleton', 'compas_rv2']

def get_version_from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', choices=['5.0', '6.0', '7.0'], default='7.0')
    args = parser.parse_args()
    return compas_rhino._check_rhino_version(args.version)

@compas.plugins.plugin(category='install', pluggable_name='installable_rhino_packages', tryfirst=True)
def default_installable_rhino_packages():
    return PACKAGES

@compas.plugins.plugin(category='install')
def after_rhino_install(installed_packages):

    if not set(PACKAGES).issubset(set(installed_packages)):
        return []

    print("\n", "-"*10, "Installing RV2 python plugin", "-"*10)

    plugin_path = os.path.dirname(__file__)
    plugin_path = os.path.join(plugin_path, 'ui/Rhino/RV2')
    plugin_path = os.path.abspath(plugin_path)

    version = get_version_from_args()

    if os.path.exists(plugin_path):
        python_plugins_path = compas_rhino._get_python_plugins_path(version)
        print("Plugin path:", python_plugins_path)
        install_plugin(plugin_path, version=version)
    else:
        raise RuntimeError("%s does not exist" % plugin_path)

    print("\n", "-"*10, "Generating rui", "-"*10)

    if compas.WINDOWS:
        call(sys.executable + " " + os.path.join(plugin_path, 'dev', 'rui.py'), shell=True)
        copyfile(os.path.join(plugin_path, 'dev', 'RV2.rui'), os.path.join(python_plugins_path, '..', '..', 'UI', 'RV2.rui'))
        print()
    
    print("\n", "-"*10, "All finished", "-"*10)

    return []


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='RhinoVault2 Installation command-line utility.')

    parser.add_argument('-v','--rhino_version', default='7.0', choices=['6.0', '7.0','8.0'])
    args = parser.parse_args()

    install(args.rhino_version)