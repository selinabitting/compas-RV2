from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_rv2.datastructures import Skeleton
from compas_rv2.datastructures import Pattern
from compas_rv2.datastructures import FormDiagram
from compas_rv2.datastructures import ForceDiagram
from compas_rv2.datastructures import ThrustDiagram

from .skeletonartist import SkeletonArtist
from .meshartist import MeshArtist
from .formartist import FormArtist
from .forceartist import ForceArtist
from .thrustartist import ThrustArtist

MeshArtist.register(Skeleton, SkeletonArtist)
MeshArtist.register(Pattern, MeshArtist)
MeshArtist.register(FormDiagram, FormArtist)
MeshArtist.register(ForceDiagram, ForceArtist)
MeshArtist.register(ThrustDiagram, ThrustArtist)

__all__ = [name for name in dir() if not name.startswith('_')]
