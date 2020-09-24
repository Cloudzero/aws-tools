#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) CloudZero, Inc. All rights reserved.
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

"""
Simple utility for manipulating CloudWatch

Usage:
    cloudwatch expire [--days <days> --filter <filter> --profile <profile>]
    cloudwatch list [--limit <limit> --profile <profile>]
    cloudwatch -h | --help

Options:
    expire                  Expire all log groups
    list                    List all log groups

    -p --profile <profile>  AWS Credentials profile to use [default: default].
    --days <days>           Expire limit in days [default: 120]
    --limit <limit>         Number of records to list
    --filter <filter>       Filter results
    -h --help               Show this screen.

"""

from __future__ import print_function
from awstools import __VERSION__

import json
from datetime import datetime, timezone, timedelta
import dateutil.parser
from docopt import docopt
import boto3

__TAG_PREFACE__ = "CLOUDZERO_CLOUDWATCH_TOOLS"


def main():
    args = parse_commandline_arguments()

    session = boto3.session.Session(profile_name=args['--profile'])
    client = session.client('logs')

    print(args)

    if args['list']:
        limit = min(int(args.get('--limit', 0)), 50)
        response = client.describe_log_groups(limit=limit)
        for loggroup in response['logGroups']:
            print(loggroup['logGroupName'])
    elif args['expire']:
        count = 0
        filter = args.get('--filter') or ''
        response = client.describe_log_groups()
        while response.get('nextToken'):
            for loggroup in response['logGroups']:
                if filter in loggroup['logGroupName']:
                    # dict_keys(['logGroupName', 'creationTime', 'metricFilterCount', 'arn', 'storedBytes'])
                    print(loggroup['logGroupName'], loggroup['storedBytes'])
                    client.put_retention_policy(
                        logGroupName=loggroup['logGroupName'],
                        retentionInDays=int(args.get('--days'))
                    )
                    count += 1
            response = client.describe_log_groups(nextToken=response['nextToken'])
        print('Configured {} log groups'.format(count))

def parse_commandline_arguments():
    return docopt(__doc__, version=__VERSION__)


if __name__ == "__main__":
    main()
