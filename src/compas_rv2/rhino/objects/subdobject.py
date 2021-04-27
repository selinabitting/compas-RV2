from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_rhino.objects import BaseObject
import rhinoscriptsyntax as rs


__all__ = ['SubdObject']


class SubdObject(BaseObject):
    """Scene object for Subd in Rhino."""

    SETTINGS = {
        'layer': "RV2::Subd",
        'layer.coarse': "RV2::Subd::coarse",
        'layer.subd': "RV2::Subd::subd",
        'color.vertices': (255, 255, 255),
        'color.edges': (0, 0, 0),
        'color.faces': (0, 0, 0),
        'color.mesh': (0, 0, 0),
        'color.subd.edges': (120, 120, 120),
        'show.mesh': True,
        'show.vertices': True,
        'show.edges': True,
        'show.faces': False,
    }

    def __init__(self, subd=None, scene=None, name=None, layer=None, visible=True, settings=None):
        super(SubdObject, self).__init__(subd, scene, name, layer, visible)
        self._guids = []
        self._guid_coarse_vertex = {}
        self._guid_coarse_edge = {}
        self._guid_subd_edge = {}
        self._guid_label = {}
        self._guid_subd = {}
        self._edge_strips = {}
        self._strip_division = {}
        self._guid_strip_division = {}
        self._anchor = None
        self._location = None
        self._scale = None
        self._rotation = None
        self.settings.update(type(self).SETTINGS)
        if settings:
            self.settings.update(settings)

    # ----------------------------------------------------------------------
    # properties
    # ----------------------------------------------------------------------

    @property
    def coarse(self):
        return self.item

    @coarse.setter
    def coarse(self, coarse):
        self.item = coarse
        self._guids = []
        self._guid_coarse_vertex = {}
        self._guid_coarse_edge = {}
        self._guid_label = {}

    # ----------------------------------------------------------------------
    # constructors
    # ----------------------------------------------------------------------
