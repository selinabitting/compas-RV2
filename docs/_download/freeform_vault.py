from compas_rv2.skeleton import Skeleton
from compas_rv2.diagrams import FormDiagram  # noqa F401
from compas_rv2.diagrams import ForceDiagram
from compas_rv2.diagrams import ThrustDiagram  # noqa F401
from compas_rv2.rhino import RhinoSkeleton
from compas_rv2.rhino import RhinoFormDiagram
from compas_rv2.rhino import RhinoForceDiagram
from compas_rv2.rhino import RhinoThrustDiagram

from compas.geometry import subtract_vectors
from compas.geometry import scale_vector
from compas.geometry import Translation

from compas_cloud import Proxy
import compas_rhino
import rhinoscriptsyntax as rs
import time

# --------------------------------------------------------------------------
# settings for visulisation in Rhino
# --------------------------------------------------------------------------
settings = {
    "layers.skeleton": "RV2::Skeleton",
    "layers.form": "RV2::FormDiagram",
    "layers.force": "RV2::ForceDiagram",
    "layers.thrust": "RV2::ThrustNetwork",

    "color.form.vertices": (0, 255, 0),
    "color.form.vertices:is_fixed": (0, 255, 255),
    "color.form.vertices:is_external": (0, 0, 255),
    "color.form.vertices:is_anchor": (255, 255, 255),

    "color.form.edges": (0, 255, 0),
    "color.form.edges:is_external": (0, 0, 255),

    "color.thrust.vertices": (255, 0, 255),
    "color.thrust.vertices:is_fixed": (0, 255, 0),
    "color.thrust.vertices:is_anchor": (255, 0, 0),

    "color.thrust.edges": (255, 0, 255),
    "color.thrust.faces": (255, 0, 255),

    "color.force.vertices": (0, 255, 0),
    "color.force.vertices:is_fixed": (0, 255, 255),

    "color.force.edges": (0, 255, 0),
    "color.force.edges:is_external": (0, 0, 255),

}

# --------------------------------------------------------------------------
# create a Rhinoskeleton
# --------------------------------------------------------------------------

guids = rs.GetObjects("select curves", filter=rs.filter.curve)
lines = compas_rhino.get_line_coordinates(guids)
rs.DeleteObjects(guids)

skeleton = Skeleton.from_skeleton_lines(lines)
rhinoskeleton = RhinoSkeleton(skeleton)

rhinoskeleton.draw_skeleton_branches()
rhinoskeleton.dynamic_draw_self()

# --------------------------------------------------------------------------
# modify skeleton
# --------------------------------------------------------------------------

rhinoskeleton.move_skeleton_vertex()
rhinoskeleton.draw_self()

rhinoskeleton.move_diagram_vertex()
rhinoskeleton.draw_self()

rhinoskeleton.diagram.subdivide()
rhinoskeleton.draw_self()

# --------------------------------------------------------------------------
# create form diagram, update form boundaries
# --------------------------------------------------------------------------


def move_diagram(diagram, distance=1.5):
    bbox = diagram.bounding_box()

    a = bbox[0]
    b = bbox[1]
    ab = subtract_vectors(b, a)
    ab = scale_vector(ab, distance)

    T = Translation(ab)
    diagram.transform(T)

    return diagram


time.sleep(1)
form = rhinoskeleton.diagram.to_form()
form.update_boundaries(feet=2)

form = move_diagram(form)
rhinoform = RhinoFormDiagram(form)
rhinoform.draw(settings)

# --------------------------------------------------------------------------
# create force diagram
# --------------------------------------------------------------------------

time.sleep(1)
force = ForceDiagram.from_formdiagram(form)
force = move_diagram(force)

rhinoforce = RhinoForceDiagram(force)
rhinoforce.draw(settings)

# --------------------------------------------------------------------------
# horizontal equilibrium
# --------------------------------------------------------------------------
time.sleep(1)
proxy = Proxy()
horizontal = proxy.package("compas_rv2.equilibrium.horizontal_nodal_proxy")
formdata, forcedata = horizontal(rhinoform.diagram.data, rhinoforce.diagram.data)

rhinoform.diagram.data = formdata
rhinoforce.diagram.data = forcedata
rhinoform.draw(settings)
rhinoforce.draw(settings)

# --------------------------------------------------------------------------
# vertical equilibrium, draw thrustnetwork
# --------------------------------------------------------------------------
time.sleep(1)
vertical = proxy.package("compas_tna.equilibrium.vertical_from_zmax_proxy")

rhinothrust = RhinoThrustDiagram(form)
zmax = 4

formdata, scale = vertical(rhinoform.diagram.data, zmax)
rhinoforce.diagram.attributes['scale'] = scale
rhinoform.diagram.data = formdata
rhinothrust.diagram.data = formdata
rhinothrust.draw(settings)
