from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_rv2.rhino import get_scene
from collections import OrderedDict

import Eto.Drawing as drawing
import Eto.Forms as forms
import Rhino.UI

import json
import os
import importlib
import sys


__all__ = ["MenuForm"]

HERE = os.path.dirname(__file__)
UI_FOLDER = os.path.join(HERE, "..", "..", "ui/Rhino/RV2/dev")
sys.path.append(UI_FOLDER)

class MenuForm(forms.Form):

    def setup(self):
        self.Owner = Rhino.UI.RhinoEtoApp.MainWindow
        self.Title = "RhinoVault2"
        layout = forms.StackLayout()
        layout.Spacing = 5
        self.load_config(layout)
        self.Width = 300

        self.Content = forms.Scrollable()
        self.Content.Content = layout
        self.Padding = drawing.Padding(12)
        self.Resizable = True

    def load_config(self, layout):
        config = json.load(open(os.path.join(UI_FOLDER, "config.json")))
        menu = config["ui"]["menus"][0]
        commands = {cmd["name"]:cmd for cmd in config["ui"]["commands"]}
        self.add_items(menu["items"], layout, commands)

    def add_items(self, items, layout, commands):
        for item in items:
            if "command" in item:
                cmd = commands[item["command"]]
                button = forms.Button(Text=cmd["menu_text"])
                layout.Items.Add(button)
                package = importlib.import_module("%s_cmd"%item["command"])
                def on_click(package):
                    def _on_click(sender, e):
                        package.RunCommand(True)
                    return _on_click

                button.Click += on_click(package)

            if "items" in item:
                sub_layout = forms.DynamicLayout()
                sub_layout.Spacing = drawing.Size(5, 0)
                collapseButton = forms.Button(Text="+", MinimumSize = drawing.Size.Empty)
                sub_layout.AddRow(forms.Label(Text=item["name"]), collapseButton)
                layout.Items.Add(forms.StackLayoutItem(sub_layout))
                groupbox = forms.GroupBox(Visible=False)
                groupbox.Padding = drawing.Padding(5)
                grouplayout = forms.StackLayout()
                self.add_items(item["items"], grouplayout, commands)
                groupbox.Content = grouplayout
                layout.Items.Add(groupbox)
               

                def on_click(groupbox):
                    def _on_click(sender, e):
                        if groupbox.Visible:
                            groupbox.Visible = False
                            sender.Text = "+"
                        else:
                            groupbox.Visible = True
                            sender.Text = "-"
                    return _on_click
                
                collapseButton.Click += on_click(groupbox)

            if "type" in item and item["type"] == "separator":
                layout.Items.Add(forms.Label(Text="_"*30))



if __name__ == "__main__":

    m = MenuForm()
    m.setup()
    m.Show()

    # m.show()
