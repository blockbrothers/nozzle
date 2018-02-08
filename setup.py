#!/usr/bin/env python3

from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 5):
    sys.exit('Only Python >=3.5 supported.')


setup(
    name='steem-nozzle',
    version='0.1.0',
    description='A Python library for the Steem Blockchain',
    long_description='',
    url='https://github.com/blockbrothers/nozzle',
    author='blockbrothers',
    author_email='info@blockbrothers.io',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='steem blockchain',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3.5',
    install_requires=['urllib3', 'certifi'],
    extras_require={},
    package_data={},
    entry_points={},
)
