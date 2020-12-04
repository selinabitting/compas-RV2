from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino
from compas_rhino.geometry import RhinoSurface
from compas_rv2.datastructures import Pattern
from compas_rv2.rhino import PatternObject
from compas_rv2.rhino import get_scene
from compas_rv2.rhino import rv2_undo


__commandname__ = "RV2pattern_from_surface"



class RhinoSurface(RhinoSurface):

    def uv_to_compas(self, cls=None, density=(10, 10)):
        """Convert the surface UV space to a COMPAS mesh.

        Parameters
        ----------
        cls : :class:`compas.datastructures.Mesh`, optional
            The type of mesh.
        density : tuple of int, optional
            The density in the U and V directions.
            Default is ``u = 10`` and ``v = 10``.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The COMPAS mesh.
        """
        return self.heightfield_to_compas(cls=cls, density=density, over_space=True)

    def heightfield_to_compas(self, cls=None, density=(10, 10), over_space=False):
        """Convert a heightfiled of the surface to a COMPAS mesh.

        Parameters
        ----------
        cls : :class:`compas.datastructures.Mesh`, optional
            The type of mesh.
        density : tuple of int, optional
            The density in the two grid directions.
            Default is ``u = 10`` and ``v = 10``.
        over_space : bool, optional
            Construct teh grid over the surface UV space instead of the XY axes.
            Default is ``False``.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The COMPAS mesh.
        """
        try:
            u, v = density
        except Exception:
            u, v = density, density
        vertices = self.heightfield(density=(u, v), over_space=over_space)
        faces = []
        for i in range(u - 1):
            for j in range(v - 1):
                face = [(i + 0) * v + j,
                        (i + 1) * v + j,
                        (i + 1) * v + j + 1,
                        (i + 0) * v + j + 1]
                faces.append(face)
        cls = cls or Mesh
        return cls.from_vertices_and_faces(vertices, faces)


@rv2_undo
def RunCommand(is_interactive):

    scene = get_scene()
    if not scene:
        return

    guid = compas_rhino.select_surface()
    if not guid:
        return

    u = PatternObject.SETTINGS['from_surface.density.U']
    v = PatternObject.SETTINGS['from_surface.density.V']

    options = ['U', 'V']
    while True:
        option = compas_rhino.rs.GetString("Enter values for U and V:", strings=options)

        if not option:
            break

        if option == 'U':
            u = compas_rhino.rs.GetInteger("Density U", u, 2, 100)
            continue
        if option == 'V':
            v = compas_rhino.rs.GetInteger("Density V", v, 2, 100)
            continue

    density = u + 1, v + 1
    pattern = RhinoSurface.from_guid(guid).uv_to_compas(cls=Pattern, density=density)

    compas_rhino.rs.HideObject(guid)

    scene.clear()
    scene.add(pattern, name='pattern')
    scene.update()

    print("Pattern object successfully created. Input surface has been hidden.")


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    RunCommand(True)
