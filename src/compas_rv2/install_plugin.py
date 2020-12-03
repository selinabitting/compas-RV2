import os
import imp

import compas_rhino

from compas._os import create_symlinks
from compas._os import remove_symlinks


__all__ = ['install_plugin']


def install_plugin(version=None):
    """Install a Rhino Python Command Plugin.

    Parameters
    ----------
    version : {'5.0', '6.0', '7.0'}, optional
        The version of Rhino for which the plugin should be installed.
        Default is ``'6.0'``.

    Notes
    -----
    The version info is only relevant for Rhino on Windows.

    The function creates an *editable install*, which means that the plugin
    folder is *symlinked* into the correct location so Rhino can find and load it.
    The contents of the source folder can still be edited and next time you start
    Rhino those canges will be reflected in the loaded plugin.

    Examples
    --------

    """
    if version not in ('5.0', '6.0', '7.0'):
        version = '6.0'

    print(os.path.dirname(__file__))

    # if not os.path.isdir(plugin):
    #     raise Exception('Cannot find the plugin: {}'.format(plugin))

    # plugin_dir = os.path.abspath(plugin)

    # plugin_path, plugin_name = os.path.split(plugin_dir)
    # if not plugin_path:
    #     plugin_path = os.getcwd()

    # plugin_dev = os.path.join(plugin_dir, 'dev')

    # if not os.path.isdir(plugin_dev):
    #     raise Exception('The plugin does not contain a dev folder.')

    # plugin_info = os.path.join(plugin_dev, '__plugin__.py')

    # if not os.path.isfile(plugin_info):
    #     raise Exception('The plugin does not contain plugin info.')

    # __plugin__ = imp.load_source('__plugin__', plugin_info)

    # if not __plugin__.id:
    #     raise Exception('Plugin id is not set.')

    # if not __plugin__.title:
    #     raise Exception('Plugin title is not set.')

    # plugin_fullname = "{}{}".format(__plugin__.title, __plugin__.id)

    # python_plugins_path = compas_rhino._get_python_plugins_path(version)

    # if not os.path.exists(python_plugins_path):
    #     os.mkdir(python_plugins_path)

    # source = plugin_dir
    # destination = os.path.join(python_plugins_path, plugin_fullname)

    # print('Installing PlugIn {} to Rhino PythonPlugIns.'.format(plugin_name))

    # remove_symlinks([destination])
    # create_symlinks([(source, destination)])

    # print()
    # print('PlugIn {} Installed.'.format(plugin_name))
    # print()
    # print('Restart Rhino and open the Python editor at least once to make it available.')


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description='COMPAS Rhino PLugin Installation command-line utility.')

    parser.add_argument('-v', '--version', choices=['5.0', '6.0', '7.0'], default='6.0', help="The version of Rhino.")

    args = parser.parse_args()

    install_plugin(version=args.version)
