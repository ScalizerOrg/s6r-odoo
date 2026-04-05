from ._fixtures import *  # noqa: F401, F403


def test_connection(odoo_rpc):
    assert odoo_rpc.uid
    assert not odoo_rpc._use_json2


def test_search(odoo_rpc):
    countries = odoo_rpc.model('res.country').search([], fields=['code', 'name'], limit=5)
    assert len(countries) == 5
    assert countries[0].code


def test_search_read(odoo_rpc):
    partners = odoo_rpc.model('res.partner').search([], fields=['name'], limit=3)
    assert len(partners) == 3
    assert partners[0].name


def test_read(odoo_rpc):
    partner = odoo_rpc.model('res.partner').read(1, fields=['name'])
    assert partner.id == 1
    assert partner.name


def test_search_count(odoo_rpc):
    count = odoo_rpc.model('res.country').search_count([])
    assert count > 0


def test_fields_get(odoo_rpc):
    fields = odoo_rpc.model('res.partner').get_fields(['name', 'email'])
    assert 'name' in fields
    assert 'email' in fields


def test_create_write_unlink(odoo_rpc):
    records = odoo_rpc.create('res.partner', {'name': 'RPC Test Partner'})
    rec = records[0]
    assert rec.id

    odoo_rpc.write('res.partner', [rec.id], {'name': 'RPC Test Updated'})

    updated = odoo_rpc.model('res.partner').read(rec.id, fields=['name'], no_cache=True)
    assert updated.name == 'RPC Test Updated'

    odoo_rpc.unlink('res.partner', [rec.id])


def test_load(odoo_rpc):
    res = odoo_rpc.model('res.partner').load_batch([
        {'name': 'RPC Load Test 1'},
        {'name': 'RPC Load Test 2'},
    ])
    assert res.get('ids')
    assert len(res['ids']) == 2
    odoo_rpc.unlink('res.partner', res['ids'])


def test_get_object_reference(odoo_rpc):
    ref = odoo_rpc.get_object_reference('base.module_account')
    assert ref
    assert ref[0] == 'ir.module.module'
    assert isinstance(ref[1], int)


def test_get_ref(odoo_rpc):
    res_id = odoo_rpc.get_ref('base.module_account')
    assert isinstance(res_id, int)
    assert res_id > 0


def test_ref(odoo_rpc):
    module = odoo_rpc.ref('base.module_account')
    assert module.id
    assert module.name == 'account'


def test_get_xml_id_from_id(odoo_rpc):
    res_id = odoo_rpc.get_ref('base.module_account')
    xml_id = odoo_rpc.get_xml_id_from_id('ir.module.module', res_id)
    assert xml_id == 'base.module_account'


def test_get_xmlid_dict(odoo_rpc):
    xmlid_dict = odoo_rpc.model('ir.module.module').get_xmlid_dict()
    assert isinstance(xmlid_dict, dict)
    assert 'base.module_account' in xmlid_dict


def test_get_id_ref_dict(odoo_rpc):
    id_ref_dict = odoo_rpc.model('ir.module.module').get_id_ref_dict()
    assert isinstance(id_ref_dict, dict)
    res_id = odoo_rpc.get_ref('base.module_account')
    assert id_ref_dict[res_id] == 'base.module_account'


def test_filtered(odoo_rpc):
    countries = odoo_rpc.model('res.country').search([], fields=['code', 'name'])
    fr = countries.filtered(code='FR')
    assert len(fr) == 1
    assert fr[0].code == 'FR'

    filtered_lambda = countries.filtered(lambda c: c.code in ('FR', 'BE'))
    assert len(filtered_lambda) >= 1


def test_mapped(odoo_rpc):
    countries = odoo_rpc.model('res.country').search([], fields=['code'], limit=10)
    codes = countries.mapped('code')
    assert isinstance(codes, list)
    assert len(codes) == 10


def test_mapped_relation(odoo_rpc):
    partners = odoo_rpc.model('res.partner').search(
        [('country_id', '!=', False)], fields=['country_id', 'name'], limit=10)
    country_codes = partners.mapped('country_id.code')
    assert isinstance(country_codes, list)
    assert len(country_codes) > 0


def test_lazy_field_access(odoo_rpc):
    """Access a field not in the initial read — triggers lazy load."""
    module = odoo_rpc.model('ir.module.module').search(
        [('name', '=', 'account')], fields=['name'], limit=1)
    assert module.name == 'account'
    assert module.category_id


def test_search_ir_model_data(odoo_rpc):
    data_ids = odoo_rpc.search_ir_model_data([('module', '=', 'base'), ('model', '=', 'res.country')])
    assert len(data_ids) > 0
    models = data_ids.mapped('model')
    assert 'res.country' in models


def test_recordset_save(odoo_rpc):
    """RecordSet.save() uses load_batch internally."""
    vals = [{'name': f'RPC Save Test {i}'} for i in range(3)]
    records = odoo_rpc.model('res.partner.category').values_list_to_records(vals)
    records.save()
    assert all(r.id for r in records)
    records.unlink()


def test_record_save(odoo_rpc):
    """OdooRecord.save() for a single new record."""
    rec = odoo_rpc.model('res.partner.category').values_to_record(
        {'name': 'RPC Single Save'}, update_cache=False)
    rec.save()
    assert rec.id
    rec.unlink()


def test_create_with_orm_commands(odoo_rpc):
    """Create a record with many2many ORM commands like [[6, 0, [ids]]]."""
    tag1 = odoo_rpc.create('res.partner.category', {'name': 'ORM Cmd Tag 1'})
    tag2 = odoo_rpc.create('res.partner.category', {'name': 'ORM Cmd Tag 2'})
    tag_ids = [tag1[0].id, tag2[0].id]

    partner = odoo_rpc.create('res.partner', {
        'name': 'ORM Commands Test',
        'category_id': [[6, 0, tag_ids]],
    })
    rec = partner[0]
    assert rec.id

    read_partner = odoo_rpc.model('res.partner').read(rec.id, fields=['category_id'], no_cache=True)
    assert len(read_partner.category_id) == 2

    odoo_rpc.unlink('res.partner', [rec.id])
    odoo_rpc.unlink('res.partner.category', tag_ids)


def test_default_get(odoo_rpc):
    defaults = odoo_rpc.default_get('res.partner', ['name', 'is_company'])
    assert isinstance(defaults, dict)


def test_read_group(odoo_rpc):
    result = odoo_rpc.read_group(
        'res.partner', [('is_company', '=', True)],
        ['country_id'], ['country_id'], limit=5)
    assert isinstance(result, list)
