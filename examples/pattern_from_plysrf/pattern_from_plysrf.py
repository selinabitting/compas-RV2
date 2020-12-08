from compas_rv2.rhino import SubdObject
import compas_rhino

guid = compas_rhino.select_surface()
subdobject = SubdObject.from_guid(guid)
compas_rhino.rs.HideObject(guid)

subdobject.draw_coarse()
subdobject.get_draw_default_subd()
subdobject.draw_subd()

subdobject.change_draw_subd()
