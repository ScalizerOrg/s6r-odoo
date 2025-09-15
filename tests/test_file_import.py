try:
    from ._fixtures import *
except ImportError:
    pass

def test_csv_file_import(odoo):
    model_name = 'res.partner'
    result = odoo.import_csv('res.partner.csv', model_name, limit=100, skip_line=500, batch_size=50)
    _test_import_result(odoo, model_name, result)

def _test_import_result(odoo, model_name, result):
    assert result and result.get('ids')
    assert len(result.get('ids')) == 100
    partner_id = odoo.model(model_name).read(result.get('ids')[0], ['name'])
    assert partner_id.name == 'Partner 501'
    partner_id = odoo.model(model_name).read(result.get('ids')[-1], ['name'])
    assert partner_id.name == 'Partner 600'

def test_xls_file_import(odoo):
    model_name = 'res.partner'
    result = odoo.import_xls('res.partner.xls', model_name, limit=100, skip_line=500, batch_size=50)
    _test_import_result(odoo, model_name, result)

def test_xlsx_file_import(odoo):
    model_name = 'res.partner'
    result = odoo.import_xlsx('res.partner.xlsx', model_name, limit=100, skip_line=500, batch_size=50)
    _test_import_result(odoo, model_name, result)
