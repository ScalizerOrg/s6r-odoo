# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

class OdooModel(object):
    def __init__(self, odoo, model_name):
        self.model_name = model_name
        self.odoo = odoo

    def __str__(self):
        return self.model_name

    def __repr__(self):
        return self.model_name

    def execute(self, *args, no_raise=False):
        return self.odoo.execute_odoo(self.model_name, args[0], args[1:], no_raise=no_raise)

    def search_get_id(self, domain):
        return self.odoo.get_search_id(self.model_name, domain)

    def get_xml_id_from_id(self, xml_id):
        return self.odoo.get_xml_id_from_id(self.model_name, xml_id)

    def read(self, ids, fields, context=None):
        return self.odoo.read(self.model_name, ids, fields, context)

    def read_search(self, domain, context=None):
        return self.odoo.read_search(self.model_name, domain, context)

    def search_count(self, domain, context=None):
        return self.odoo.search_count(self.model_name, domain, context)

    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True, context=None):
        return self.odoo.read_group(self.model_name, domain, fields, groupby, offset, limit, orderby, lazy, context)

    def search(self, domain=[], fields=[], order="", offset=0, limit=0, context=None):
        return self.odoo.search(self.model_name, domain, fields, order, offset, limit, context)

    def search_ids(self, domain=[], fields=[], order="", offset=0, limit=0, context=None):
        return self.odoo.search_ids(self.model_name, domain, fields, order, offset, limit, context)

    def get_record(self, rec_id, context=None):
        return self.odoo.get_record(self.model_name, rec_id, context)

    def default_get(self, field):
        return self.odoo.default_get(self.model_name, field)

    def load(self, load_keys, load_data, context=None):
        return self.odoo.load(self.model_name, load_keys, load_data, context)

    def load_batch(self, data, ignore_fields=[], batch_size=100, skip_line=0, context=None):
        return self.odoo.load_batch(self.model_name, data, ignore_fields, batch_size, skip_line, context)

    def write(self, ids, values, context=None):
        return self.odoo.write(self.model_name, ids, values, context)

    def create(self, values, context=None):
        return self.odoo.create(self.model_name, values, context)

    def unlink(self, values, context=None):
        return self.odoo.unlink(self.model_name, values, context)

    def unlink_domain(self, domain, context=None):
        return self.odoo.unlink_domain(self.model_name, domain, context)

    def create_attachment(self, name, datas, res_id=False, context=None):
        return self.odoo.create_attachment(name, datas, self.model_name, res_id, context)

    def create_attachment_from_local_file(self, file_path, res_id=False, name=False, encode=False, context=None):
        return self.odoo.create_attachment_from_local_file(file_path, self.model_name, res_id, name, encode, context)

    def get_id_ref_dict(self):
        return self.odoo.get_id_ref_dict(self.model_name)

    def get_xmlid_dict(self):
        return self.odoo.get_xmlid_dict(self.model_name)

    def get_fields(self, fields):
        return self.get_fields(self.model_name, fields)