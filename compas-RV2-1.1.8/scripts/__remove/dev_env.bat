REM create a conda dev environment for compas_rv2
conda env remove -n rv2-dev
conda create -n rv2-dev python=3.7 conda-pack cython -y
conda activate rv2-dev
pip install compas==0.15.6
pip install git+https://github.com/BlockResearchGroup/compas_cloud.git#egg=compas_cloud
pip install git+https://github.com/BlockResearchGroup/compas_tna.git#egg=compas_tna
pip install git+https://github.com/BlockResearchGroup/compas_skeleton.git#egg=compas_skeleton
pip install git+https://github.com/BlockResearchGroup/compas_triangle.git#egg=compas_triangle
pip install -e .
python -m compas_rv2.install --dev