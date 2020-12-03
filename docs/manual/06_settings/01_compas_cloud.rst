.. _compas_cloud:

********************************************************************************
compas_cloud
********************************************************************************

**compas_cloud** is an essential infrastructure component used by RV2.
It runs a background server for executing highly efficient numerical algorithms from CPython packges such as **numpy** and **scipy** that are not compatible with IronPython that runs inside Rhino.
This allows RV2 to utilise full capacity of other compas packages such as **compas_tna** and **compas_triangle** which has CPython dependencies.
compas_cloud server communicates with Rhino through websocket protocol, and can be controlled from RV2 menu:

.. figure:: /_images/compas_cloud.png
    :figclass: figure
    :class: figure-img img-fluid

* Cloud > Check: check if connection to compas_cloud server is healthy.

* Cloud > Restart: Restart compas_cloud server, with options of running in background or in a prompt console which is handy for debugging.

* Cloud > Shut Down: Shutdown the compas_cloud server.

