.. _pattern:

********************************************************************************
1. Pattern
********************************************************************************

.. figure:: /_images/rv2_workflow_01.jpg
    :figclass: figure
    :class: figure-img img-fluid

A pattern is a network of lines that define the topology of the form diagram. The ``Pattern`` in RV2 which is a ``mesh`` representation of this pattern, can be generated using a variety of inputs and methods.

----

1. Pattern from lines
=====================

.. figure:: /_images/icon_from-lines.jpg
   :width: 100 px
   :alt: Left floating image
   :align: left

From a collection of connected Rhino line objects. Each segment needs to be an indepedent, ungrouped line object. Polylines are not viable inputs.

.. rst-class:: clear-both

|

----

2. Pattern from mesh
====================

.. figure:: /_images/icon_from-mesh.jpg
   :width: 100 px
   :alt: alternate text
   :align: left

From a Rhino mesh object, where the edges of the mesh are converted to the edges of the ``Pattern``.

.. rst-class:: clear-both

|

----

3. Pattern from surface
=======================

From an untrimmed Rhino NURBS surface, where the UV mapping is used to generate a quad-mesh.

|

----

4. Pattern from Skeleton
========================

From a ``Skeleton``, a network of lines representing the "spine" of the ``Pattern``. Based on the `compas_skeleton <https://github.com/BlockResearchGroup/compas_skeleton>`_  package, ``Skeleton`` provides features that enable generation and modification of complex patterns easy, fast and interactive. ``From Skeleton`` function comes with built-in smoothing, subdivision, merge and various manipulation features.

``Skeleton`` works with quad-meshes only.

|

----

5. Pattern from Triangulation
=============================

From a set of boundary features (boundary edges, openings and guide curves), a tri-mesh is generated using Delaunay triangulation. The triangulation and various meshing features are based on the `compas_triangle <https://github.com/BlockResearchGroup/compas_triangle>`_  package.

This feature is currently under construction.

|

----

6. Pattern from Features
========================

From a set of boundary features (boundary edges, openings, guide curves and singularities), a quad-mesh is generated using features of the `compas_pattern <https://github.com/BlockResearchGroup/compas_triangle>`_  package.

This feature is currently under construction.



