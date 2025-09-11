try:
    from ._fixtures import *
except ImportError:
    pass


def _test_load_data(odoo, data):
    res = odoo.model('res.partner').load_batch(data)
    if res and res.get('messages'):
        for message in res.get('messages'):
            odoo.logger.error(message)
        return


def test_load_xmlids(odoo):
    category_values = [{'id': 'external_config.category_test_01', 'name': 'Category 01'},
                       {'id': 'external_config.category_test_02', 'name': 'Category 02'}]
    res = odoo.model('res.partner.category').load_batch(category_values)
    if res and res.get('messages'):
        for message in res.get('messages'):
            odoo.logger.error(message)
        return
    assert res and res.get('ids')
    assert len(res.get('ids')) == 2
    assert odoo.query_count == 1
    odoo.reset_count()
    category_ids = res.get('ids')
    category_ids_str = ','.join([str(i) for i in category_ids])
    category_xmlids_str = ','.join([v['id'] for v in category_values])

    title_ids = odoo.model('res.partner.title').read(['base.res_partner_title_madam', 'base.res_partner_title_mister'],
                                                     ['name'])
    odoo.reset_count()
    data_partners_with_xmlids = [{'id': f'external_config.partner_test_01',
                      'name': 'Lastname Firstname 01',
                      'title/id': 'base.res_partner_title_madam',
                      'category_id/id': category_xmlids_str},
                     {'id': f'external_config.partner_test_02',
                      'name': 'Lastname Firstname 02',
                      'title/id': 'base.res_partner_title_mister',
                      'category_id/id': category_xmlids_str}]

    _test_load_data(odoo, data_partners_with_xmlids)
    partner_ids = odoo.model('res.partner').values_list_to_records(data_partners_with_xmlids)
    assert partner_ids[0].category_id[0].id > 0

    # 2 queries to get titles xmlids (categories xmlids are in cache)
    assert odoo.get_method_count('search_read', 'ir.model.data') == 2

    odoo.reset_count()
    partner_ids = odoo.model('res.partner').values_list_to_records(data_partners_with_xmlids)

    # Use the xmlid cache to get the id
    assert partner_ids[0].title.id == 1
    assert odoo.get_method_count('search_read', 'ir.model.data') == 0

    # Clear the cache and get the title xmlids again
    odoo.clear_cache()
    odoo.reset_count()
    partner_ids = odoo.model('res.partner').values_list_to_records(data_partners_with_xmlids)
    assert partner_ids[0].title.id == 1
    assert odoo.get_method_count('search_read', 'ir.model.data') == 4
    partner_ids.save()

    # test without xmlids in values
    odoo.clear_cache()
    odoo.reset_count()
    data_partners = [{'id': f'external_config.partner_test_01',
                      'name': 'Lastname Firstname 01',
                      'title.id': title_ids[0].id,
                      'category_id.id': category_ids_str},
                     {'id': f'external_config.partner_test_02',
                      'name': 'Lastname Firstname 02',
                      'title.id': title_ids[1].id,
                      'category_id.id': category_ids_str}]
    _test_load_data(odoo, data_partners)
    partner_ids = odoo.model('res.partner').values_list_to_records(data_partners)
    partner_ids.save()
    assert partner_ids[0].id > 0
    assert odoo.get_method_count('search_read', 'ir.model.data') == 0

    # Test resolve_xmlids param
    odoo.clear_cache()
    odoo.reset_count()
    partner_ids = odoo.model('res.partner').values_list_to_records(data_partners, resolve_xmlids=False)
    partner_ids.save()
    assert partner_ids[0].id > 0
    assert odoo.get_method_count('search_read', 'ir.model.data') == 0
