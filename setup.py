import os
from setuptools import setup, find_packages

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name='hgc',
    version='0.2.3',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='A python package for correction, validation and analysis of ground water quality samples',
    long_description=read('README.rst'),
    long_description_content_type="text/x-rst",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Hydrology',
    ],
    python_requires='>=3.6',
    project_urls={
    'Source': 'https://github.com/KWR-Water/hgc',
    'Documentation': 'http://hgc.readthedocs.io/en/latest/',
    'Tracker': 'https://github.com/KWR-Water/hgc/issues',
    'Help': 'https://stackoverflow.com/questions/tagged/hgc'
    },
    install_requires=[
        'pandas>=0.23',
        'openpyxl>=3.0.0',
        'cloudpickle==1.2.2',
        'xlrd>=1.0.0',
        'phreeqpython>=1.3.2',  # TODO: possibly this can be made an optional dependency but we need to figure out how to do this properly
        'scipy', # TODO: temporarily require SciPy. This is actually a dep of phreeqpython, which however, doesn't correctly require it
        # 'fuzzywuzzy>=1.0',
        'googletrans',
        'pubchempy',
        'molmass',

        ],
    include_package_data=True,
    url='https://github.com/KWR-Water/hgc',
    author='KWR Water Research Institute',
    author_email='martin.korevaar@kwrwater.nl, martin.van.der.schans@kwrwater.nl, erwin.vonk@kwrwater.nl',
)
