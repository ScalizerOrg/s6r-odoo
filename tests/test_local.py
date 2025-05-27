import logging
import time
import random
import string
from src.s6r_odoo import OdooConnection

def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def test_local():
    logging.basicConfig()
    logger = logging.getLogger("test")

    odoo = OdooConnection(url='http://odoo_project.localhost',
                          dbname='project',
                          user='admin',
                          password='admin', debug_xmlrpc=False, logger=logger)

    xmlid_dict = odoo.model('ir.module.module').get_xmlid_dict()
    logger.info('ir.module.module XMLIDs : %s', xmlid_dict)
    id_ref_dict = odoo.model('ir.module.module').get_id_ref_dict()
    logger.info('ir.module.module ID refs : %s', id_ref_dict)
    ir_model_data = odoo.model('ir.module.module').get_ir_model_data()
    logger.info('ir.module.module ir_model_data : %s', ir_model_data)

    object_reference = odoo.get_object_reference('base.module_account')
    logger.info("base.module_account get_object_reference --> ['ir.module.module', id] : %s", object_reference)
    res_id = odoo.get_ref('base.module_account')
    logger.info("base.module_account get_ref --> id : %s", res_id)
    module_account = odoo.ref('base.module_account')
    msg = 'base.module_account ref --> OdooRecord :\nModule: %s (%s)\nDescription: %s'
    logger.info(msg, module_account.display_name,
                module_account.name,
                module_account.description)

    odoo.get_xml_id_from_id('ir.module.module', module_account.id)

    odoo.print_query_count()

    partner_fields = odoo.execute_odoo('res.partner', 'fields_get', [['name'], None])
    partner_fields2 = odoo.model('res.partner').execute('fields_get', ['name'])

    country_fields = odoo.model('res.country').get_fields([])
    country_required_fields = ', '.join(
        country_fields[key]['name'] for key in country_fields if country_fields[key]['required'])
    logger.info('Country required fields : %s', country_required_fields)

    # Script optimised to access license and category_id field
    start_time = time.time()
    module_ids = odoo.model('ir.module.module').search([('author', 'ilike', 'Odoo')],
                                                       fields=['display_name', 'category_id', 'license'],
                                                       order='create_date desc, name', limit=100)
    optimized_query_time = time.time() - start_time
    start_time = time.time()
    logger.info('Module categories : %s', ', '.join(set([module.category_id.name for module in module_ids])))
    for module_id in module_ids:
        module_license = module_id.license if module_id['license'] else 'Unknown'
        logger.info('* Module %s : %s', module_id.display_name, module_id.license)
        continue
    optimized_time = time.time() - start_time
    logger.info("Optimised Script : %s seconds (first query : %s seconds)", optimized_time, optimized_query_time)

    # Script NOT optimised to access to licence and category_id field
    # start_time = time.time()
    # module_ids = odoo.model('ir.module.module').search([('author', 'ilike', 'Odoo')],
    #                                                    fields=['display_name'],
    #                                                    order='create_date desc, name', limit=10)
    # not_optimized_query_time = time.time() - start_time
    # start_time = time.time()
    # logger.info('Module categories : %s', ', '.join(set([module.category_id.name for module in module_ids])))
    # for module_id in filter(lambda x: x.category_id.name != 'Scalizer', module_ids): # module_ids:
    #     module_license = module_id.license if module_id['license'] else 'Unknown'
    #     logger.info('* Module %s : %s', module_id.display_name, module_id.license)
    #     continue
    # not_optimized_time = time.time() - start_time
    # logger.info("NOT Optimised Script : %s seconds (first query : %s seconds)", not_optimized_time, not_optimized_query_time)


    # XMLIDs Tests
    # logger.info('Module XMLIDs : %s', odoo.get_xmlid_dict('ir.module.module'))

    object_id = odoo.get_ref('base.module_account')
    logger.info('base.module_account get_ref --> id : %s', object_id)
    module_account_lazy = odoo.model('ir.module.module').read(object_id, ['name', 'description'])

    logger.info('Module (LAZY): %s\nCategory: %s\nDescription: %s\n',
                module_account_lazy['name'],
                module_account_lazy['category_id'].name,
                module_account_lazy['description'])

    # test cache
    origin_email = 'test@example.com'
    email1 = 'john@example.com'
    partner_id = odoo.ref('base.main_partner')
    partner_id.email = email1
    partner_id.save()
    if partner_id.email != email1:
        raise Exception('Email %s not updated' % email1)
    email2 = 'sophie@example.com'
    partner_id.write({'email': email2})
    if partner_id.email != email2:
        raise Exception('Email %s not updated' % email2)

    partner_id2 = odoo.model('res.partner').read(partner_id.id)
    if partner_id2.email_formatted and email2 in partner_id2.email_formatted:
        partner_id.write({'email': origin_email})
        raise Exception('Cache not used with read')

    partner_id2 = odoo.ref('base.main_partner')
    if partner_id2.email_formatted and email2 in partner_id2.email_formatted:
        partner_id.write({'email': origin_email})
        raise Exception('Cache not used with ref')

    partner_id3 = odoo.ref('base.main_partner', no_cache=True)
    if email2 not in partner_id3.email_formatted:
        partner_id.write({'email': origin_email})
        raise Exception('Cache used with ref')
    partner_id3.write({'email': email1})
    partner_id3.refresh()
    if email1 not in partner_id3.email_formatted:
        partner_id.write({'email': origin_email})
        raise Exception('Refresh failed')

    partner_id.write({'email': origin_email})

    partner_ids = odoo.model('res.partner').search([], fields=['name', 'website'])
    for partner_id in partner_ids:
        partner_id.website = 'https://www.%s.com' % get_random_string(8)
    partner_ids.save()

    partner_ids = odoo.model('res.partner').search([('name', '=', 'TO_REMOVE')], fields=['name'])
    if partner_ids:
        partner_ids.unlink()

    new_partner_values_list = [{'name': "TO_REMOVE", 'website': get_random_string(8)} for i in range(5000)]
    new_partner_ids = odoo.model('res.partner').load_batch(new_partner_values_list)
    new_partner_ids.unlink()

    odoo.print_query_count()

    # Test record creation from dict
    partner_tag1_values = {
        'name': 'Test tag without xmlid',
        'color': 2,
    }
    partner_tag1_id = odoo.model('res.partner.category').values_to_record(partner_tag1_values, update_cache=False)
    # this record will be created using "create" method
    partner_tag1_id.save()

    partner_tag2_values = {
        '/id': f'external_config.res_partner_category_test',
        'name': 'Test tag with xmlid',
        'color': 10,
    }
    partner_tag2_id = odoo.model('res.partner.category').values_to_record(partner_tag2_values, update_cache=False)
    # this record will be created using "load" method
    partner_tag2_id.save()
    # cleanup
    partner_tag1_id.unlink()
    partner_tag2_id.unlink()

    partner_tag_values_list = [{'name': f"TAG {i}", 'color': i} for i in range(10)]
    partner_tag_ids = odoo.model('res.partner.category').values_list_to_records(partner_tag_values_list)
    # load the records without xmlid
    for partner_tag in partner_tag_ids:
        partner_tag.computed_value = partner_tag.color % 2 == 0

    filtered_tag_ids = partner_tag_ids.filtered(lambda x: x.computed_value)
    filtered_tag_ids2 = partner_tag_ids.filtered(computed_value=True, name='TAG 8')

    partner_tag_ids.save()
    partner_tag_ids.unlink()

    partner_tags_list2 = [{'/id': f"external_config.res_partner_category_{i}", 'name': f"TAG {i}", 'color': i - 10} for
                          i in range(10, 20)]
    partner_tag_ids2 = odoo.model('res.partner.category').values_list_to_records(partner_tags_list2)
    # load the records with xmlid
    partner_tag_ids2.save()
    partner_tag_ids2.unlink()

    data_ids = odoo.search_ir_model_data([('module', '=', 'base')])
    models = data_ids.mapped('model')
    logger.info('Models : %s', ', '.join(models))

    partner_ids = odoo.model('res.partner').search([], fields=['country_id', 'name'])
    country_codes = partner_ids.mapped('country_id.code')
    logger.info('Country codes : %s', ', '.join(country_codes))

    data_ids = odoo.search_ir_model_data([('module', '=', 'base')])
    if data_ids:
        models = data_ids.mapped('model')
        for model in models:
            model_data_ids = data_ids.filtered(model=model)
            record_ids = odoo.model(model).read(model_data_ids.mapped('res_id'))
            # logger.info(record_ids)
            break

    data_users = [{'id': f'external_config.user_test_01',
                   'name': 'Lastname Firstname TEST1', 'login': 'test1@test.fr',
                   'title.id': 1, 'company_ids.id': [1, 3], 'active': True},
                  {'id': f'external_config.user_test_02',
                   'name': 'Lastname Firstname TEST2', 'login': 'test2@test.fr',
                   'title.id': 1, 'company_ids.id': [1, 3], 'active': True}]
    odoo.model('res.users').load_batch(data_users)

if __name__ == '__main__':
    test_local()