# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


class OdooRecord(object):
    _odoo = None
    _model = None
    _values = {}
    _field = ''
    _parent_model = None

    def __init__(self, odoo, model, values: dict, field='', parent_model=None):
        self._odoo = odoo
        self.id = False
        if model:
            self._model = model
            self._odoo = self._model._odoo
        if field:
            self._field = field
        if parent_model:
            self._parent_model = parent_model
        self._values = values
        self._init_values()

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

    def __bool__(self):
        if hasattr(self, 'id'):
            return bool(self.id)
        else:
            return False


    def _init_values(self):
        self.set_values(self._values)

    def set_values(self, values):
        if self._model:
            self._odoo._models[self._model.model_name]._cache[values['id']] = values
        for key in values:
            value = values[key]
            if isinstance(value, list) and len(value) == 2:
                setattr(self, key, OdooRecord(self._odoo, None, {'id': value[0], 'name': value[1]}, key, self._model))
            else:
                setattr(self, key, value)

    def read(self):
        if not self._model:
            field_desc = self._parent_model.load_field_description(self._field)
            self._model = self._odoo.model(field_desc['relation'])
        if not self._model._fields_loaded:
            self._model.load_fields_description()
        if self.id in self._model._cache:
            res = self._model._cache[self.id]
            self.set_values(res)
        else:
            res = self._odoo._read(self._model.model_name, self.id, self._model.get_fields_list())
            if res:
                self.set_values(res[0])
