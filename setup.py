import os
from setuptools import setup, find_packages

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name='hgc',
    version='0.1',
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
    project_urls={
    'Source': 'https://github.com/KWR-Water/hgc',
    'Documentation': 'http://hgc.readthedocs.io/en/latest/',
    'Tracker': 'https://github.com/KWR-Water/hgc/issues',
    'Help': 'https://stackoverflow.com/questions/tagged/hgc'
    },
    install_requires=['pandas>=0.23'],
    url='https://github.com/KWR-Water/hgc',
    author='KWR Water Research Institute',
    author_email='martin.korevaar@kwrwater.nl, martin.van.der.schans@kwrwater.nl, erwin.vonk@kwrwater.nl'
)
