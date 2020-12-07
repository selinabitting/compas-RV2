from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys
import traceback

import Eto.Drawing as drawing
import Eto.Forms as forms
import Rhino.UI


__all__ = ["ErrorForm", "ErrorHandler"]


from functools import wraps


def ErrorHandler(title="Error", showLocalTraceback=True):
    def outer(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                if showLocalTraceback:
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    text = traceback.format_exception(exc_type, exc_value, exc_tb)
                    text = "".join(text)
                else:
                    text = str(error)
                ErrorForm(text, title=title)
        return wrapper
    return outer


class ErrorForm(forms.Dialog):

    def __init__(self, error="Unknown", title="Error", width=800, height=400):
        self.Title = title
        self.Padding = drawing.Padding(0)
        self.Resizable = False

        # tab_items = forms.StackLayoutItem(self.TabControl, True)
        layout = forms.StackLayout()
        layout.Spacing = 5
        layout.HorizontalContentAlignment = forms.HorizontalAlignment.Stretch

        self.m_textarea = forms.TextArea()
        self.m_textarea.Size = drawing.Size(400, 400)
        self.m_textarea.Text = error
        self.m_textarea.ReadOnly = True
        layout.Items.Add(self.m_textarea)

        sub_layout = forms.DynamicLayout()
        sub_layout.Spacing = drawing.Size(5, 0)
        sub_layout.AddRow(None, self.cancel)
        layout.Items.Add(forms.StackLayoutItem(sub_layout))

        self.Content = layout
        self.Padding = drawing.Padding(12)
        self.Resizable = True
        # self.ClientSize = drawing.Size(width, height)

        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    @property
    def cancel(self):
        self.AbortButton = forms.Button(Text='Close')
        self.AbortButton.Click += self.on_cancel
        return self.AbortButton

    def on_cancel(self, sender, event):
        self.Close()


if __name__ == "__main__":
    # error = ErrorForm("TEST")

    @ErrorHandler()
    def break_func():
        raise RuntimeError("some error message")

    break_func()
