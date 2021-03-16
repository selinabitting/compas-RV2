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


__all__ = ["MenuForm"]

HERE = os.path.dirname(__file__)
UI_FOLDER = os.path.join(HERE, "..", "..", "ui/Rhino/RV2/dev")

class MenuForm(forms.Dialog[bool]):

    def setup(self):

        self.Title = "RhinoVault2"
        layout = forms.StackLayout()
        layout.Spacing = 5
        layout.HorizontalContentAlignment = forms.HorizontalAlignment.Stretch
        # layout.Items.Add(tab_items)
        self.load_config(layout)
        self.Width = 300
        self.Height = 900

        self.Content = forms.Scrollable()
        self.Content.Content = layout
        self.Padding = drawing.Padding(12)
        self.Resizable = True

    def load_config(self, layout):
        config = json.load(open(os.path.join(UI_FOLDER, "config.json")))
        menu = config["ui"]["menus"][0]
        self.add_items(menu["items"], layout)

    def add_items(self, items, layout):
        for item in items:
            if "command" in item:
                layout.Items.Add(forms.Button(Text=item["command"]))
            if "items" in item:
                groupbox = forms.GroupBox(Text=item["name"])
                groupbox.Padding = drawing.Padding(5)
                grouplayout = forms.StackLayout()
                self.add_items(item["items"], grouplayout)
                groupbox.Content = grouplayout
                layout.Items.Add(groupbox)
                
            if "type" in item and item["type"] == "separator":
                layout.Items.Add(forms.Label(Text="-"*20))

    def show(self):
        Rhino.UI.EtoExtensions.ShowSemiModal(self, Rhino.RhinoDoc.ActiveDoc, Rhino.UI.RhinoEtoApp.MainWindow)



if __name__ == "__main__":

    m = MenuForm()
    m.setup()
    m.show()
