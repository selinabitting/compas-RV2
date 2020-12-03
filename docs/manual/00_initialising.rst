.. _initialising:

********************************************************************************
0. Initialising
********************************************************************************

.. figure:: /_images/rv2_workflow_00.jpg
    :figclass: figure
    :class: figure-img img-fluid

Initialising RV2 command is required to run at the beginning of all RV2 sessions.

|

----

.. figure:: /_images/rv2_init.png
    :figclass: figure
    :class: figure-img img-fluid

The initialisation does several necessary jobs:

* Bring up a front-page providing useful links about RV2 and require users to accept RV2's Terms and Agreements to proceed.

* Initialize data structures and user session needed for RV2 to operate in Rhino environment.

* Kick off **compas_cloud** server in background and establish connection to it from Rhino.