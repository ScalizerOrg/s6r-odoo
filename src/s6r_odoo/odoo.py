# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
from datetime import datetime
import logging
import ssl
import os
import sys
import xmlrpc.client
from pprint import pformat

import requests
from bs4 import BeautifulSoup

from .model import OdooModel

METHODE_MAPPING = {
    15: [('get_object_reference', 'check_object_reference')]
}


class OdooConnection:
    _context = {'lang': 'fr_FR', 'noupdate': True}

    def __init__(self, url, dbname, user, password, version=15.0, http_user=None, http_password=None, createdb=False,
                 debug_xmlrpc=False):
        self.logger = logging.getLogger("Odoo Connection".ljust(15))
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
        self._debug_xmlrpc = debug_xmlrpc
        # noinspection PyProtectedMember,PyUnresolvedReferences
        self._insecure_context = ssl._create_unverified_context()
        self._compute_url()
        if createdb:
            self._create_db()
        self._prepare_connection()

    @property
    def context(self):
        return self._context

    def model(self, model_name):
        return OdooModel(self, model_name)

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

    def execute_odoo(self, *args, no_raise=False):
        self.logger.debug("*" * 50)
        self.logger.debug("Execute odoo :")
        self.logger.debug("\t Model : %s" % (args[0]))
        self.logger.debug("\t Method : %s" % (args[1]))
        self.logger.debug("\t " + "%s " * (len(args) - 2) % args[2:])
        self.logger.debug("*" * 50)
        try:
            res = self.object.execute_kw(self._dbname, self.uid, self._password, *args)
            return res
        except Exception as e:
            if no_raise:
                pass
            else:
                self.logger.error(pformat(args))
                self.logger.error(e)
                raise e

    def get_ref(self, external_id):
        res = \
            self.execute_odoo('ir.model.data', self._get_xmlrpc_method('get_object_reference'), external_id.split('.'))[
                1]
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

    def get_id_from_xml_id(self, xml_id, no_raise=False):
        if '.' not in xml_id:
            xml_id = "external_config." + xml_id
        try:
            object_reference = self._get_xmlrpc_method('get_object_reference')
            res = self.execute_odoo('ir.model.data', object_reference, xml_id.split('.'), no_raise=no_raise)
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

    def get_xml_id_from_id(self, model, res_id):
        try:
            domain = [('model', '=', model), ('res_id', '=', res_id)]
            res = self.execute_odoo('ir.model.data', 'search_read', [domain, ['module', 'name'], 0, 0, "id"],
                                    {'context': self._context})
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

    def read(self, model, ids, fields, context=None):
        return self.execute_odoo(model, 'read', [ids, fields],
                                 {'context': context or self._context})

    def read_group(self, model, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True, context=None):
        res = self.execute_odoo(model, 'read_group', [domain, fields, groupby, offset, limit, orderby, lazy],
                                {'context': context or self._context})
        return res

    def search(self, model, domain=[], fields=[], order="", offset=0, limit=0, context=None):
        params = [domain, fields, offset, limit, order]
        res = self.execute_odoo(model, 'search_read', params, {'context': context or self._context})
        return res

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
            self.logger.error("%s : %s" % (message['record'], message['message']))
        return res

    def load_batch(self, model, datas, ignore_fields=[], batch_size=100, skip_line=0, context=None):
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
        for cc, data in enumerate(datas):
            if len(load_datas[-1]) >= batch_size:
                load_datas.append([])
            load_datas[-1].append([data[i] for i in load_keys])

        cc = 0
        for load_data in load_datas:
            start_batch = datetime.now()
            self.logger.info("\t\t* %s : %s-%s/%s" % (model, skip_line + cc, skip_line + cc + len(load_data), skip_line + cc_max))
            cc += len(load_data)
            res = self.load(model, load_keys, load_data, context=context)
            for message in res['messages']:
                if message.get('type') in ['warning', 'error']:
                    if message.get('record'):
                        self.logger.error("record : %s" % (message['record']))
                    if message.get('message'):
                        self.logger.error("message : %s" % (message['message']))
                    raise Exception(message['message'])
                else:
                    self.logger.info(message)
            stop_batch = datetime.now()
            self.logger.info("\t\t\tBatch time %s ( %sms per object)" % (
                stop_batch - start_batch, ((stop_batch - start_batch) / len(load_data)).microseconds / 1000))
        stop = datetime.now()
        self.logger.info("\t\t\tTotal time %s" % (stop - start))

    def create(self, model, values, context=None):
        params = [values] if isinstance(values, dict) else values
        res = self.execute_odoo(model, 'create', params,  {'context': context or self._context})
        return res

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

    def get_id_ref_dict(self, model):
        model_datas = self.search('ir.model.data', [('model', '=', model)])
        return dict([(data['res_id'], '%s.%s' % (data['module'], data['name'])) for data in model_datas])

    def get_xmlid_dict(self, model):
        model_datas = self.search('ir.model.data', [('model', '=', model)])
        return dict([('%s.%s' % (data['module'], data['name']), data['res_id']) for data in model_datas])

    def get_fields(self, model, fields=[]):
        return self.execute_odoo(model, 'fields_get', [], {'allfields': fields, 'attributes': ['string', 'help', 'type']})