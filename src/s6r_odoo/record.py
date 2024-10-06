# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


class OdooRecord(object):
    _odoo = None
    _model = None
    _field = ''
    _parent_model = None

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
        if name not in self._values:
            if not self._model._fields_loaded:
                self._model.load_fields_description()
            if  name in self._model._fields:
                self.read([name])
                return getattr(self, name)
            raise AttributeError("Attribute '%s' not found in model '%s'" % (name, self._model))

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super().__setattr__(name, value)
        if name in self._values and name in self._initialized_fields and value != self._values[name]:
            self._updated_values[name] = value
            return super().__setattr__(name, value)
        else:
            res = super().__setattr__(name, value)
            self._initialized_fields.append(name)
            return res

    def _update_cache(self):
        if self._model:
            self._model._update_cache(self._values['id'], self._values)

    def set_values(self, values, update_cache=True):
        self._values.update(values)
        if self._model and update_cache:
            self._update_cache()
        for key in values:
            value = values[key]
            if isinstance(value, list) and len(value) == 2:
                setattr(self, key, OdooRecord(self._odoo, None, {'id': value[0], 'name': value[1]}, key, self._model))
            else:
                setattr(self, key, value)

    def read(self, fields=None, no_cache=False):
        # if not self._model:
        #     print('Model not found')
            # field_desc = self._parent_model.load_field_description(self._field)
            # self._model = self._odoo.model(field_desc['relation'])
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
        if self.id:
            self._model.write(self.id, self._updated_values)
            self._updated_values = {}
        else:
            self.id = self._odoo._create(self._model.model_name, self._values)
            self._initialized_fields = list(self._values.keys())

    def write(self, values):
        self._model.write(self.id, values)
        self._values.update(values)
        self.__dict__.update(values)

    def refresh(self):
        self.read(self._initialized_fields, no_cache=True)
