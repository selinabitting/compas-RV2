from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.datastructures import Mesh

from compas_rv2.datastructures import Skeleton
from compas_rv2.datastructures import SubdMesh
from compas_rv2.datastructures import Pattern
from compas_rv2.datastructures import FormDiagram
from compas_rv2.datastructures import ForceDiagram
from compas_rv2.datastructures import ThrustDiagram

from .meshartist import MeshArtist
from .skeletonartist import SkeletonArtist
from .formartist import FormArtist
from .forceartist import ForceArtist
from .thrustartist import ThrustArtist

MeshArtist.register(Mesh, MeshArtist, context='Rhino')
MeshArtist.register(Skeleton, SkeletonArtist, context='Rhino')
MeshArtist.register(SubdMesh, MeshArtist, context='Rhino')
MeshArtist.register(Pattern, MeshArtist, context='Rhino')
MeshArtist.register(FormDiagram, FormArtist, context='Rhino')
MeshArtist.register(ForceDiagram, ForceArtist, context='Rhino')
MeshArtist.register(ThrustDiagram, ThrustArtist, context='Rhino')
