conda env remove -n rv2
conda create -n rv2 python=3.7 conda-pack cython -y
conda activate rv2
pip install compas==0.15.6
pip install git+https://github.com/compas-dev/compas.git#egg=compas
pip install git+https://github.com/BlockResearchGroup/compas_cloud.git#egg=compas_cloud
pip install git+https://github.com/BlockResearchGroup/compas_tna.git#egg=compas_tna
pip install git+https://github.com/BlockResearchGroup/compas_skeleton.git#egg=compas_skeleton
pip install git+https://github.com/BlockResearchGroup/compas_triangle.git#egg=compas_triangle
pip install git+https://github.com/BlockResearchGroup/compas_singular.git#egg=compas_singular
pip install .
python scripts/pack.py
