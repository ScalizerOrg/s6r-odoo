from ._fixtures import *

from s6r_odoo.odoo import OdooConnection
from s6r_odoo.model import OdooModel
from s6r_odoo.record import OdooRecord
from s6r_odoo.record_set import OdooRecordSet


def test_values_to_record(odoo):
    model_name = 'res.partner'

    partner_id = odoo.values_to_record(model_name,123)
    assert isinstance(partner_id, OdooRecord)
    assert partner_id.id == 123

    partner_values = {
        'name': 'Jean-Test',
        'email': 'jean@test.cool'
    }
    partner_id = odoo.values_to_record(model_name,partner_values)
    assert isinstance(partner_id, OdooRecord)
    assert partner_id.name == 'Jean-Test'

    #TODO test cache

def test_get_xmlid_dict(odoo):
    xmlids = odoo.model('ir.module.module').get_xmlid_dict()

    assert 'base.module_account' in xmlids

def test_get_id_ref_dict(odoo):
    id_refs = odoo.model('ir.module.module').get_id_ref_dict()

    #check if dict has at least a key '1' containing a string with a '.'
    assert len(id_refs.get(1).split('.')) == 2

def test_get_ir_model_data(odoo_multi_versions):
    odoo = odoo_multi_versions
    ir_model_data = odoo.model('ir.module.module').get_ir_model_data()

    assert isinstance(ir_model_data, OdooRecordSet)
    assert ir_model_data._model.model_name == 'ir.model.data'

