import os
import json

HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, "../src/compas_rv2/ui/Rhino/RV2/dev/config.json")
FILE_O = os.path.join(HERE, "../src/compas_rv2/ui/Rhino/RV2/dev/RV2.rui")


def main():
    with open(FILE_I, "r") as f:
        config = json.load(f)

    macros = []
    for name in config["ui"]["macros"]:
        macros.append({
            "name": name,
            "script": "-_{}".format(name),
            "tooltip": "",
            "help_text": "",
            "button_text": name,
            "menu_text": name
        })

    rui = Rui(FILE_O)

    rui.init()
    rui.add_macros(macros)
    rui.add_menus(config["ui"]["menus"])
    rui.add_toolbars(config["ui"]["toolbars"])
    rui.add_toolbargroups(config["ui"]["toolbargroups"])
    rui.write()



# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    main()
