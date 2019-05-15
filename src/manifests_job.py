# -*- coding: utf-8 -*-
"""
Implementation of the class to retrieve and store manifests.

Currently focuses on the following ecosystems
    - Maven
    - NPM
    - PyPI
"""

from rudra import logger
from rudra.data_store.bigquery import maven_bigquery as mvn_bq
from rudra.data_store.bigquery import npm_bigquery as npm_bq
from rudra.data_store.bigquery import pypi_bigquery as pypi_bq
from rudra.data_store.aws import AmazonS3
from src.config import cloud_constants as cc


class ManifestsJob:
    """The ManifestsJob class gets the manifests data from Google Bigquery.

    After data retrieval and processing, it is in AWS S3 sequentially
    for each ecosystem.
    """

    def __init__(self, cloud_services=cc.USE_CLOUD_SERVICES):
        """Initialize the ManifestsJob object."""
        self.local_dev = not cloud_services
        self.bucket_name = cc.S3_BUCKET_NAME
        self.s3_client = AmazonS3(
            region_name=cc.AWS_S3_REGION,
            bucket_name=self.bucket_name,
            aws_access_key_id=cc.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=cc.AWS_S3_SECRET_ACCESS_KEY,
            local_dev=self.local_dev
        )

    def run_maven_job(self):
        """Run the maven big query processing job.

        This job retrieves and stores manifests for
        github projects based on the java ecosystem.
        """
        mvn_bq_builder = mvn_bq.MavenBigQuery()
        mvn_bq_builder.query = """
            SELECT con.content AS content
            FROM `bigquery-public-data.github_repos.contents` AS con
            INNER JOIN (SELECT files.id AS id
                FROM `bigquery-public-data.github_repos.languages` AS langs
                INNER JOIN `bigquery-public-data.github_repos.files` AS files
                    ON files.repo_name = langs.repo_name
                WHERE REGEXP_CONTAINS(TO_JSON_STRING(language), r'(?i)java')
                AND files.path LIKE '%pom.xml'
            ) AS L
            ON con.id = L.id;
        """

        logger.info('Starting job for maven Big Query Manifests')
        mvn_job = mvn_bq.MavenBQDataProcessing(
            big_query_instance=mvn_bq_builder,
            s3_client=self.s3_client,
            file_name=cc.MANIFEST_FILENAME)
        mvn_job.process()
        logger.info('Completed job for maven Big Query Manifests')

    def run_npm_job(self):
        """Run the npm big query processing job.

        This job retrieves and stores manifests for
        github projects based on the node.js ecosystem.
        """
        npm_bq_builder = npm_bq.NpmBigQuery()
        npm_bq_builder.query = """
            SELECT A.repo_name as repo_name, B.content as content
            FROM `bigquery-public-data.github_repos.files` AS A
            INNER JOIN  `bigquery-public-data.github_repos.contents` as B
            ON A.id=B.id WHERE A.path like 'package.json';
        """

        logger.info('Starting job for npm Big Query Manifests')
        npm_job = npm_bq.NpmBQDataProcessing(
            big_query_instance=npm_bq_builder,
            s3_client=self.s3_client,
            file_name=cc.MANIFEST_FILENAME)
        npm_job.process()
        logger.info('Completed job for npm Big Query Manifests')

    def run_pypi_job(self):
        """Run the pypi big query processing job.

        This job retrieves and stores manifests for
        github projects based on the python ecosystem.
        """
        pypi_bq_builder = pypi_bq.PyPiBigQuery()
        pypi_bq_builder.query = """
            SELECT con.content AS content
            FROM `bigquery-public-data.github_repos.contents` AS con
            INNER JOIN (SELECT files.id AS id
                FROM `bigquery-public-data.github_repos.languages` AS langs
                INNER JOIN `bigquery-public-data.github_repos.files` AS files
                    ON files.repo_name = langs.repo_name
                WHERE REGEXP_CONTAINS(TO_JSON_STRING(language), r'(?i)python')
                AND files.path LIKE '%requirements.txt'
            ) AS L
            ON con.id = L.id;
        """

        logger.info('Starting job for pypi Big Query Manifests')
        pypi_job = pypi_bq.PyPiBigQueryDataProcessing(
            big_query_instance=pypi_bq_builder,
            s3_client=self.s3_client,
            file_name=cc.MANIFEST_FILENAME)
        pypi_job.process(validate=True)
        logger.info('Completed job for pypi Big Query Manifests')
