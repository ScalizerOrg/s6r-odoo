from ._fixtures import *

def test_csv_file_import(odoo):
    model_name = 'res.partner'
    result = odoo.import_csv('res.partner.csv', model_name, limit=500, skip_line=500)
    assert result and result.get('ids')
    assert len(result.get('ids')) == 500
    partner_id = odoo.model(model_name).read(result.get('ids')[0], ['name'])
    assert partner_id.name == 'Partner 501'
    partner_id = odoo.model(model_name).read(result.get('ids')[-1], ['name'])
    assert partner_id.name == 'Partner 1000'
