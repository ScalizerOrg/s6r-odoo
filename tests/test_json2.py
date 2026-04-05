from ._fixtures import *  # noqa: F401, F403


def test_connection(odoo_json2):
    assert odoo_json2.uid
    assert odoo_json2._use_json2


def test_search(odoo_json2):
    countries = odoo_json2.model('res.country').search([], fields=['code', 'name'], limit=5)
    assert len(countries) == 5
    assert countries[0].code


def test_search_read(odoo_json2):
    partners = odoo_json2.model('res.partner').search([], fields=['name'], limit=3)
    assert len(partners) == 3
    assert partners[0].name


def test_read(odoo_json2):
    partner = odoo_json2.model('res.partner').read(1, fields=['name'])
    assert partner.id == 1
    assert partner.name


def test_search_count(odoo_json2):
    count = odoo_json2.model('res.country').search_count([])
    assert count > 0


def test_fields_get(odoo_json2):
    fields = odoo_json2.model('res.partner').get_fields(['name', 'email'])
    assert 'name' in fields
    assert 'email' in fields


def test_create_write_unlink(odoo_json2):
    records = odoo_json2.create('res.partner', {'name': 'JSON2 Test Partner'})
    rec = records[0]
    assert rec.id

    odoo_json2.write('res.partner', [rec.id], {'name': 'JSON2 Test Updated'})

    updated = odoo_json2.model('res.partner').read(rec.id, fields=['name'], no_cache=True)
    assert updated.name == 'JSON2 Test Updated'

    odoo_json2.unlink('res.partner', [rec.id])


def test_load(odoo_json2):
    res = odoo_json2.model('res.partner').load_batch([
        {'name': 'JSON2 Load Test 1'},
        {'name': 'JSON2 Load Test 2'},
    ])
    assert res.get('ids')
    assert len(res['ids']) == 2
    odoo_json2.unlink('res.partner', res['ids'])


def test_get_object_reference(odoo_json2):
    ref = odoo_json2.get_object_reference('base.module_account')
    assert ref
    assert ref[0] == 'ir.module.module'
    assert isinstance(ref[1], int)


def test_get_ref(odoo_json2):
    res_id = odoo_json2.get_ref('base.module_account')
    assert isinstance(res_id, int)
    assert res_id > 0


def test_ref(odoo_json2):
    module = odoo_json2.ref('base.module_account')
    assert module.id
    assert module.name == 'account'


def test_get_xml_id_from_id(odoo_json2):
    res_id = odoo_json2.get_ref('base.module_account')
    xml_id = odoo_json2.get_xml_id_from_id('ir.module.module', res_id)
    assert xml_id == 'base.module_account'


def test_get_xmlid_dict(odoo_json2):
    xmlid_dict = odoo_json2.model('ir.module.module').get_xmlid_dict()
    assert isinstance(xmlid_dict, dict)
    assert 'base.module_account' in xmlid_dict


def test_get_id_ref_dict(odoo_json2):
    id_ref_dict = odoo_json2.model('ir.module.module').get_id_ref_dict()
    assert isinstance(id_ref_dict, dict)
    res_id = odoo_json2.get_ref('base.module_account')
    assert id_ref_dict[res_id] == 'base.module_account'


def test_filtered(odoo_json2):
    countries = odoo_json2.model('res.country').search([], fields=['code', 'name'])
    fr = countries.filtered(code='FR')
    assert len(fr) == 1
    assert fr[0].code == 'FR'

    filtered_lambda = countries.filtered(lambda c: c.code in ('FR', 'BE'))
    assert len(filtered_lambda) >= 1


def test_mapped(odoo_json2):
    countries = odoo_json2.model('res.country').search([], fields=['code'], limit=10)
    codes = countries.mapped('code')
    assert isinstance(codes, list)
    assert len(codes) == 10


def test_mapped_relation(odoo_json2):
    partners = odoo_json2.model('res.partner').search(
        [('country_id', '!=', False)], fields=['country_id', 'name'], limit=10)
    country_codes = partners.mapped('country_id.code')
    assert isinstance(country_codes, list)
    assert len(country_codes) > 0


def test_lazy_field_access(odoo_json2):
    """Access a field not in the initial read — triggers lazy load."""
    module = odoo_json2.model('ir.module.module').search(
        [('name', '=', 'account')], fields=['name'], limit=1)
    assert module.name == 'account'
    assert module.category_id


def test_search_ir_model_data(odoo_json2):
    data_ids = odoo_json2.search_ir_model_data([('module', '=', 'base'), ('model', '=', 'res.country')])
    assert len(data_ids) > 0
    models = data_ids.mapped('model')
    assert 'res.country' in models


def test_recordset_save(odoo_json2):
    """RecordSet.save() uses load_batch internally."""
    vals = [{'name': f'JSON2 Save Test {i}'} for i in range(3)]
    records = odoo_json2.model('res.partner.category').values_list_to_records(vals)
    records.save()
    assert all(r.id for r in records)
    records.unlink()


def test_record_save(odoo_json2):
    """OdooRecord.save() for a single new record."""
    rec = odoo_json2.model('res.partner.category').values_to_record(
        {'name': 'JSON2 Single Save'}, update_cache=False)
    rec.save()
    assert rec.id
    rec.unlink()


def test_create_with_orm_commands(odoo_json2):
    """Create a record with many2many ORM commands like [[6, 0, [ids]]]."""
    # Create two tags first
    tag1 = odoo_json2.create('res.partner.category', {'name': 'ORM Cmd Tag 1'})
    tag2 = odoo_json2.create('res.partner.category', {'name': 'ORM Cmd Tag 2'})
    tag_ids = [tag1[0].id, tag2[0].id]

    # Create partner with many2many ORM command
    partner = odoo_json2.create('res.partner', {
        'name': 'ORM Commands Test',
        'category_id': [[6, 0, tag_ids]],
    })
    rec = partner[0]
    assert rec.id

    # Verify tags were assigned
    read_partner = odoo_json2.model('res.partner').read(rec.id, fields=['category_id'], no_cache=True)
    assert len(read_partner.category_id) == 2

    # Cleanup
    odoo_json2.unlink('res.partner', [rec.id])
    odoo_json2.unlink('res.partner.category', tag_ids)


def test_default_get(odoo_json2):
    defaults = odoo_json2.default_get('res.partner', ['name', 'is_company'])
    assert isinstance(defaults, dict)


def test_read_group(odoo_json2):
    result = odoo_json2.read_group(
        'res.partner', [('is_company', '=', True)],
        ['country_id'], ['country_id'], limit=5)
    assert isinstance(result, list)
