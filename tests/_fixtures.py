"""
- Official doc about fixtures: https://docs.pytest.org/en/stable/how-to/fixtures.html#fixtures-can-introspect-the-requesting-test-context
- Good article about using fixtures with arguments: https://pytest-with-eric.com/fixtures/pytest-fixture-with-arguments/
"""

import pytest
import os
import logging

from s6r_odoo.odoo import OdooConnection

auth_v16 = {
    'url':'https://s6r-odoo-unit-test.16.demo.scalizer.fr',
    'dbname':'s6r-odoo-unit-test.16.demo.scalizer.fr',
    'user':'admin',
    'password':os.environ['ODOO_V16_PASSWORD'],
}
auth_v17 = {
    'url':'https://s6r-odoo-unit-test.17.demo.scalizer.fr',
    'dbname':'s6r-odoo-unit-test.17.demo.scalizer.fr',
    'user':'admin',
    'password': os.environ['ODOO_V17_PASSWORD'],
}
auth_v18 = {
    'url':'https://s6r-odoo-unit-test.18.demo.scalizer.fr',
    'dbname':'s6r-odoo-unit-test.18.demo.scalizer.fr',
    'user':'admin',
    'password': os.environ['ODOO_V18_PASSWORD'],
}

# Base connection fixture
@pytest.fixture
def odoo_conn():
    def _odoo_conn(url, dbname, user, pwd):
        logging.basicConfig()
        logger = logging.getLogger("test")
        return OdooConnection(url=url,
                                   dbname=dbname,
                                   user=user,
                                   password=pwd,
                                   debug_xmlrpc=False,
                                   logger=logger)
    return _odoo_conn

#Latest version
@pytest.fixture(params=[auth_v18], ids=['v18'])
def odoo(odoo_conn,request):
    return odoo_conn(*request.param.values())

#3 latest versions
@pytest.fixture(params=[auth_v16, auth_v17, auth_v18], ids=['v16', 'v17', 'v18'])
def odoo_multi_versions(odoo_conn,request):
    return odoo_conn(*request.param.values())
