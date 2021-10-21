from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import compas_rhino as Rhino

from compas_rhino.artists import MeshArtist
from compas.datastructures import Mesh
from compas.datastructures import meshes_join
from compas_rhino.geometry import RhinoSurface
from compas_rhino.objects import BaseObject
from compas_rhino.artists import MeshArtist

from compas.geometry import angle_vectors
from compas.geometry import distance_point_point
from compas.utilities import geometric_key

from compas.utilities import abstractclassmethod
from compas_rhino.geometry._geometry import BaseRhinoGeometry


__all__ = ['SurfaceObject']


class SurfaceObject(BaseRhinoGeometry):
    """Scene object for surface(s) or polysurface(s) in RV2.""" 

    SETTINGS = {
        'layer': "RV2::SurftoMesh",
        'layer.subd': "RV2::SurftoMesh::subdivided",
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

    def __init__(self, scene=None, name=None, layer=None, visible=True, settings=None):
        super(SurfaceObject, self).__init__(scene, name, layer, visible)
        self._subd = None
        self._guids = []
        self._guid_vertex = {}
        self._guid_edge = {}
        self._guid_subd_edge = {}
        self._guid_label = {}
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
    def type(self):
        if self.object:
            return self.object.ObjectType
        else:
            return self._type

    @type.setter
    def type(self, surface):
        self._type = surface

    @property
    def name(self):
        if self.object:
            return self.object.Attributes.Name
        else:
            return self._name
    
    @name.setter
    def name(self, value):
        if self.object:
            self.object.Attributes.Name = value
            self.object.CommitChanges()
        else:
            self._name = value


    # ----------------------------------------------------------------------
    # selection of surface
    # ----------------------------------------------------------------------

    @classmethod
    def from_guid(cls, guid=None):

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
        if guid and callable(guid):
            surface = Rhino.select_surface(guid)
        else:
            surface = Rhino.find_object(guid)

        rhinosurface = RhinoSurface.from_guid(surface)

        wrapper = cls()
        wrapper.guid = rhinosurface.Id
        wrapper.object = rhinosurface
        wrapper.geometry = rhinosurface.Geometry
        return wrapper
    
    @classmethod
    def from_selection(cls):
        guid = Rhino.select_surface()
        return cls.from_guid(guid)

    # ----------------------------------------------------------------------
    # modification
    # ----------------------------------------------------------------------
    def surface_type(self, density=(5,5)):
        """Checks if selection is surface or polysurface. 
        If polysurface explodes to surfaces

        Parameters
        ----------
        density : tuple, optional
            The density in the U and V directions of the parameter space.
            Default is ``10`` in both directions.
        Returns
        -------
        list
            A list of surfaces.
        """
        rs = Rhino.rs

        if rs.IsPolysurface(self.guid):
            faces = rs.ExplodePolysurfaces(self.guid)
        elif rs.IsSurface(self.guid):
            faces = [self.guid]
        else:
            raise Exception('Object is not a surface.')


    def space(self, density=(10, 10)):

        """Construct a parameter grid over the UV space of the surface.
        Parameters
        ----------
        density : tuple, optional
            The density in the U and V directions of the parameter space.
            Default is ``10`` in both directions.
        Returns
        -------
        list
            A list of UV parameter tuples.
        """
        
        rs = Rhino.rs
        rs.EnableRedraw(False)
        try:
            du, dv = density
        except TypeError:
            du = density
            dv = density
        density_u = int(du)
        density_v = int(dv)
        if rs.IsPolysurface(self.guid):
            faces = rs.ExplodePolysurfaces(self.guid)
        elif rs.IsSurface(self.guid):
            faces = [self.guid]
        else:
            raise Exception('Object is not a surface.')
        uv = []
        for face in faces:
            domain_u = rs.SurfaceDomain(face, 0)
            domain_v = rs.SurfaceDomain(face, 1)
            du = (domain_u[1] - domain_u[0]) / (density_u - 1)
            dv = (domain_v[1] - domain_v[0]) / (density_v - 1)
            # move to meshgrid function
            for i in range(density_u):
                for j in range(density_v):
                    uv.append((domain_u[0] + i * du, domain_v[0] + j * dv))
        if len(faces) > 1:
            rs.DeleteObjects(faces)
        rs.EnableRedraw(True)
        return uv


    def curvature(self, points=None):
        """"""
        rs = Rhino.rs
        if not points:
            points = self.heightfield()
        curvature = []
        if rs.IsPolysurface(self.guid):
            rs.EnableRedraw(False)
            faces = {}
            for point in points:
                bcp = rs.BrepClosestPoint(self.guid, point)
                uv = bcp[1]
                index = bcp[2][1]
                try:
                    face = faces[index]
                except (TypeError, IndexError):
                    face = rs.ExtractSurface(self.guid, index, True)
                    faces[index] = face
                props = rs.SurfaceCurvature(face, uv)
                curvature.append((point, (props[1], props[3], props[5])))
            rs.DeleteObjects(faces.values())
            rs.EnableRedraw(False)
        elif rs.IsSurface(self.guid):
            for point in points:
                bcp = rs.BrepClosestPoint(self.guid, point)
                uv = bcp[1]
                props = rs.SurfaceCurvature(self.guid, uv)
                curvature.append((point, (props[1], props[3], props[5])))
        else:
            raise Exception('Object is not a surface.')
        return curvature


    def borders(self, border_type=1):

        """Duplicate the borders of the surface.
        Parameters
        ----------
        border_type : {0, 1, 2}
            The type of border.
            * 0: All borders
            * 1: The exterior borders.
            * 2: The interior borders.
        Returns
        -------
        list
            The GUIDs of the extracted border curves.
        """

        rs = Rhino.rs
        border = rs.DuplicateSurfaceBorder(self.guid, type=border_type)
        curves = rs.ExplodeCurves(border, delete_input=True)
        return curves


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

        if not self.geometry.HasBrepForm:
            print ('Object is not a surface or Polysurface.')
            return

        brep = Rhino.Geometry.Brep.TryConvertBrep(self.geometry)

        if facefilter and callable(facefilter):
            faces = [face for face in brep.Faces if facefilter(face)]
        else:
            faces = brep.Faces

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



    # ----------------------------------------------------------------------
    # visualize
    # ----------------------------------------------------------------------

    def draw(self):
            artist = MeshArtist(self.subd)
            layer = self.settings['layer.subd']
            color = self.settings['color.subd.edges']
            artist.layer = layer
            edges = [edge for edge in self.subd.edges() if not self.subd.is_edge_on_boundary(edge[0], edge[1])]
            guids = artist.draw_edges(edges, color=color)
            self.guid_subd_edge = zip(guids, edges)
            artist.redraw()
    


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':
    pass
