# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from .model import OdooModel

class OdooRecord(object):
    _odoo = None
    _model = None
    _field = ''
    _parent_model = None
    _xmlid = ''

    _updated_values = {}
    _initialized_fields = []

    def __init__(self, odoo, model, values: dict, field='', parent_model=None):
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

        self.set_values(values, update_cache=False)

    def __str__(self):
        if self._model:
            if hasattr(self, 'id'):
                return "%s(%s)" % (self._model, self.id)
            if hasattr(self, 'name'):
                return "%s(%s)" % (self._model, self.name)
        elif self._field:
            if hasattr(self, 'id'):
                return "%s(%s)" % (self._field, self.id)
            if hasattr(self, 'name'):
                return "%s(%s)" % (self._field, self.name)
        return str(self._values)

    def __repr__(self):
        return str(self)

    def __bool__(self):
        if hasattr(self, 'id'):
            return bool(self.id)

    def __getitem__(self, key):
        if isinstance(key, str):
            return getattr(self, key)

    def __getattr__(self, name):
        if name.startswith('_'):
            return self.super().__getattr__(name)
        if not self._model:
            return self.super().__getattr__(name)
        if name == 'get':
            return self._values.get
        if name not in self._values:
            if not self._model._fields_loaded:
                self._model.load_fields_description()
            if  name in self._model._fields:
                self.read([name])
                return getattr(self, name)
            raise AttributeError("Attribute '%s' not found in model '%s'" % (name, self._model))

    def __setattr__(self, name, value):
        if name.startswith('_') or name == 'id':
            return super().__setattr__(name, value)
        if name not in self._values:
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

    def set_values(self, values, update_cache=True):
        self._values.update(values)
        if not values.get('id', False):
            self._updated_values = values

        if '/id' in values:
            self._xmlid = values.pop('/id', None)
        if 'id' in values and isinstance(values['id'], str):
            self._xmlid = values.pop('id', None)

        if self._model and update_cache:
            self._update_cache()
        related_values = {}
        for key in values:
            value = values[key]
            #handling relation to other record
            if isinstance(value, list) and len(value) == 2:
                field_name = key
                field = self._model.get_field(field_name)
                if not field.get('relation'):
                    continue
                model = OdooModel(self._odoo, field.get('relation'))
                if field.get('type') == 'many2one':
                    record = OdooRecord(self._odoo, model, {'id': value[0], 'name': value[1]}, field_name, self._model)
                else: #one2many or many2many
                    record = self._odoo.values_list_to_records(field.get('relation'), [{'id':val} for val in value])
                super().__setattr__(key, record)
            elif key.endswith('/id') and isinstance(value, str):
                field_name = key[:-3]
                field = self._model.get_field(field_name)
                if not field.get('relation'):
                    continue
                res_id = self._odoo.get_ref(value)
                model = OdooModel(self._odoo, field.get('relation'))
                record = OdooRecord(self._odoo, model, {'id': res_id}, field_name, self._model)
                record._xmlid = value
                super().__setattr__(field_name, record)
                related_values[f'{field_name}.id'] = record.id
                self._values.pop(key, None)
            elif key.endswith('.id') and isinstance(value, int):
                field_name = key[:-3]
                field = self._model.get_field(field_name)
                if not field.get('relation'):
                    continue
                model = OdooModel(self._odoo, field.get('relation'))
                record = OdooRecord(self._odoo, model, {'id': value}, field_name, self._model)
                super().__setattr__(field_name, record)
                related_values[f'{field_name}.id'] = record.id
            else:
                super().__setattr__(key, value)
        self._values.update(related_values)

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
