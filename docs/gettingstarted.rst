********************************************************************************
Getting Started
********************************************************************************

Beta Release install (Windows Only)
===================================

1. Get the latest release from: https://github.com/BlockResearchGroup/compas-RV2/releases

    .. figure:: /_images/install_1_download.png
        :figclass: figure
        :class: figure-img img-fluid


2. Unzip downloaded folder

    .. figure:: /_images/install_2_extract.png
        :figclass: figure
        :class: figure-img img-fluid


3. open unzipped folder and go to its sub-folder: `RV2/dev/`, right click on `install.bat` (.bat extension might be hidden) and choose `Run as Administrator`

    .. figure:: /_images/install_3_run.png
        :figclass: figure
        :class: figure-img img-fluid


4. If the installation is successful, you should be able to see following logs:

    .. figure:: /_images/install_4_done.png
            :figclass: figure
            :class: figure-img img-fluid


5. Activate RV2 toolbar in Rhino

   * Go to menu `Tools > Toolbar Layout...`.

    .. figure:: /_images/install_5_toolbar.png
            :figclass: figure
            :class: figure-img img-fluid

   * In pop-up window, click `File > Open...`.

   .. figure:: /_images/install_6_open.png
            :figclass: figure
            :class: figure-img img-fluid

   * Then in file explorer, select `YOUR_RV2_FOLDER\dev\RV2.rui`.

   .. figure:: /_images/install_7_rui.png
            :figclass: figure
            :class: figure-img img-fluid
    
   * Now you will see RhinoVAULT2 appears in rhino menu.

    .. figure:: /_images/install_8_done.png
            :figclass: figure
            :class: figure-img img-fluid


Known Issues
============

Following error might appear for fresh Rhino installations:

.. code-block:: none

        FileNotFoundError: [WinError 3] The system cannot find the path specified:
            'C:\Users\xxx\AppData\Roaming\McNeel\Rhinoceros\6.0\Plug-ins\PythonPlugins'

To fix this, run `EditPythonScript` once and restart Rhino.
