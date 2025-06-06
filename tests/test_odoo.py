from ._fixtures import *

from s6r_odoo.odoo import OdooConnection
from s6r_odoo.model import OdooModel
from s6r_odoo.record import OdooRecord
from s6r_odoo.record_set import OdooRecordSet

def test_model(odoo):
    model_name = 'res.partner'
    model = odoo.model(model_name)

    assert model_name in odoo._models
    assert isinstance(model,OdooModel)

def test_get_object_reference(odoo):
    object_reference = odoo.get_object_reference('base.module_account')

    assert len(object_reference) == 2
    assert object_reference[0] == 'ir.module.module'
    assert isinstance(object_reference[1], int)

def test_get_ref(odoo):
    res_id = odoo.get_ref('base.module_account')

    assert isinstance(res_id,int)

def test__read_success(odoo_multi_versions):
    odoo = odoo_multi_versions
    ids = [1]
    fields = [
        'author',
        'description',
        'display_name',
        'name',
        'state',
        'website',
    ]
    res = odoo._read('ir.module.module',ids,fields)

    assert len(res)==1
    assert res[0]['author'] == 'Odoo S.A.'

def test_ref(odoo_multi_versions):
    #trying ref() on 'ir.module.module' model raises an XMPLRPC error on v17+ (because of None value)
    odoo = odoo_multi_versions
    country_fr = odoo.ref('base.fr')

    assert isinstance(country_fr, OdooRecord)
    assert country_fr.name == 'France'
    #TODO
    #assert country_fr._xmlid = 'base.fr'

