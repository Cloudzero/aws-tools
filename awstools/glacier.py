#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) CloudZero, Inc. All rights reserved.
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

"""
Simple utility for manipulating AWS Glacier vaults and archives

Usage:
    glacier [delete] [--name <name>] [--profile <profile>] [--verbose]
    glacier -h | --help

Options:
    -h --help               Show this screen.
    -p --profile <profile>  AWS Credentials profile to use [default: default].
    -n --name <name>        Name of image [default: amzn-ami-hvm*].
    -v --verbose            Display as much detail of the operation as possible.
"""

from __future__ import print_function
from awstools import __VERSION__

import json
from datetime import datetime, timezone, timedelta
import dateutil.parser
from docopt import docopt
import boto3

__TAG_PREFACE__ = "CLOUDZERO_GLACIER_TOOLS"


def main():
    args = parse_commandline_arguments()

    session = boto3.session.Session(profile_name=args['--profile'])
    client = session.client('glacier')

    vault_list = []

    vaults = client.list_vaults()
    __FMT__ = "{:35} {:25} {:25} {:>13} {:>13} {:>5} {:}"
    print(__FMT__.format("Name", "Created", "last inventory", "# of Archives", "Size (bytes)", "Jobs", "ARN"))
    for vault in vaults['VaultList']:
        jobs = client.list_jobs(vaultName=vault['VaultName'])
        print(__FMT__.format(vault['VaultName'],
                             vault['CreationDate'],
                             vault['LastInventoryDate'],
                             vault['NumberOfArchives'],
                             vault['SizeInBytes'],
                             len(jobs['JobList']),
                             vault['VaultARN']))

        job = None
        latest_job_date = dateutil.parser.parse("0001-1-1T00:00Z")  # A time long long ago
        latest_job = {}
        for job in jobs['JobList']:
            job['CreationDate'] = dateutil.parser.parse(job['CreationDate'])
            if job['Completed']:
                job['CompletionDate'] = dateutil.parser.parse(job['CompletionDate'])
            if latest_job_date < job['CreationDate']:
                latest_job_date = job['CreationDate']
                latest_job = job
            print(" - JOB: {}   {:15}   {}   {}".format(job['Action'],
                                                        job['StatusCode'],
                                                        job['CreationDate'],
                                                        job['JobDescription']))
        else:
            if job is not None:
                print("  ")

        vault_list += [
            {"name": vault['VaultName'], "archive_count": vault['NumberOfArchives'], "job_count": len(jobs['JobList']),
             "latest_job": latest_job, "arn": vault['VaultARN'], "last_inventory_date": ""}]

    if args['delete']:
        print("\nDeleting all Vaults:")
        print(" - Checking for available inventory data.")
        for vault in vault_list:
            if vault['archive_count'] == 0:
                print(" - Vault '{}' is empty, deleting".format(vault['name']))
                # client.delete_vault(vaultName=vault['name'])
            elif ready_for_archive_delete(vault, client):
                print(" - Starting delete of all archives from vault {}".format(vault['name']))
                count = delete_all_archives_from_vault(vault, client)
                print(" - Delete process started for {} archives, it can"
                      " take up to 24 hours for this to complete".format(count))
            elif not is_refresh_in_progress(vault, client):
                print(" - Refreshing inventory for vault {}".format(vault['name']))
                refresh_vault_inventory(vault, client)
            else:
                print(" - Inventory refresh in progress, please try again later")


def ready_for_archive_delete(vault, client):
    return ((vault['archive_count'] > 0 and is_inventory_refreshed(vault, client)) and
            not is_delete_in_progress(vault, client))


def is_inventory_refreshed(vault, client):
    refresh_timestamp = get_refresh_timestamp(vault, client)

    if not refresh_timestamp:  # Inventory refresh never run
        return 0
    elif vault['latest_job']['Action'] == "InventoryRetrieval" and vault['latest_job']['Completed']:
        return 1
    else:
        return has_24hours_passed_since(refresh_timestamp)


def is_delete_in_progress(vault, client):
    delete_timestamp = get_delete_timestamp(vault, client)

    if not delete_timestamp:  # delete never run
        return False
    else:
        return not has_24hours_passed_since(delete_timestamp) and is_inventory_refreshed(vault, client)


def is_refresh_in_progress(vault, client):
    refresh_timestamp = get_refresh_timestamp(vault, client)

    if not refresh_timestamp:  # Inventory refresh never run
        return False
    else:
        return vault['latest_job']['Action'] == "InventoryRetrieval" and not vault['latest_job']['Completed']


def refresh_vault_inventory(vault, client: boto3.client) -> object:
    response = client.initiate_job(
        vaultName=vault['name'],
        jobParameters={
            'Format': 'JSON',
            'Type': 'inventory-retrieval',
            'Description': 'CloudZero AWS Tools - Glacier inventory retrieval'
            # 'SNSTopic': 'string',
            # 'InventoryRetrievalParameters': {
            #     'StartDate': 'string',
            #     'EndDate': 'string',
            #     'Limit': 'string',
            #     'Marker': 'string'
            # }
        }
    )
    set_refresh_timestamp(vault, client)
    return response


def delete_all_archives_from_vault(vault, client):
    response = client.get_job_output(
        vaultName=vault['name'],
        jobId=vault['latest_job']['JobId'],
    )
    inventory_data = json.loads(response['body'].read().decode("utf-8"))
    archive_count = 0
    print("  ", end="")
    for archive in inventory_data['ArchiveList']:
        client.delete_archive(vaultName=vault['name'], archiveId=archive['ArchiveId'])
        print('.', end="", flush=True)
        archive_count += 1
    print(".")
    set_delete_timestamp(vault, client)
    return archive_count


def has_24hours_passed_since(timestamp):
    return timestamp < datetime.now(timezone.utc) - timedelta(hours=24)


def get_refresh_timestamp(vault, client):
    try:
        return dateutil.parser.parse(get_vault_tag(vault['name'], "REFRESH", client))
    except AttributeError:
        return 0


def set_refresh_timestamp(vault, client):
    return set_vault_tag(vault['name'], "REFRESH", datetime.now(timezone.utc).isoformat(), client)


def get_delete_timestamp(vault, client):
    try:
        return dateutil.parser.parse(get_vault_tag(vault['name'], "DELETE", client))
    except AttributeError:
        return 0


def set_delete_timestamp(vault, client):
    return set_vault_tag(vault['name'], "DELETE", datetime.now(timezone.utc).isoformat(), client)


def get_vault_tag(vault_name, name, client):
    tags = client.list_tags_for_vault(
        vaultName=vault_name
    )

    return tags['Tags'].get("{}_{}".format(__TAG_PREFACE__, name), None)


def set_vault_tag(vault_name, name, value, client):
    response = client.add_tags_to_vault(
        vaultName=vault_name,
        Tags={
            "{}_{}".format(__TAG_PREFACE__, name): value
        }
    )
    return response


def parse_commandline_arguments():
    return docopt(__doc__, version=__VERSION__)


if __name__ == "__main__":
    main()
