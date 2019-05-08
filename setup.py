# -*- coding: utf-8 -*-

"""Project setup file for fabric8 analytics big query manifest job."""

from setuptools import setup, find_packages


def get_requirements():
    """Parse all packages mentioned in the 'requirements.txt' file."""
    with open('requirements.txt') as fd:
        lines = fd.read().splitlines()
        reqs, dep_links = [], []
        for line in lines:
            if line.startswith('git+'):
                dep_links.append(line)
            else:
                reqs.append(line)
        return reqs, dep_links


# pip doesn't install from dependency links by default,
# so one should install dependencies by
#  `pip install -r requirements.txt`, not by `pip install .`
#  See https://github.com/pypa/pip/issues/2023
reqs, dep_links = get_requirements()
setup(
    name='f8a-bq-manifest-scheduler',
    version='0.1',
    scripts=[
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=reqs,
    dependency_links=dep_links,
    include_package_data=True,
    author='Dipanjan Sarkar',
    author_email='dsarkar@redhat.com',
    description='Retrieve store manifests from GitHub using Google BigQuery',
    license='ASL 2.0',
    keywords='f8a-bq-manifest-scheduler',
    url=('https://github.com/fabric8-analytics/'
         'fabric8-analytics-bigquery-manifests-job')
)
