import logging
import time
from s6r_odoo import OdooConnection

logging.basicConfig()
logger = logging.getLogger("test")
odoo = OdooConnection(url='http://odoo_test.localhost',
                          dbname='odoo_test',
                          user='admin',
                          password='admin', debug_xmlrpc=True, logger=logger)

partner_fields = odoo.execute_odoo('res.partner', 'fields_get', [['name'], None])

country_fields = odoo.model('res.country').get_fields([])
country_required_fields = ', '.join(country_fields[key]['name'] for key in country_fields if country_fields[key]['required'])
logger.info('Country required fields : %s', country_required_fields)


#Script optimised to access to licence and category_id field
start_time = time.time()
module_ids = odoo.model('ir.module.module').search([('author', 'ilike', 'Odoo')],
                                                   fields=['display_name', 'category_id', 'license'],
                                                   order='create_date desc, name', limit=10000)
optimized_query_time = time.time() - start_time
start_time = time.time()
logger.info('Module categories : %s', ', '.join(set([module.category_id.name for module in module_ids])))
for module_id in module_ids:
    module_license = module_id.license if module_id['license'] else 'Unknown'
    # logger.info('Module %s : %s', module_id.display_name, module_id.license)
    continue
optimized_time = time.time() - start_time
logger.info("Optimised Script : %s seconds (first query : %s seconds)", optimized_time, optimized_query_time)


# Script NOT optimised to access to licence and category_id field
start_time = time.time()
module_ids = odoo.model('ir.module.module').search([('author', 'ilike', 'Odoo')],
                                                   fields=['display_name'],
                                                   order='create_date desc, name', limit=10)
not_optimized_query_time = time.time() - start_time
start_time = time.time()
logger.info('Module categories : %s', ', '.join(set([module.category_id.name for module in module_ids])))
for module_id in filter(lambda x: x.category_id.name != 'Scalizer', module_ids): # module_ids:
    module_license = module_id.license if module_id['license'] else 'Unknown'
    logger.info('Module %s : %s', module_id.display_name, module_id.license)
    continue
not_optimized_time = time.time() - start_time
logger.info("NOT Optimised Script : %s seconds (first query : %s seconds)", not_optimized_time, not_optimized_query_time)

# XMLIDs Tests
logger.info('Module XMLIDs : %s', odoo.get_xmlid_dict('ir.module.module'))

object_id = odoo.get_ref('base.module_account')
logger.info('base.module_account get_ref --> id : %s', object_id)
module_account_lazy = odoo.model('ir.module.module').read(object_id, ['name', 'description'])

logger.info('Module (LAZY): %s\nCategory: %s\nDescription: %s\n',
            module_account_lazy['name'],
            module_account_lazy['category_id'].name,
            module_account_lazy['description'])

object_reference = odoo.get_object_reference('base.module_account')
logger.info("base.module_account get_object_reference --> ['ir.module.module', id] : %s", object_reference)
module_account = odoo.ref('base.module_account')
msg = 'base.module_account ref --> OdooRecord :\nModule: %s (%s)\nDescription: %s\nXMLID: %s'
logger.info(msg, module_account.display_name,
            module_account.name,
            module_account.description,
            odoo.get_xml_id_from_id('ir.module.module', module_account.id))

email = 'john@example.com'
partner_id = odoo.ref('base.main_partner')
partner_id.email = email
partner_id.save()
if partner_id.email != email:
    raise Exception('Email %s not updated' % email)
email = 'sophie@example.com'
partner_id.write({'email': email})
if partner_id.email != email:
    raise Exception('Email %s not updated' % email)

partner_id2 = odoo.model('res.partner').read(partner_id.id)
if email in partner_id2.email_formatted:
    partner_id.write({'email': 'test@example.com'})
    raise Exception('Cache not used with read')

partner_id2 = odoo.ref('base.main_partner')
if email in partner_id2.email_formatted:
    partner_id.write({'email': 'test@example.com'})
    raise Exception('Cache not used with ref')

partner_id.write({'email': 'test@example.com'})

logger.info('Query count : %s', odoo.query_count)
for method in odoo.method_count:
    logger.info('Count %s : %s', method, odoo.method_count[method])
