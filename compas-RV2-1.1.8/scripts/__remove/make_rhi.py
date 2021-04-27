import os
import shutil
from zipfile import ZipFile


HERE = os.path.dirname(__file__)


def make_rhi(plugin_dir):
    """Package the Rhino CommandPlugin into an .rhi

    Parameters
    ----------
    plugin_dir : str
        The path tho the base plugin directory.

    Returns
    -------
    None

    Examples
    --------
    >>> make_rhi('../ui/Rhino/RV2')

    """

    zip_path = "{}.zip".format(plugin_dir)
    rhi_path = "{}.rhi".format(plugin_dir)

    dev_dir = os.path.join(plugin_dir, 'dev')

    with ZipFile(zip_path, 'w') as zip_file:
        for root, dirs, files in os.walk(dev_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                zip_file.write(filepath, os.path.relpath(filepath, dev_dir))

    os.rename(zip_path, rhi_path)


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    # run from the command line
    # $ python make_rhi.py ../ui/Rhino/RV2

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('plugin_dir', help="The path to the plugin directory.")
    args = parser.parse_args()

    make_rhi(args.plugin_dir)
