# -*- coding: utf-8 -*-
"""
This file contains the constants for interaction with AWS/Minio.

Note: Please don't add keys directly here, refer to environment variables
"""

import os

USE_CLOUD_SERVICES = False
AWS_S3_ACCESS_KEY_ID = os.environ.get('AWS_S3_ACCESS_KEY_ID', '')
AWS_S3_SECRET_ACCESS_KEY = os.environ.get('AWS_S3_SECRET_ACCESS_KEY', '')
S3_BUCKET_NAME = 'developer-analytics-audit-report'
MANIFEST_FILENAME = 'collated.json'