# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
from datetime import datetime
import logging
import time
import ssl
import os
import sys
import xmlrpc.client
from pprint import pformat

import requests
from bs4 import BeautifulSoup

from .file_import import FileImport
from .model import OdooModel
from .record import OdooRecord
from .record_set import OdooRecordSet

METHODE_MAPPING = {
    15: [('get_object_reference', 'check_object_reference')]
}


class OdooConnection:
    query_count = 0
    method_count = {}

    def __init__(self, url, dbname, user, password, version=15.0, http_user=None, http_password=None, createdb=False,
                 debug_xmlrpc=False, legacy=False, logger=None, **kwargs):
        self.logger = logger or logging.getLogger("Odoo Connection".ljust(15))
        if debug_xmlrpc:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self._url = url
        self._dbname = dbname
        self._user = user
        self._password = password
        self._http_user = http_user
        self._http_password = http_password
        self._version = version
        self._legacy = legacy
        self._debug_xmlrpc = debug_xmlrpc
        self._context = {'lang': kwargs.get('lang') or 'fr_FR', 'noupdate': True}
        # noinspection PyProtectedMember,PyUnresolvedReferences
        self._insecure_context = ssl._create_unverified_context()
        self._compute_url()
        if createdb:
            self._create_db()
        self._prepare_connection()
        self._models = {}
        self._file_import = FileImport(self)

    def __str__(self):
        return 'OdooConnection(%s)' % self._dbname

    def __repr__(self):
        return str(self)

    @property
    def context(self):
        return self._context

    def model(self, model_name):
        if model_name in self._models:
            return self._models[model_name]
        res = OdooModel(self, model_name)
        self._models[model_name] = res
        return res

    def _compute_url(self):
        if self._http_user or self._http_password:
            self._url = self._url.replace('https://', 'https://%s:%s@' % (self._http_user, self._http_password))

    def _get_xmlrpc_method(self, method):
        new_method = method
        for v in METHODE_MAPPING:
            if self._version >= v:
                for i in METHODE_MAPPING[v]:
                    if i[0] == method:
                        new_method = i[1]
        return new_method

    def init_logger(self, name='s6r-odoo', level='INFO'):
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(f'%(asctime)s - {name} - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        self.logger = root_logger

    def _create_db(self):
        post = {
            'master_pwd': "admin123",
            'name': self._dbname,
            'login': self._user,
            'password': self._password,
            'phone': '',
            'lang': 'fr_FR',
            'country_code': 'fr',
        }
        session = requests.Session()
        session.verify = False
        r = session.post(url=self._url + "/web/database/create", params=post)
        soup = BeautifulSoup(r.text, 'html.parser')
        alert = soup.find('div', attrs={"class": u"alert alert-danger"})
        if alert:
            self.logger.debug(self._url + "/web/database/create")
            self.logger.debug(post)
            self.logger.debug(alert.get_text())
            if "already exists" not in alert.text:
                raise Exception(alert.text)

    def _prepare_connection(self):
        self.logger.info("Prepare connection %s %s %s" % (self._url, self._dbname, self._user))
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self._url), allow_none=True,
                                                context=self._insecure_context)
        self.object = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self._url), allow_none=True,
                                                context=self._insecure_context)
        self.logger.info("==============")
        try:
            self.uid = self.common.authenticate(self._dbname, self._user, self._password, {})
        except xmlrpc.client.Fault as err:
            if 'FATAL:' in err.faultString:
                msg = err.faultString[err.faultString.find('FATAL:') + 6:].strip()
                self.logger.error(msg)
                raise ConnectionError(msg)
            raise err
        except xmlrpc.client.ProtocolError as err:
            msg = f'{err.url} {err.errmsg} ({err.errcode})'
            self.logger.error(msg)
            raise ConnectionError(msg)
        except Exception as err:
            self.logger.error(err)
            raise

        self.logger.debug('Connection uid : %s' % self.uid)
        if not self.uid:
            msg = f'Connection Error to {self._url} {self._dbname}. Check "{self._user}" username and password.'
            self.logger.error(msg)
            raise ConnectionError(msg)

    def reset_count(self):
        self.query_count = 0
        self.method_count = {}

    def query_counter_update(self, model, method):
        self.query_count += 1
        if method not in self.method_count:
            self.method_count[method] = {model: 1}
        else:
            if model not in self.method_count[method]:
                self.method_count[method][model] = 1
            else:
                self.method_count[method][model] += 1

    def execute_odoo(self, *args, no_raise=False, no_log=False, retry=0):
        model = args[0]
        method = args[1]
        self.query_counter_update(model, method)

        self.logger.debug("*" * 50)
        self.logger.debug("Execute odoo :")
        self.logger.debug("\t Model : %s" % model)
        self.logger.debug("\t Method : %s" % method)
        self.logger.debug("\t " + "%s " * (len(args) - 2) % args[2:])
        self.logger.debug("*" * 50)
        try:
            if retry:
                self._prepare_connection()
            res = self.object.execute_kw(self._dbname, self.uid, self._password, *args)
            return res
        except (ConnectionResetError, ConnectionError, xmlrpc.client.ProtocolError) as e:
            if not retry:
                self.logger.info("Retry #1 to connect to Odoo...")
                time.sleep(5)
                return self.execute_odoo(*args, no_raise=no_raise, no_log=no_log, retry=1)
            elif retry == 1:
                self.logger.info("Retry #2 to connect to Odoo...")
                time.sleep(10)
                return self.execute_odoo(*args, no_raise=no_raise, no_log=no_log, retry=2)
            else:
                self.logger.error("Max connection retry reached.", exc_info=True)
                if not no_raise:
                    raise

        except Exception as e:
            if no_raise:
                pass

            if not no_log:
                self.logger.error(pformat(args))
                if hasattr(e, 'faultString'):
                    self.logger.error(e.faultString)
                    if 'InterfaceError: cursor already closed' in e.faultString:
                        if retry > 5:
                            raise e
                        self.logger.info("Retry to connect to Odoo...")
                        time.sleep(5)
                        return self.execute_odoo(*args, no_raise=no_raise, no_log=no_log, retry=retry+1)
                else:
                    self.logger.error(e)
            if not no_raise:
                raise e

    def values_to_record(self, model_name, values, update_cache=True, resolve_xmlids=True):
        if isinstance(values, int):
            values = {'id': values}
        record = OdooRecord(self, self.model(model_name), values, resolve_xmlids=resolve_xmlids)
        if update_cache:
            self._models[model_name]._update_cache(record.id, values)
        return record

    def values_list_to_records(self, model_name, val_list, update_cache=True, resolve_xmlids=True):
        if val_list is None:
            val_list = []
        if self._legacy:
            return val_list
        records = [self.values_to_record(model_name, values, update_cache, resolve_xmlids) for values in val_list]
        return OdooRecordSet(records, model=self.model(model_name))

    def get_ref(self, external_id):
        object_ref = self.get_object_reference(external_id)
        res = object_ref[1] if object_ref else False
        self.logger.debug('Get ref %s > %s' % (external_id, res))
        return res

    def get_local_file(self, path, encode=False):
        if encode:
            with open(path, "rb") as f:
                res = f.read()
                res = base64.b64encode(res).decode("utf-8", "ignore")
        else:
            with open(path, "r") as f:
                res = f.read()
        return res

    def get_country(self, code):
        return self.execute_odoo('res.country', 'search', [[('code', '=', code)], 0, 1, "id", False],
                                 {'context': self._context})[0]

    def get_menu(self, website_id, url):
        return self.execute_odoo('website.menu', 'search',
                                 [[('website_id', '=', website_id), ('url', '=', url)], 0, 1, "id", False],
                                 {'context': self._context})[0]

    def get_search_id(self, model, domain):
        return self.execute_odoo(model, 'search', [domain, 0, 1, "id", False], {'context': self._context})[0]

    def search_ir_model_data(self, domain):
        return self.model('ir.model.data').search(domain,
                                                  fields=['module', 'name', 'model', 'res_id'],
                                                  order='id')

    def get_object_reference_legacy(self, xml_id, no_raise=False):
        object_reference = self._get_xmlrpc_method('get_object_reference')
        return self.execute_odoo('ir.model.data', object_reference, xml_id.split('.'), no_raise=no_raise)


    def get_object_reference(self, xml_id, no_raise=False, cache_only=False):
        if self._legacy:
            return self.get_object_reference_legacy(xml_id, no_raise=no_raise)

        ref = self._get_object_reference_cache(xml_id)
        if ref:
            return ref
        if cache_only:
            return
        module, name = xml_id.split('.')
        domain = [('module', '=', module), ('name', '=', name)]
        res = self.search_ir_model_data(domain)
        if res:
            ir_model_data_id = res[0]
            return [ir_model_data_id.model, ir_model_data_id.res_id]

    def get_id_from_xml_id(self, xml_id, no_raise=False, cache_only=False):
        if '.' not in xml_id:
            xml_id = "external_config." + xml_id
        try:
            res = self.get_object_reference(xml_id, no_raise=no_raise, cache_only=cache_only)
            return res[1] if res else False
        except xmlrpc.client.Fault as fault:
            if no_raise:
                pass
            raise ValueError(fault.faultString.strip().split('\n')[-1])
        except Exception as err:
            if no_raise:
                pass
            else:
                raise err

    def ref(self, ixml_id, no_raise=False, fields=None, no_cache=False):
        object_reference = self.get_object_reference(ixml_id, no_raise=no_raise)
        if len(object_reference) == 2:
            model, res_id = object_reference
            res = self.model(model).read(res_id, fields=fields, no_cache=no_cache)
            res._xmlid = ixml_id
            return res

    def get_xml_id_from_id(self, model, res_id, cache_only=False):
        cache_xmlid = self._get_xmlid_cache(model, res_id)
        if cache_xmlid:
            return cache_xmlid
        if cache_only:
            return
        try:
            domain = [('model', '=', model), ('res_id', '=', res_id)]
            res = self.search_ir_model_data(domain)
            if res:
                datas = res[0]
                return "%s.%s" % (datas['module'], datas['name'])
            else:
                raise ValueError('xml_id not found.')
        except Exception as err:
            raise err

    def write(self, model, ids, values, context=None):
        return self.execute_odoo(model, 'write', [ids, values],
                                 {'context': context or self._context})

    def set_active(self, is_active, model, domain, search_value_xml_id):
        if search_value_xml_id:
            object_id = self.get_id_from_xml_id(search_value_xml_id)
            domain = [(domain[0][0], domain[0][1], object_id)]
        object_ids = self.search_ids(model, domain, context=self._context)
        self.write(model, object_ids, {'active': is_active})

    def read_search(self, model, domain, context=None):
        res = self.execute_odoo(model, 'search_read', [domain],
                                {'context': context or self._context})
        return res

    def search_count(self, model, domain, context=None):
        res = self.execute_odoo(model, 'search_count', [domain],
                                {'context': context or self._context})
        return res

    def _read(self, model, ids, fields, context=None):
        param_ids = [ids] if isinstance(ids, int) else ids
        return self.execute_odoo(model, 'read', [param_ids, fields],
                                 {'context': context or self._context})

    def read(self, model, ids, fields, context=None):
        if ids and isinstance(ids, list) and isinstance(ids[0], str):
            ids = [self.get_ref(i) for i in ids]
        res =  self._read(model, ids, fields, context)
        return self.values_list_to_records(model, res)

    def read_group(self, model, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True, context=None):
        res = self.execute_odoo(model, 'read_group', [domain, fields, groupby, offset, limit, orderby, lazy],
                                {'context': context or self._context})
        return res

    def search(self, model, domain=[], fields=[], order="", offset=0, limit=0, context=None, **kwargs):
        if 'exclude_fields' in kwargs:
            exclude_fields = kwargs['exclude_fields']
            fields = [f for f in fields if f not in exclude_fields]
        if not fields:
            model_fields = self.get_fields(model)
            if len(model_fields) > 20:
                self.logger.warning(
                    f"You are trying to search and read {len(model_fields)} fields for model {model}"
                    "\nThis might slow down your script, consider using fields parameter.")
        params = [domain, fields, offset, limit, order]
        res = self.execute_odoo(model, 'search_read', params, {'context': context or self._context})
        if res and limit==1 and not self._legacy and not 'legacy' in kwargs:
            return self.values_list_to_records(model, res)[0]
        return self.values_list_to_records(model, res)

    def search_ids(self, model, domain=[], order="", offset=0, limit=0, context=None):
        params = [domain, offset, limit, order]
        res = self.execute_odoo(model, 'search', params, {'context': context or self._context})
        return res

    def get_record(self, model, rec_id, context=None):
        params = [[('id', '=', rec_id)]]
        res = self.execute_odoo(model, 'search_read', params,
                                {'context': context or self._context})
        if res:
            return res[0]

    def default_get(self, model, field):
        res = self.execute_odoo(model, 'default_get', [field])
        return res

    def load(self, model, load_keys, load_data, context):
        res = self.execute_odoo(model, 'load', [load_keys, load_data], {'context': context or self._context})
        for message in res['messages']:
            self.logger.error("%s : %s" % (message.get('record', False), message['message']))
        return res

    def prepare_load_batch_datas(self, datas):
        batch_keys = list(datas[0].keys())
        for i, values in enumerate(datas):
            for key in batch_keys:
                if key not in values:
                    self.logger.warning(f"Value for key {key} not found in line {i}")
                    values[key] = ''
                if key.endswith('.id') and isinstance(values.get(key), list):
                    values[key] = ','.join([str(v) for v in values.get(key)]) if values.get(key) else ''
                if key.endswith('.id') and isinstance(values.get(key), int):
                    values[key] = str(values.get(key))
                if isinstance(values[key], bool):
                    values[key] = '1' if values[key] else '0'
        return datas

    def load_batch(self, model, datas, batch_size=100, skip_line=0, context=None, **kwargs):
        ignore_fields = kwargs.get('ignore_fields', [])
        datas = datas[skip_line:]
        context = self.context | context if context else self.context
        if not datas:
            return
        cc_max = len(datas)
        start = datetime.now()

        load_keys = list(datas[0].keys())
        for field in ignore_fields:
            try:
                load_keys.remove(field)
            except ValueError:
                self.logger.warning(f"\"{field}\" field name not found in data keys")
        load_datas = [[]]
        datas = self.prepare_load_batch_datas(datas)
        for cc, data in enumerate(datas):
            if len(load_datas[-1]) >= batch_size:
                load_datas.append([])
            load_datas[-1].append([data[i] for i in load_keys])

        cc = 0
        res = {'ids': [], 'messages': []}
        for load_data in load_datas:
            start_batch = datetime.now()
            self.logger.info("\t\t* %s : %s-%s/%s" % (model, skip_line + cc, skip_line + cc + len(load_data), skip_line + cc_max))
            cc += len(load_data)
            load_res = self.load(model, load_keys, load_data, context=context)
            res['ids'].extend(load_res.get('ids', []) or [])
            messages = load_res.get('messages', [])
            res['messages'].extend(messages)
            for message in messages:
                if message.get('type') in ['warning', 'error']:
                    if message.get('record'):
                        self.logger.error("record : %s" % (message['record']))
                    if message.get('message'):
                        self.logger.error("message : %s" % (message['message']))
                else:
                    self.logger.info(message)
            stop_batch = datetime.now()
            self.logger.info("\t\t\tBatch time %s ( %sms per object)" % (
                stop_batch - start_batch, ((stop_batch - start_batch) / len(load_data)).microseconds / 1000))
        stop = datetime.now()
        self.logger.info("\t\t\tTotal time %s" % (stop - start))
        return res

    def create(self, model, values, context=None):
        if isinstance(values, dict):
            values = [values]
        res = self.execute_odoo(model, 'create', [values],  {'context': context or self._context})
        if isinstance(res, int):
            res = [res]
        res_values = [{'id': r} | values[i] for i, r in enumerate(res)]
        return self.values_list_to_records(model, res_values)

    def unlink(self, model, values, context=None):
        return self.execute_odoo(model, 'unlink', [values],  {'context': context or self._context})

    def unlink_domain(self, model, domain, context=None):
        values = self.search_ids(model, domain)
        return self.unlink(model, values, context)

    def create_attachment(self, name, datas, res_model, res_id=False, context=None):
        values = {
                    'name': name,
                    'datas': datas,
                    'res_model': res_model}
        if res_id:
            values['res_id'] = res_id
        return self.create('ir.attachment', values,  context)

    def create_attachment_from_local_file(self, file_path, res_model, res_id=False,
                                          name=False, encode=False, context=None):
        datas = self.get_local_file(file_path, encode)
        file_name = name or os.path.basename(file_path)
        return self.create_attachment(file_name, datas, res_model, res_id, context)

    def get_ir_model_data(self, model):
        return self.search('ir.model.data', [('model', '=', model)],
                    fields=['module', 'name', 'model', 'res_id'])

    def get_id_ref_dict(self, model):
        """
        Returns a dict with id as key and xmlid as value
        :param model: Model name
        :return: {894: 'base.module_account', ...}
        """
        model_datas = self.get_ir_model_data(model)
        return dict([(data.res_id, '%s.%s' % (data.module, data.name)) for data in model_datas])

    def get_xmlid_dict(self, model):
        """
        Returns a dict with xmlid as key and id as value
        :param model: Model name
        :return: {'base.module_account': 894, ...}
        """
        model_datas = self.get_ir_model_data(model)
        return dict([('%s.%s' % (data.module, data.name), data.res_id) for data in model_datas])

    def get_id_ref_list(self, model):
        """
        Returns a dict with record id as key and a xmlid list as value
        :param model: Model name
        :return: {'894': ['base.module_account', ...], ...}
        """
        xmlid_dict = self.get_xmlid_dict(model)
        return dict([(id, [xmlid for xmlid, res_id in xmlid_dict.items() if res_id == id]) for id in xmlid_dict.values()])

    def get_fields(self, model_name, fields=None, attributes=None):
        model = self.model(model_name)
        if model._fields and not fields and not attributes:
            return model._fields
        if model._fields and fields:
            return {f:model._fields[f] for f in fields if f in model._fields}
        params = [fields or []]
        if attributes:
            params.append(attributes)

        res_fields = self.execute_odoo(model_name, 'fields_get', params)
        if not fields and model and not model._fields_loaded:
            model._fields = res_fields
        return res_fields

    def _get_xmlid_cache(self, model_name, res_id):
        if not 'ir.model.data' in self._models:
            return
        cache = self._get_model_cache('ir.model.data')
        ir_model_datas = list(filter(lambda x: x['model'] == model_name and x['res_id'] == res_id, cache))
        if ir_model_datas:
            return '{0}.{1}'.format(ir_model_datas[0]['module'], ir_model_datas[0]['name'])

    def _get_object_reference_cache(self, xml_id):
        if not 'ir.model.data' in self._models:
            return
        module, name = xml_id.split('.')
        cache = self._get_model_cache('ir.model.data')
        ir_model_datas = list(filter(lambda x: x['module'] == module and x['name'] == name, cache))
        if ir_model_datas:
            return [ir_model_datas[0]['model'], ir_model_datas[0]['res_id']]

    def _get_model_cache(self, model_name):
        cache = self.model(model_name)._cache
        return [cache[res_id] for res_id in cache.keys()]

    def clear_cache(self):
        for model in self._models:
            self.model(model)._cache = {}

    def print_query_count(self):
        self.logger.info('Query count : %s', self.query_count)
        for method in self.method_count:
            self.logger.info('Method Count %s : %s', method, self.method_count[method])

    def get_method_count(self, method, model=None):
        if model:
            method_values = self.method_count.get(method, {})
            if method_values:
                return method_values.get(model, 0)
            else:
                return sum(method_values.values())
        return 0

    def import_csv(self, file_path, model, **kwargs):
        return self._file_import.import_csv(file_path, model, **kwargs)

    def import_xls(self, file_path, model, **kwargs):
        return self._file_import.import_xls(file_path, model, **kwargs)

    def import_xlsx(self, file_path, model, **kwargs):
        return self._file_import.import_xlsx(file_path, model, **kwargs)