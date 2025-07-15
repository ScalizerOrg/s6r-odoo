from ._fixtures import *

from s6r_odoo.odoo import OdooConnection
from s6r_odoo.model import OdooModel
from s6r_odoo.record import OdooRecord
from s6r_odoo.record_set import OdooRecordSet

def test_save(odoo):

    partner_values_list = [
        {
            '/id':'external_import.res_partner_sauvequipeut',
            'name': 'Sauve qui peut',
            'email': 'sqp@test.com',
            'parent_id/id': 'external_import.res_partner_lamaisonmere',

        },
        {
            '/id': 'external_import.res_partner_sauvezlesdauphins',
            'name': 'Sauvez les dauphins',
            'email': 'sld@test.com',
            'parent_id/id': 'external_import.res_partner_lamaisonmere',
        },
        {
            '/id': 'external_import.res_partner_lamaisonmere',
            'name': 'Maison Mère',
            'email': 'mm@test.com',
            'parent_id/id': '',
        },
    ]
    partner_ids = odoo.values_list_to_records('res.partner', partner_values_list)

    #save without hierarchy first
    partner_ids.save(ignore_fields=['parent_id/id'])

    assert len(partner_ids[0]._initialized_fields) == 2
    assert all([f in ['name', 'email'] for f in partner_ids[0]._initialized_fields])
    assert list(partner_ids[0]._updated_values.keys()) == ['parent_id/id']

    #save with hierarchy
    partner_ids.save()

    assert len(partner_ids[0]._initialized_fields) == 3
    assert all([f in ['name', 'email', 'parent_id'] for f in partner_ids[0]._initialized_fields])
    assert partner_ids[0]._updated_values == {}
