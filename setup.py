#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) CloudZero, Inc. All rights reserved.
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

from setuptools import setup, find_packages
from awstools import __VERSION__

setup(name='awstools',
      version=__VERSION__,
      description='A collection of aws tools for basic or everyday AWS operations to make life easier ',
      author='Erik Peterson',
      author_email='erik@cloudzero.com',
      url='https://github.com/Cloudzero/aws-tools',
      packages=find_packages(),
      entry_points={
          'console_scripts': ['glacier=awstools.glacier:main',
                              'ami=awstools.ami:main']
      },
      install_requires=['boto3>=1.4.1', 'docopt>=0.6.2'],
      keywords="aws glacier.py.py cloudzero",
      classifiers=[
          "Programming Language :: Python :: 3",
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Environment :: Console",
          "Operating System :: MacOS :: MacOS X",
          "License :: OSI Approved :: MIT License"]
      )
