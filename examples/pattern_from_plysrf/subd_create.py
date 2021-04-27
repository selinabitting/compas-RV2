from compas_rv2.datastructures import Subd
from compas.datastructures import Mesh
import compas_rhino
from compas_rhino.artists import MeshArtist

guid = compas_rhino.select_mesh()
rhinomesh = compas_rhino.geometry.RhinoMesh.from_guid(guid)
mesh = rhinomesh.to_compas()
# artist = MeshArtist(mesh)
# artist.draw_edgelabels()

subd = Subd.from_mesh(mesh)
subd.get_subd()
print(subd._strip_division)
subd.change_division((0,1), 10)
subd.get_subd()

artist = MeshArtist(subd.subd_mesh)
artist.draw_faces(join_faces=True)
# artist.draw_edgelabels()
