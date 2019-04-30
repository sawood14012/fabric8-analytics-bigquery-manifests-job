import pytest
from unittest import mock
import json
import shutil
import pathlib
import tempfile
import os
import uuid
import sqlite3

from rudra.data_store.local_data_store import LocalDataStore
from src import manifests_job

class MockDB:

    def __init__(self, db=':memory:'):
        self.session = sqlite3.connect(db)
        self.cols = ['id', 'name', 'content']
        self._create_data()

    def _create_data(self):
        query = """
        drop table if exists manifests;
        create table manifests({id} int, {nm} char, {cn} char);
        insert into manifests ({id}, {nm}, {cn}) values (1, 'requirements.txt', '{rq}');
        insert into manifests ({id}, {nm}, {cn}) values (2, 'requirements.txt', '{rq}');
        insert into manifests ({id}, {nm}, {cn}) values (3, 'package.json', '{pk}');
        insert into manifests ({id}, {nm}, {cn}) values (4, 'package.json', '{pk}');
        insert into manifests ({id}, {nm}, {cn}) values (5, 'pom.xml', '{pm}');
        insert into manifests ({id}, {nm}, {cn}) values (6, 'pom.xml', '{pm}');
        """.format(**dict(zip(('id', 'nm', 'cn'), self.cols)),
                   rq=self.manifest_content('pypi'),
                   pm=self.manifest_content('maven'),
                   pk=self.manifest_content('npm')
                   )

        self.session.executescript(query)

    def manifest_content(self, eco):
        eco_map_manifest = {'pypi': 'requirements.txt',
                            'maven': 'pom.xml',
                            'npm': 'package.json'}

        dir_path = pathlib.Path(__file__).resolve().parents[0]
        test_dir_path = dir_path.joinpath(
            "data", eco_map_manifest.get(eco)).absolute()
        with open(test_dir_path) as f:
            return f.read()

    def run(self, query):
        res = self.session.execute(query).fetchall()
        return [dict(zip(self.cols, r)) for r in res]


class QueryJob:

    def __init__(self, qry=None, job_id=uuid.uuid4()):
        self.output = MockDB().run(qry)
        self.job_id = job_id
        self.state = 'PENDING'

    def result(self):
        return self.output

    def done(self):
        return True

    def __iter__(self):
        return iter(self.output)


class MockBigQuery(mock.Mock):

    QueryJobConfig = type('QueryJobConfig', (), {'priority': None})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = self.Job

    class Client:

        def __init__(self, *args, **kwargs):
            self._state_flag = False

        def query(self, qry, *args, **kwargs):
            self.qry = qry
            return QueryJob(self.qry)

        def get_job(self, job_id):
            query_job = QueryJob(qry=self.qry, job_id=job_id)
            query_job.state = ['PENDING', 'DONE'][self._state_flag]
            self._state_flag = True
            return query_job

    class Job:
        QueryJobConfig = type('QueryJobConfig', (), {})

    class QueryPriority:
        BATCH = 'batch'


class MockS3(LocalDataStore):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_connected = lambda: True

    def object_exists(self, fname):
        return pathlib.Path(self.src_dir).joinpath(fname).exists()

    def write_json_file(self, fname, content):
        fpath = pathlib.Path(self.src_dir).joinpath(fname)
        if not fpath.parent.exists():
            fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(str(fpath.absolute()), 'w') as json_fileobj:
            return json.dump(content, json_fileobj)

    def connect(self):
        return self.is_connected()

    def __del__(self):
        shutil.rmtree(self.src_dir)


@pytest.fixture
@mock.patch('rudra.data_store.bigquery.base.bigquery',
            new_callable=MockBigQuery)
def _data_process_client_maven(_mock_bigquery_obj):
    _mvn_ins = manifests_job.mvn_bq.MavenBigQuery()
    s3_client = MockS3(tempfile.mkdtemp())
    _mvn_ins.query = "select id, name, content from manifests\
            where name like '%pom.xml'"
    _client = manifests_job.mvn_bq.MavenBQDataProcessing(_mvn_ins, s3_client=s3_client)
    return _client, s3_client


@pytest.fixture
@mock.patch('rudra.data_store.bigquery.base.bigquery',
            new_callable=MockBigQuery)
def _data_process_client_npm(_mock_bigquery_obj):
    _npm_ins = manifests_job.npm_bq.NpmBigQuery()
    s3_client = MockS3(tempfile.mkdtemp())
    _npm_ins.query = "select id, name, content from manifests\
            where name like '%package.json'"
    _client = manifests_job.npm_bq.NpmBQDataProcessing(_npm_ins, s3_client=s3_client)
    return _client, s3_client


@pytest.fixture
@mock.patch('rudra.data_store.bigquery.base.bigquery',
            new_callable=MockBigQuery)
def _data_process_client_pypi(_mock_bigquery_obj):
    
    _pypi_ins = manifests_job.pypi_bq.PyPiBigQuery()
    s3_client = MockS3(tempfile.mkdtemp())
    _pypi_ins.query = "select id, name, content from manifests\
            where name like '%requirements.txt'"
    _client = manifests_job.pypi_bq.PyPiBigQueryDataProcessing(_pypi_ins, s3_client=s3_client)
    return _client, s3_client


class TestManifestsJob:

    def test_run_maven_job(self, _data_process_client_maven):
        dp_client, s3_client = _data_process_client_maven
        dp_client.process()
        data = s3_client.read_json_file(dp_client.filename)
        assert 'maven' in data
        assert len(data['maven']) > 0
        for k, v in data['maven'].items():
            assert 'org.apache.camel:camel-spring-boot-starter' in k
            assert 'org.springframework.boot:spring-boot-starter-web' in k
            assert v == 2

    def test_run_npm_job(self, _data_process_client_npm):
        dp_client, s3_client = _data_process_client_npm
        dp_client.process()
        data = s3_client.read_json_file(dp_client.filename)
        assert 'npm' in data
        assert len(data['npm']) > 0
        for k, v in data['npm'].items():
            assert 'request' in k
            assert 'winston' in k
            assert 'xml2object' in k
            assert v == 2

    def test_run_pypi_job(self, _data_process_client_pypi):
        dp_client, s3_client = _data_process_client_pypi
        dp_client.process(validate=True)
        data = s3_client.read_json_file(dp_client.filename)
        assert 'pypi' in data
        assert len(data['pypi']) > 0
        for k, v in data['pypi'].items():
            assert 'boto' in k
            assert 'chardet' in k
            assert 'flask' in k
            assert 'unknown1' not in k
            assert 'unknown2' not in k
            assert v == 2
