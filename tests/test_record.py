from ._fixtures import *

from s6r_odoo.odoo import OdooConnection
from s6r_odoo.model import OdooModel
from s6r_odoo.record import OdooRecord
from s6r_odoo.record_set import OdooRecordSet

@pytest.mark.skip(reason='WIP')
def test_read_without_fields_without_cache(odoo):

    partner_values = {
        # 'id':1,
        'name': 'Jean-Claude Test',
        'email': 'jc@test.com',
    }
    partner_id = odoo.values_to_record('res.partner', partner_values)

    #doesn't return anything
    p = partner_id.read(no_cache=True)

    pass

    assert False
