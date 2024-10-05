import logging
import time
from s6r_odoo import OdooConnection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


odoo = OdooConnection(url='http://odoo_test.localhost',
                          dbname='odoo_test',
                          user='admin',
                          password='admin', debug_xmlrpc=True, logger=logger)

res = odoo.execute_odoo('res.partner', 'fields_get', [['name'], None])




fields = odoo.model('res.country').get_fields([])

print('Partner required fields : %s' % ', '.join(fields[key]['name'] for key in fields if fields[key]['required']))


#Script optimised to access to licence and category_id field
start_time = time.time()
module_ids = odoo.model('ir.module.module').search([('author', 'ilike', 'Odoo')],
                                                   fields=['display_name', 'category_id', 'license'],
                                                   order='create_date desc, name', limit=10000)
optimized_query_time = time.time() - start_time
start_time = time.time()
print('Module categories : %s' % ', '.join(set([module.category_id.name for module in module_ids])))
for module_id in module_ids:
    module_license = module_id.license if module_id['license'] else 'Unknown'
    # print('Module %s : %s' % (module_id.display_name, module_id.license))
    continue
optimized_time = time.time() - start_time
print("Optimised Script : %s seconds (first query : %s seconds)" % (optimized_time, optimized_query_time))


# Script NOT optimised to access to licence and category_id field
start_time = time.time()
module_ids = odoo.model('ir.module.module').search([('author', 'ilike', 'Odoo')],
                                                   fields=['display_name'],
                                                   order='create_date desc, name', limit=10)
not_optimized_query_time = time.time() - start_time
start_time = time.time()
print('Module categories : %s' % ', '.join(set([module.category_id.name for module in module_ids])))
for module_id in filter(lambda x: x.category_id.name != 'Scalizer', module_ids): # module_ids:
    module_license = module_id.license if module_id['license'] else 'Unknown'
    # print('Module %s : %s' % (module_id.display_name, module_id.license))
    continue
not_optimized_time = time.time() - start_time
print("NOT Optimised Script : %s seconds (first query : %s seconds)" % (not_optimized_time, not_optimized_query_time))

# XMLIDs Tests
print('Module XMLIDs : %s' % odoo.get_xmlid_dict('ir.module.module'))

object_id = odoo.get_ref('base.module_account')
print('base.module_account get_ref --> id : %s' % object_id)
module_account_lazy = odoo.model('ir.module.module').read(object_id, ['name', 'description'])

print('Module (LAZY): %s\nCategory: %s\nDescription: %s\n' % (module_account_lazy['name'],
                                                       module_account_lazy['category_id'].name,
                                                       module_account_lazy['description']))

object_reference = odoo.get_object_reference('base.module_account')
print("base.module_account get_object_reference --> ['ir.module.module', id] : %s" % object_reference)
module_account = odoo.ref('base.module_account')
msg = 'base.module_account ref --> OdooRecord :\nModule: {} ({})\nDescription: {}\nXMLID: {}'
print(msg.format(module_account.display_name,
                 module_account.name,
                 module_account.description,
                 odoo.get_xml_id_from_id('ir.module.module', module_account.id)))

partner_id = odoo.ref('base.main_partner')
partner_id.email = 'john@example.com'
partner_id.save()
partner_id.write({'email': 'sophie@example.com'})

partner_id2 = odoo.ref('base.main_partner')
print(partner_id2.email)


# print(odoo_cli.search('ir.module.module', [('name', '=', 'base')])[0]['installed_version'])
# print(odoo_cli.model('product.template').search_count([]))
# print(odoo_cli.execute_odoo('ir.module.module', 'search', [[('name', '=', 'account'), ('state', '=', 'installed')]]))
# print(odoo_cli.model('ir.module.module').search([('name', '=', 'account'), ('state', '=', 'installed')]))
# print(odoo_cli.model('ir.module.module').search([('name', '=', 'account'), ('state', '=', 'installed')], fields=['id']))
# print(odoo_cli.model('ir.module.module').execute('search', [('name', '=', 'account'), ('state', '=', 'installed')]))
#
# print(m_order.execute('action_preview_sale_order', [5]))
# print(m_order.execute('read_group', [], ['amount_total'], ['date_order']))
# print(m_order.read_group([], ['amount_total'], ['date_order']))
# # print(m_order.read_group([], ['amount_total'], ['date_order']))
# # print(odoo_cli.execute_odoo("sale.order", 'read_group', [[], ['amount_total'], ['date_order']]))
# # print(odoo_cli.read_group("sale.order", [], ['amount_total'], ['date_order']))
# # partners = odoo_cli.read_search('res.partner', [])
# # for partner in partners:
# #     print(partner)
