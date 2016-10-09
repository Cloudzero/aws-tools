#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) CloudZero, Inc. All rights reserved.
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

"""
Simple utility to get the latest AMI for a given image name, by default the Amazon Linux AMI

Usage:
    get_latest_ami.py [--name <NAME>] [--details]
    get_latest_ami.py -h | --help

Options:
    -h --help       Show this screen
    --name <NAME>   Name of image [default: customer_64bit_img].
    --details       Show all details of the image, not just the AMI
"""

from __future__ import print_function
import boto3
from docopt import docopt
from pprint import pprint


def parse_commandline_arguments():
    return docopt(__doc__, version='Get Latest AMI')


def main(args):
    client = boto3.client('ec2')

    response = client.describe_images(
        Owners=[
            'amazon',
        ],
        Filters=[
            {
                'Name': 'name',
                'Values': [
                    args['--name'],
                ]
            },
        ]
    )

    count = 0
    for count, image in enumerate(response["Images"], start=1):
        if args['--details']:
            pprint(image)
        else:
            print(image['ImageId'])

    print('Search finished, {} images found'.format(count))


if __name__ == "__main__":
    docopt_args = parse_commandline_arguments()
    main(docopt_args)
