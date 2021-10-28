from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import compas_rhino as Rhino
from copy import deepcopy
from compas_rhino.utilities import geometry
from compas_rhino.artists import MeshArtist
from compas.datastructures import Mesh
from compas.datastructures import meshes_join
from compas_rhino.geometry import RhinoSurface
from compas_rhino.objects import BaseObject
from compas_rhino.artists import MeshArtist
from compas_rhino import delete_objects


from compas.geometry import angle_vectors
from compas.geometry import distance_point_point
from compas.utilities import geometric_key

from compas.utilities import abstractclassmethod
from compas_rhino.geometry._geometry import BaseRhinoGeometry


__all__ = ['SurfaceObject']


def mesh_fast_copy(other):
    geometry = Mesh()
    geometry.vertex = deepcopy(other.vertex)
    geometry.face = deepcopy(other.face)
    geometry.facedata = deepcopy(other.facedata)
    geometry.halfedge = deepcopy(other.halfedge)
    geometry._max_face = other._max_face
    geometry._max_vertex = other._max_vertex
    return geometry



class SurfaceObject(BaseObject):
    """Scene object for surface(s) or polysurface(s) in RV2."""

    SETTINGS = {
        'layer': "RV2::SurftoMesh",
        'layer.subd': "RV2::SurftoMesh::subdivided",
        'layer.uv_mesh':  "RV2::SurftoMesh::uv_mesh",
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

    def __init__(self, uv_mesh=None, scene=None, name=None, layer=None, visible=True, settings=None):
        super(SurfaceObject, self).__init__(uv_mesh, scene, name, layer, visible)
        self._guids = []
        self._guid_vertex = {}
        self._guid_edge = {}
        self._guid_uv_mesh_edge = {}
        self._guid_uv_mesh_vertex = {}
        self._guid_subdivided = {}

        self.guid = None
        self.object = None
        self.geometry = None
        self._type = None
        self._name = None

        self.settings.update(type(self).SETTINGS)

        if settings:
            self.settings.update(settings)

    # ----------------------------------------------------------------------
    # properties
    # ----------------------------------------------------------------------

    @property
    def uv_mesh(self):
        return self.item

    @uv_mesh.setter
    def uv_mesh(self, uv_mesh):
        self.item = uv_mesh
        self._guids = []
        self._guid_uv_mesh_vertex = {}
        self._guid_uv_mesh_edge = {}

    @property
    def guid_uv_mesh_edge(self):
        return self._guid_uv_mesh_edge

    @guid_uv_mesh_edge.setter
    def guid_uv_mesh_edge(self, values):
        self._guid_uv_mesh_edge = dict(values)

    @property
    def geometry(self):
        return self._geometry

    @geometry.setter
    def geometry(self, geometry):
        self._geometry = geometry
        self._guid_geometry = {}
        self._guid_geometry_vertex = {}
        self._guid_geometry_edge = {}
        

    @property
    def guid_geometry_edge(self):
        return self._guid_geometry_edge

    @guid_geometry_edge.setter
    def guid_geometry_edge(self, values):
        self._guid_geometry_edge = dict(values)

    # ----------------------------------------------------------------------
    # selection of surface
    # ----------------------------------------------------------------------

    @classmethod
    def from_guid(cls, guid):

        """Construct a Rhino object wrapper from the GUID of an existing Rhino object.
        Parameters
        ----------
        guid : str
           The GUID of the Rhino object.
        Returns
        -------
        :class:`compas_rhino.geometry.BaseRhinoGeometry`
          The Rhino object wrapper.
        """

        rhinosurface = RhinoSurface.from_guid(guid)
        mesh = rhinosurface.to_compas(cleanup=False)
        surfaceobject = cls(mesh)
        surfaceobject.uv_mesh = mesh

        return surfaceobject

    @classmethod
    def from_selection(cls):
        guid = Rhino.select_surface()
        return cls.from_guid(guid)

    # ----------------------------------------------------------------------
    # modification
    # ----------------------------------------------------------------------

    def to_compas_mesh(self, nu, nv=None, weld=False, facefilter=None, cls=None):
        """Convert the surface to a COMPAS mesh.
        Parameters
        ----------
        nu: int
            The number of faces in the u direction.
        nv: int, optional
            The number of faces in the v direction.
            Default is the same as the u direction.
        weld: bool, optional
            Weld the vertices of the mesh.
            Default is ``False``.
        facefilter: callable, optional
            A filter for selection which Brep faces to include.
            If provided, the filter should return ``True`` or ``False`` per face.
            A very simple filter that includes all faces is ``def facefilter(face): return True``.
            Default parameter value is ``None`` in which case all faces are included.
        cls: :class:`compas.geometry.Mesh`, optional
            The type of COMPAS mesh.

        Returns
        -------
        :class:`compas.geometry.Mesh`
        """
        nv = nv or nu
        cls = cls or Mesh

        #print(self.type)
        print(self)
        print(self.geometry)
        #print(self.HasBrepForm)

        #if not self.uv_mesh.HasBrepForm:
        #    print ('Object is not a surface or Polysurface.')
        #    return
        #brep = Rhino.Geometry.Brep.TryConvertBrep(self.geometry)

        if facefilter and callable(facefilter):
            faces = [face for face in self.geometry.faces if facefilter(face)]
        else:
            faces = self.geometry.faces

        meshes = []
        for face in faces:
            domain_u = face.Domain(0)
            domain_v = face.Domain(1)
            du = (domain_u[1] - domain_u[0]) / (nu)
            dv = (domain_v[1] - domain_v[0]) / (nv)

            @memoize
            def point_at(i, j):
                return point_to_compas(face.PointAt(i, j))

            quads = []
            for i in range(nu):
                for j in range(nv):
                    a = point_at(domain_u[0] + (i + 0) * du, domain_v[0] + (j + 0) * dv)
                    b = point_at(domain_u[0] + (i + 1) * du, domain_v[0] + (j + 0) * dv)
                    c = point_at(domain_u[0] + (i + 1) * du, domain_v[0] + (j + 1) * dv)
                    d = point_at(domain_u[0] + (i + 0) * du, domain_v[0] + (j + 1) * dv)
                    quads.append([a, b, c, d])

            meshes.append(cls.from_polygons(quads))

        return meshes_join(meshes, cls=cls)

    def get_geometry(self):
        geometry = mesh_fast_copy(self.item)
        self.geometry = geometry

    def change_draw_subd(self):
        while True:
            guid = self.to_compas_mesh(nu=10)
            if not guid:
                break
            self.clear_geometry()
            self.get_geometry()
            self.draw_geometry()

    # ----------------------------------------------------------------------
    # visualize
    # ----------------------------------------------------------------------

    def draw_uv_mesh(self):
        self.artist.layer = self.settings['layer.uv_mesh']
        color = self.settings['color.edges']
        guids = self.artist.draw_edges(color=color)
        self.guid_uv_mesh_edge = zip(guids, list(self.item.edges()))
        self.artist.redraw()

    def draw_geometry(self):
        artist = MeshArtist(self.geometry)
        layer = self.settings['layer.subd']
        color = self.settings['color.subd.edges']
        #artist.layer = layer
        edges = [edge for edge in self.geometry.edges() if not self.geometry.is_edge_on_boundary(edge[0], edge[1])]
        guids = artist.draw_edges(color=color)
        self.guid_geometry_edge = zip(guids, list(self.item.edges()))
        artist.redraw()

    def clear_uv_mesh(self):
        guid_uv_mesh_edge = list(self.guid_uv_mesh_edge.keys())
        delete_objects(guid_uv_mesh_edge, purge=True)
        self._guid_uv_mesh_edge = {}

    def clear_geometry(self):
        guid_subd_edge = list(self.guid_subd_edge.keys())
        delete_objects(guid_subd_edge, purge=True)
        self._guid_subd_edge = {}

# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':
    pass
