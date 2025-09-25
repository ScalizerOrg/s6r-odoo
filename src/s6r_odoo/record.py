# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json
from .model import OdooModel


class OdooJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for OdooRecord and OdooRecordSet"""

    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if isinstance(obj, (list, tuple)) and hasattr(obj, 'ids'):  # Handle OdooRecordSet
            return [record.to_dict() if hasattr(record, 'to_dict') else dict(record) for record in obj]
        return super().default(obj)


# Monkey patch json.dumps to use our custom encoder by default
_original_dumps = json.dumps


def dumps(*args, **kwargs):
    if 'cls' not in kwargs:
        kwargs['cls'] = OdooJSONEncoder
    return _original_dumps(*args, **kwargs)


json.dumps = dumps


class OdooRecord(object):
    _odoo = None
    _model = None
    _field = ''
    _parent_model = None
    _xmlid = ''

    _updated_values = {}
    _initialized_fields = []

    def __init__(self, odoo, model, values: dict, field='', parent_model=None, **kwargs):
        self._values = {}
        self._updated_values = {}
        self._initialized_fields = []
        self._odoo = odoo
        self.id = False
        if model:
            self._model = model
            self._odoo = self._model._odoo
        if field:
            self._field = field
        if parent_model:
            self._parent_model = parent_model

        self.set_values(values, update_cache=False, resolve_xmlids=kwargs.get('resolve_xmlids', True))

    def __str__(self):
        if self._model:
            if hasattr(self, 'id') and self.id:
                return "%s(%s)" % (self._model, self.id)
            if 'name' in self._values:
                return "%s(%s)" % (self._model, self.name)
            elif self._xmlid:
                return "%s(%s)" % (self._model, self._xmlid)
        elif self._field:
            if hasattr(self, 'id'):
                return "%s(%s)" % (self._field, self.id)
            if hasattr(self, 'name'):
                return "%s(%s)" % (self._field, self.name)
        return str(self._values)

    def __repr__(self):
        return str(self)

    def __iter__(self):
        """Support for dict() conversion by yielding key-value pairs"""
        for key in self.get_attributes():
            yield key, self.__dict__[key]

    def get_attributes(self):
        for key in list(self.__dict__.keys()):
            if key.startswith('_'):
                continue
            yield key

    def __getitem__(self, key):
        if isinstance(key, str):
            return getattr(self, key)

    def get(self, key, default=None):
        if key in list(self.__dict__.keys()):
            return getattr(self, key)
        return default

    def to_dict(self):
        """Convert the record to a dictionary with JSON-serializable values"""
        result = {}
        for key in self.get_attributes():
            value = getattr(self, key)
            if isinstance(value, OdooRecord):
                result[key] = value.to_dict()
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            elif isinstance(value, dict):
                result[key] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                result[key] = [
                    item.to_dict() if isinstance(item, OdooRecord) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def __bool__(self):
        if hasattr(self, 'id') and self._model:
            return bool(self.id)
        else:
            return any([bool(getattr(self, k)) for k in list(self.__dict__.keys())])

    def __getattribute__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        if not super().__getattribute__('_model') and name in super().__getattribute__('_values'):
            return super().__getattribute__(name)
        if name not in self._values and self._model:
            if not self._model._fields_loaded:
                self._model.load_fields_description()
            if name in self._model._fields:
                res = self.read([name])
            else:
                res = super().__getattribute__(name)
        else:
            res = super().__getattribute__(name)
        if isinstance(res, dict):
            return OdooRecord(self._odoo, None, res)
        if res and isinstance(res, list) and not isinstance(res[0], OdooRecord):
            return self._odoo.values_list_to_records(None, res)
        return res

    def __setattr__(self, name, value):
        if name.startswith('_') or name == 'id':
            return super().__setattr__(name, value)
        if name not in self._values and self._model:
            if not self._model._fields_loaded:
                self._model.load_fields_description()
        if name in self._values and name in self._initialized_fields and value != self._values[name]:
            self._updated_values[name] = value
            return super().__setattr__(name, value)
        if name in self._values and name not in self._initialized_fields:
            self._updated_values[name] = value
            res = super().__setattr__(name, value)
            self._initialized_fields.append(name)
            return res
        return super().__setattr__(name, value)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            return self.__setattr__(key, value)
        return super().__setitem__(key, value)

    def __hash__(self):
        return hash((self.id, self._model))

    def __eq__(self, other):
        if hasattr(other, 'id') and hasattr(other, '_model'):
            return self.id == other.id and self._model == other._model
        return super().__eq__(other)

    @property
    def _read_fields(self):
        return [k for k in self.__dict__.keys() if not k.startswith('_')]

    def _update_cache(self):
        if self._model:
            self._model._update_cache(self._values['id'], self._values)

    def set_values(self, values, update_cache=True, resolve_xmlids=True):
        values = values.copy()
        self._values.update(values)
        self._handle_id_and_xmlid(values)
        if self._model and update_cache:
            self._update_cache()
        self._process_related_values(values, resolve_xmlids)

    def _handle_id_and_xmlid(self, values):
        if not values.get('id', False):
            self._updated_values = values
        if '/id' in values:
            self._xmlid = values.pop('/id', None)
        if 'id' in values and isinstance(values['id'], str):
            self._xmlid = values.pop('id', None)

    def _process_related_values(self, values, resolve_xmlids=True):
        value_type = 'id'
        for key, value in values.items():
            if '.' in key:
                field_name = key.split('.')[0]
            elif '/' in key:
                value_type = 'xmlid'
                field_name = key.split('/')[0]
            else:
                field_name = key

            if self._model:
                field = self._model.get_field(field_name)
            else:
                field = None

            if field and isinstance(value, list) and len(value) == 2 and isinstance(value[0], int) and isinstance(
                    value[1], str):
                self._handle_relation_list(field_name, value, field)
            elif not field:
                if isinstance(value, list):
                    if len(value) == 2 and isinstance(value[0], int) and isinstance(value[1], str):
                        value = OdooRecord(self._odoo, None, {'id': value[0], 'name': value[1]})
                elif isinstance(value, dict):
                    value = OdooRecord(self._odoo, None, value)
                super().__setattr__(key, value)
            elif field.get('type') == 'many2many' and key.endswith('id') or key.endswith('ids'):
                self._values.pop(key, None)
                self._handle_relation_many2many_ids(field_name, value, value_type, resolve_xmlids)
            elif key.endswith('/id') and isinstance(value, str):
                if resolve_xmlids:
                    self._values.pop(key, None)
                    self._handle_relation_xmlid(field_name, value, resolve_xmlids)
            elif key.endswith('.id') and isinstance(value, int):
                self._handle_relation_id(field_name, value)
            elif isinstance(value, dict):
                value = OdooRecord(self._odoo, None, value)
                super().__setattr__(key, value)
            else:
                try:
                    super().__setattr__(key, value)
                except Exception as e:
                    self.logger.error(e)

    def _handle_relation_list(self, key, value, field=False):
        field_name = key
        if not field or not field.get('relation'):
            return
        relation = field.get('relation')
        model = OdooModel(self._odoo, relation)
        if field.get('type') == 'many2one':
            record = OdooRecord(self._odoo, model, {'id': value[0], 'name': value[1]}, field_name, self._model)
        else:
            record = self._odoo.values_list_to_records(relation, [{'id': val} for val in value])
        super().__setattr__(key, record)

    def _handle_relation_many2many_ids(self, field_name, value, value_type, resolve_xmlids=True):
        if isinstance(value, str):
            value = value.split(',')
        if value_type == 'id':
            value = [int(val) for val in value]
        if value_type == 'xmlid' and resolve_xmlids:
            value = [self._odoo.get_ref(val) for val in value]
        field = self._model.get_field(field_name)
        if not field or not field.get('relation'):
            return
        relation = field.get('relation')
        record = self._odoo.values_list_to_records(relation, [{'id': val} for val in value])
        super().__setattr__(field_name, record)

    def _handle_relation_xmlid(self, field_name, value, resolve_xmlids):
        field = self._model.get_field(field_name)
        if not field.get('relation'):
            return
        if resolve_xmlids:
            res_id = self._odoo.get_ref(value)
        else:
            res_id = value

        model = OdooModel(self._odoo, field.get('relation'))
        record = OdooRecord(self._odoo, model, {'id': res_id}, field_name, self._model)
        record._xmlid = value
        super().__setattr__(field_name, record)
        if resolve_xmlids:
            self._values[f'{field_name}.id'] = record.id
        else:
            self._values[f'{field_name}/id'] = record._xmlid

    def _handle_relation_id(self, field_name, value):
        field = self._model.get_field(field_name)
        if not field.get('relation'):
            return
        model = OdooModel(self._odoo, field.get('relation'))
        record = OdooRecord(self._odoo, model, {'id': value}, field_name, self._model)
        super().__setattr__(field_name, record)
        self._values[f'{field_name}.id'] = record.id

    def read(self, fields=None, no_cache=False):
        if not self._model._fields_loaded:
            self._model.load_fields_description()
        if self.id in self._model._cache and not no_cache:
            res = self._model._cache[self.id]
            # check if all fields are in res dict
            if any(field not in res for field in fields):
                res.update(self._read(fields))

            self.set_values(res)
        else:
            if not fields:
                fields = self._model.get_fields_list()
            res = self._read(fields)
            if res:
                self.set_values(res)

    def _read(self, fields):
        res = self._model._read(self.id, fields)
        if res:
            return res[0]

    def save(self):
        values = self.get_update_values()
        if self._xmlid:
            res = self._model.load(list(values.keys()), [list(values.values())])
            if res.get('ids'):
                self.id = res.get('ids')[0]
            return
        if self.id:
            self._model.write(self.id, self._updated_values)
            self._updated_values = {}
        else:
            self.id = self._odoo.create(self._model.model_name, self._values)[0].id
            self._initialized_fields = list(self._values.keys())

    def write(self, values):
        self._model.write(self.id, values)
        self._values.update(values)
        self.__dict__.update(values)

    def refresh(self):
        self.read(self._initialized_fields, no_cache=True)

    def get_update_values(self):
        if '/id' in self._values:
            self._xmlid = self._values['/id']
            self._values.pop('/id', None)

        value_id = self._values.get('id', False)
        if isinstance(value_id, str):
            self._xmlid = value_id
            self.id = None
            self._values['id'] = None

        if self.id:
            values = self._updated_values
            values['.id'] = self.id
        else:
            values = self._values
            if self._xmlid:
                values['id'] = self._xmlid
            else:
                values['id'] = None

        return values

    def unlink(self):
        if self.id:
            self._model.unlink(self.id)
            self._model._cache.pop(self.id, None)
        self.id = None
