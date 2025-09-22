# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


class OdooModel(object):

    _fields_loaded = False
    _fields = {}
    _cache = {}
    _xmlid_cache = {}

    def __init__(self, odoo, model_name):
        self.model_name = model_name
        self._odoo = odoo
        self._cache = {}
        self._fields = {}
        self._xmlid_cache = {}

    def __str__(self):
        return self.model_name or ''

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.model_name)

    def __eq__(self, other):
        return self.model_name == other.model_name

    def _update_cache(self,record_id, values):
        if record_id:
            self._cache[record_id] = values

    def values_to_record(self, values, update_cache=True):
        if update_cache and 'id' in values and isinstance(values['id'], int):
            self._update_cache(values['id'], values)
        return self._odoo.values_to_record(self.model_name, values, update_cache=False)

    def values_list_to_records(self, val_list, update_cache=True, resolve_xmlids=True):
        return self._odoo.values_list_to_records(self.model_name, val_list,
                                                 update_cache=update_cache,
                                                 resolve_xmlids=resolve_xmlids)

    def _get_cache(self, record_id):
        if record_id in self._cache:
            return self.values_to_record(self._cache.get(record_id), update_cache=False)

    def execute(self, model_method,  *args, no_raise=False):
        return self._odoo.execute_odoo(self.model_name, model_method, args, no_raise=no_raise)

    def search_get_id(self, domain):
        return self._odoo.get_search_id(self.model_name, domain)

    def get_xml_id_from_id(self, xml_id, cache_only=False):
        return self._odoo.get_xml_id_from_id(self.model_name, xml_id, cache_only=cache_only)

    def read(self, ids, fields=None, context=None, no_cache=False):
        if not ids:
            return []
        if not fields:
            fields = self.get_fields_list()
            if len(fields) > 20:
                self._odoo.logger.warning(
                    f"You are trying to read {len(fields)} fields for model {self.model_name} id: {str(ids)}"
                    "\nThis might slow down your script, consider using fields parameter.")
        if isinstance(ids, int):
            if not no_cache:
                cache_record = self._get_cache(ids)
                if cache_record:
                    return cache_record

            record = self._odoo.read(self.model_name, [ids], fields, context)[0]
            if record:
                return record

        return self._odoo.read(self.model_name, ids, fields, context)

    def _read(self, ids, fields=None, context=None, no_cache=False):
        return self._odoo._read(self.model_name, ids, fields, context)

    def read_search(self, domain, context=None):
        return self._odoo.read_search(self.model_name, domain, context)

    def search_count(self, domain, context=None):
        return self._odoo.search_count(self.model_name, domain, context)

    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True, context=None):
        return self._odoo.read_group(self.model_name, domain, fields, groupby, offset, limit, orderby, lazy, context)

    def search(self, domain=[], fields=[], order="", offset=0, limit=0, context=None, **kwargs):
        return self._odoo.search(self.model_name, domain, fields, order, offset, limit, context, **kwargs)

    def search_ids(self, domain=[], fields=[], order="", offset=0, limit=0, context=None):
        return self._odoo.search_ids(self.model_name, domain, fields, order, offset, limit, context)

    def get_record(self, rec_id, context=None):
        return self._odoo.get_record(self.model_name, rec_id, context)

    def default_get(self, field):
        return self._odoo.default_get(self.model_name, field)

    def load(self, load_keys, load_data, context=None):
        return self._odoo.load(self.model_name, load_keys, load_data, context)

    def check_load_batch_data(self, data):
        if not data:
            return
        header = set(data[0].keys())
        for values in data:
            values_keys = set(values.keys())
            if values_keys != header:
                missing_keys = header - values_keys
                raise ValueError("All records must have the same keys."
                                 " %s not present in the first record." % ', '.join(missing_keys))

    def load_batch(self, data, batch_size=100, skip_line=0, context=None, **kwargs):
        self.check_load_batch_data(data)
        return self._odoo.load_batch(self.model_name, data, batch_size, skip_line, context, **kwargs)

    def write(self, ids, values, context=None):
        return self._odoo.write(self.model_name, ids, values, context)

    def create(self, values, context=None):
        return self._odoo.create(self.model_name, values, context)

    def unlink(self, values, context=None):
        return self._odoo.unlink(self.model_name, values, context)

    def unlink_domain(self, domain, context=None):
        return self._odoo.unlink_domain(self.model_name, domain, context)

    def create_attachment(self, name, datas, res_id=False, context=None):
        return self._odoo.create_attachment(name, datas, self.model_name, res_id, context)

    def create_attachment_from_local_file(self, file_path, res_id=False, name=False, encode=False, context=None):
        return self._odoo.create_attachment_from_local_file(file_path, self.model_name, res_id, name, encode, context)

    def get_id_ref_dict(self):
        return self._odoo.get_id_ref_dict(self.model_name)

    def get_xmlid_dict(self):
        return self._odoo.get_xmlid_dict(self.model_name)

    def get_id_ref_list(self):
        return self._odoo.get_id_ref_list(self.model_name)

    def get_fields(self, fields=None, attributes=None):
        return self._odoo.get_fields(self.model_name, fields, attributes)

    def load_fields_description(self):
        if not self._fields_loaded and self.model_name:
            self._fields = self.get_fields()
            self._fields_loaded = True

    def load_field_description(self, field):
        if field in self._fields:
            return self._fields[field]
        field_desc = self.get_fields([field])
        self._fields.update(field_desc)
        return field_desc[field]

    def get_fields_list(self):
        if not self._fields_loaded:
            self.load_fields_description()
        return list(self._fields.keys())

    def get_ir_model_data(self):
        ir_model_datas = self._odoo.get_ir_model_data(self.model_name)
        self._xmlid_cache = ir_model_datas
        return ir_model_datas

    def _find_id_in_xmlid_cache(self, xml_id):
        module, name = xml_id.split('.')
        ir_model_datas = list(filter(lambda x: x.module == module and x.name == name, self._xmlid_cache))
        if ir_model_datas:
            return ir_model_datas[0].res_id

    def _find_ref_in_xmlid_cache(self, res_id):
        ir_model_datas = list(filter(lambda x: x.res_id == res_id, self._xmlid_cache))
        if ir_model_datas:
            return '{0}.{1}'.format(ir_model_datas[0].module, ir_model_datas[0].name)

    def get_field(self, field):
        if not self._fields_loaded and self.model_name:
            self.load_fields_description()
        if field in self._fields:
            return self._fields[field]

