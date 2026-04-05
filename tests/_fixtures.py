# - Official doc about fixtures: https://docs.pytest.org/en/stable/how-to/fixtures.html#fixtures-can-introspect-the-requesting-test-context
# - Good article about using fixtures with arguments: https://pytest-with-eric.com/fixtures/pytest-fixture-with-arguments/

import pytest
import os
import logging

from s6r_odoo.odoo import OdooConnection

auth_v16 = {
    'url':'https://s6r-odoo-unit-test.16.demo.scalizer.fr',
    'dbname':'s6r-odoo-unit-test.16.demo.scalizer.fr',
    'user':'admin',
    'password':os.environ.get('ODOO_V16_PASSWORD', ''),
}
auth_v17 = {
    'url':'https://s6r-odoo-unit-test.17.demo.scalizer.fr',
    'dbname':'s6r-odoo-unit-test.17.demo.scalizer.fr',
    'user':'admin',
    'password': os.environ.get('ODOO_V17_PASSWORD', ''),
}
auth_v18 = {
    'url':'https://s6r-odoo-unit-test.18.demo.scalizer.fr',
    'dbname':'s6r-odoo-unit-test.18.demo.scalizer.fr',
    'user':'admin',
    'password': os.environ.get('ODOO_V18_PASSWORD', ''),
}
auth_v19 = {
    'url':'https://s6r-odoo-unit-test.19.demo.scalizer.fr',
    'dbname':'s6r-odoo-unit-test.19.demo.scalizer.fr',
    'user':'admin',
    'password': os.environ.get('ODOO_V19_API_KEY', ''),
    'version': 19,
}

# Base connection fixture
@pytest.fixture
def odoo_conn():
    def _odoo_conn(**kwargs):
        logging.basicConfig()
        logger = logging.getLogger("test")
        kwargs.setdefault('version', 18)
        kwargs.setdefault('debug_xmlrpc', False)
        kwargs['logger'] = logger
        return OdooConnection(**kwargs)
    return _odoo_conn

#Latest version (XML-RPC)
@pytest.fixture(params=[auth_v18], ids=['v18'])
def odoo_rpc(odoo_conn,request):
    return odoo_conn(**request.param)

#Latest version (JSON-2)
@pytest.fixture(params=[auth_v19], ids=['v19'])
def odoo_json2(odoo_conn,request):
    return odoo_conn(**request.param)

#Latest version
@pytest.fixture(params=[auth_v19], ids=['v19'])
def odoo(odoo_conn,request):
    return odoo_conn(**request.param)

#All versions
@pytest.fixture(params=[auth_v16, auth_v17, auth_v18, auth_v19], ids=['v16', 'v17', 'v18', 'v19'])
def odoo_multi_versions(odoo_conn,request):
    return odoo_conn(**request.param)
