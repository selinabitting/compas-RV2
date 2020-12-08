"""
********************************************************************************
compas_rv2.datastructures
********************************************************************************

.. currentmodule:: compas_rv2.datastructures

Patterns
========

.. autosummary::
    :toctree: generated/
    :nosignatures:

    Skeleton
    Pattern


Diagrams
========

.. autosummary::
    :toctree: generated/
    :nosignatures:

    FormDiagram
    ForceDiagram
    ThrustDiagram

"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from .meshmixin import MeshMixin  # noqa: F401
from .skeleton import Skeleton  # noqa: F401
from .pattern import Pattern  # noqa: F401
from .formdiagram import FormDiagram  # noqa: F401
from .forcediagram import ForceDiagram  # noqa: F401
from .thrustdiagram import ThrustDiagram  # noqa: F401


__all__ = [name for name in dir() if not name.startswith('_')]
