from compas_rv2.datastructures import Skeleton
from compas_rv2.rhino import SkeletonObject
from compas_rv2.rhino import SkeletonArtist
import compas_rhino

guids = compas_rhino.select_lines()
lines = compas_rhino.get_line_coordinates(guids)

skeleton = Skeleton.from_skeleton_lines(lines)
skeleton.update_mesh_vertices_pos()
skeletonobject = SkeletonObject(skeleton)

skeletonobject.draw()
skeletonobject.dynamic_draw_widths()

skeletonobject.move_skeleton_vertex()
skeletonobject.draw()
# skeletonobject.draw_mesh_vertices()
# skeletonobject.move_mesh_vertex()

# artist = SkeletonArtist(skeleton)
# artist.draw_skeleton_vertices()
# artist.draw_skeleton_edges()
# artist.draw_mesh_vertices()
# artist.draw_subd()
# print(skeletonobject)
# print(skeletonobject.artist)
