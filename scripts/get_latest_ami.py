#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) CloudZero, Inc. All rights reserved.
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

"""
Simple utility to get the latest AMI for a given image name, by default the Amazon Linux AMI

Note: If you are using Hashicorp Terraform (> v0.7.7), don't run this script, just use this in your tf configuration

      data "aws_ami" "linux_ami" {
          most_recent = true
          filter {
              name = "owner-alias"
              values = ["amazon"]
          }
          filter {
              name = "name"
              values = ["amzn-ami-hvm-*"]
          }
      }

Usage:
    get_latest_ami.py [--name <NAME>] [--details]
    get_latest_ami.py -h | --help

Options:
    -h --help       Show this screen
    --name <NAME>   Name of image [default: amzn-ami-hvm*].
    --details       Show all details of the image, not just the AMI
"""

from __future__ import print_function
import boto3
from docopt import docopt
from pprint import pprint
import operator

__VERSION__ = "0.1"


def parse_commandline_arguments():
    return docopt(__doc__, version=__VERSION__)


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

    sorted_images = sorted(response["Images"], key=operator.itemgetter('CreationDate'))

    count = 0
    for count, image in enumerate(sorted_images, start=1):
        print("{} | {} | {}".format(image['CreationDate'], image['ImageId'], image['Description']))
        if args['--details']:
            pprint(image)
            print("-" * 80)

    print('Search finished, {} images found'.format(count))


if __name__ == "__main__":
    docopt_args = parse_commandline_arguments()
    main(docopt_args)
