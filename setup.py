#!/usr/bin/env python3

import pathlib
from distutils.core import setup
from pkg_resources import parse_requirements

def get_requirements(requirements_filename: str):
    with pathlib.Path(requirements_filename).open() as requirements_txt:
        return [str(requirement) for requirement in parse_requirements(requirements_txt)]

setup(
    name='Obfuscapk',
    version='1.0.0',
    description='An automatic obfuscation tool for Android apps that works in a black-box fashion, supports advanced obfuscation features and has a modular architecture easily extensible with new techniques',
    author='ClaudiuGeorgiu',
    url='https://github.com/ClaudiuGeorgiu/Obfuscapk',
    packages=['obfuscapk'],
    package_dir={'obfuscapk': 'src/obfuscapk'},
    package_data={'obfuscapk': ['obfuscators/**', 'resources/**', '../requirements.txt']},
    include_package_data=True,
    install_requires=get_requirements('src/requirements.txt')
)
