# -*- coding: utf-8 -*-
# Copyright (c) CloudZero, Inc. All rights reserved.
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

from datetime import datetime, timezone
from awstools.glacier import has_24hours_passed_since


def test_has_24hours_passed_since():
    assert has_24hours_passed_since(datetime.now(timezone.utc)) is False
