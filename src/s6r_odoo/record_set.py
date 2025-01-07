# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from .record import OdooRecord

class OdooRecordSet(list):
    _odoo = None
    _model = None

    def __init__(self, seq=(), model=None):
        super().__init__(seq)
        if model:
            self._model = model
            self._odoo = self._model._odoo

    def __getattr__(self, name):
        if name == 'ids':
            return self.get_ids()
        else:
            return self.super().__getattr__(name)

    def save(self, batch_size=100, skip_line=0, ignore_fields=[]):
        values_list = [r.get_update_values() for r in self]
        res = self._model.load_batch(values_list, batch_size=batch_size,skip_line=skip_line,
                                     ignore_fields=ignore_fields)
        res_ids = res.get('ids', False)
        if not res_ids:
            return False
        for i, r in enumerate(self):
            r._updated_values = {}
            if not r.id:
                r.id = res_ids[i]
        return True

    def get_ids(self):
        return [r.id for r in self]

    def unlink(self):
        ids = self.ids
        self._model.unlink(ids)
        for key in ids:
            self._model._cache.pop(key, None)
        self.clear()

    def filtered(self, func=None, **kwargs):
        if func:
            res = [r for r in self if func(r)]
        else:
            res = [r for r in self if all(getattr(r, k) == v for k, v in kwargs.items())]
        return OdooRecordSet(res, model=self._model)

    def mapped(self, path):
        res = []
        parents = self
        for field in path.split('.'):
            res = set([getattr(r, field) for r in parents if r])
            parents = res
        res = list(res)
        if res and isinstance(res[0], OdooRecord):
            return OdooRecordSet(res, model=res[0]._model)
        return res
