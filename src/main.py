# -*- coding: utf-8 -*-
"""The main script for the Big Query manifests retrieval."""

from rudra import logger
import manifests_job as mj
import time


def main():
    """Retrieve, process and store the manifest files.

    These manifests are obtained from Big Query.
    """
    logger.info('Initializing ManifestsJob object')
    mjob = mj.ManifestsJob()
    start = time.monotonic()

    logger.info('Starting Manifest Job')
    mjob.run_maven_job()
    mjob.run_npm_job()
    mjob.run_pypi_job()
    logger.info("Finished Manifest Job, time taken: {}".format(
        time.monotonic() - start))


if __name__ == '__main__':
    main()
