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
              values = ["amzn-ami-hvm-*gp2"]
          }
      }

Usage:
    ami [--name <NAME>] [--type <TYPE>] [--details] [--latest]
    ami -h | --help

Options:
    -h --help       Show this screen
    --name <NAME>   Name of image [default: amzn-ami-hvm*].
    --type <TYPE>   Type of image, either gp2, ebs or s3 [default: gp2]
    --details       Show all details of the image, not just the AMI
    --latest        Show only the latest AMI
"""

from __future__ import print_function
from awstools import __VERSION__

import boto3
from docopt import docopt
import operator


def parse_commandline_arguments():
    return docopt(__doc__, version=__VERSION__)


def main():
    args = parse_commandline_arguments()

    client = boto3.client('ec2')

    response = client.describe_images(
        Owners=[
            'amazon',
        ],
        Filters=[
            {
                'Name': 'name',
                'Values': [
                    "{}{}".format(args['--name'], args['--type']),
                ]
            },
        ]
    )

    sorted_images = sorted(response["Images"], key=operator.itemgetter('CreationDate'))

    if args['--latest']:
        image = sorted_images[-1]
        if args['--details']:
            print("{} | {} | {} | {}".format(image['CreationDate'], image['ImageId'], image['Name'],
                                             image['Description']))
        else:
            print(image['ImageId'])
    else:
        count = 0
        for count, image in enumerate(sorted_images, start=1):
            if args['--details']:
                print("{} | {} | {} | {}".format(image['CreationDate'], image['ImageId'], image['Name'],
                                                 image['Description']))
            else:
                print(image['ImageId'])

        if args['--details']:
            print('Search finished, {} images found'.format(count))

if __name__ == "__main__":
    main()
