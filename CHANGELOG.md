# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.4] - 2025-09-25

### Fixed

 - Fix __getattribute__ and __getattr__

## [2.2.0] - 2025-09-11

### Added

 - Add to_dict method on OdooRecord and OdooRecordSet and allows to convert OdooRecord to json
 - Add import_csv, import_xls and import_xlsx methods
     ```python
    odoo.import_xlsx('res.partner.xlsx', 'res.partner', limit=100, skip_line=500, batch_size=50)
    odoo.import_xls('res.partner.xls', 'res.partner', limit=100, skip_line=500, batch_size=50)
    odoo.import_csv('res.partner.csv', 'res.partner', limit=100, skip_line=500, batch_size=50)
    ```
 - Add tests to ensure read, search and create returns a RecordSet
 - Add get_id_ref_list method to get a dict with record id as key and a xmlid list as value
        e.g. {'894': ['base.module_account', ...], ...}

## [2.1.9] - 2025-08-01

### Added
   
   - Better id and xmlid handling with values_list_to_records
   - values_list_to_records now always returns an OdooRecordSet, even if empty
   - support for One2many and Many2many fields in OdooRecord
   - default language used in OdooConnection context can now be set using 'lang' keyword 

### Fixed
   
   - Concurrent OdooConnections have their own cache now
   - Record without id are not stored in cache anymore, this prevents having a 'False' key in _cache dict
   - Prevent OdooRecord _xmlid attribute to be overridden with 'None' in some cases
   - Prevent '/id' suffix to ends up in '_initialized_fields' when records are created manually from values dict then saved.

## [2.1.7] - 2025-06-09

### Fixed

 - Fix messages log in `load_batch` method

## [2.1.6] - 2025-05-27

### Fixed

 - Fix TypeError: 'bool' object is not iterable in `load_batch`

## [2.1.4] - 2025-05-05

### Fixed

 - Add retry on xmlrpc InterfaceError such "cursor already closed"


## [2.1.3] - 2025-04-30

### Fixed

 - Add retry on xmlrpc ProtocolError such "502 Bad Gateway"


## [2.1.2] - 2025-04-10

### Added

 - Add retry on connection error

## [2.1.1] - 2025-04-03

### Added

 - Add `cache_only` option to `get_xml_id_from_id` method

## [2.1.0] - 2025-03-27

### Added

 - Breaking change: with limit=1, **search** method returns a single record instead of a recordset, unless setting legacy=True
 - Improve remote error loging and add no_log option

## [2.0.5] - 2025-03-25

### Added

 - Allows to use the method 'get' on record object to ease retro-compatibility


## [2.0.4] - 2025-02-06

### Added

 - Allows to load batch with related values as int or int list

## [2.0.3] - 2025-01-07

### Fixed

 - OdooRecordSet inherit from list instead of set to preserve search order

## [2.0.2] - 2024-12-16

### Added

   - Allows to use 'filtered' and 'mapped' functions on record set
   - Introduce '_xmlid' property on record
   - Add exclude_fields parameter to search function

## [2.0.1] - 2024-12-13

### Added

   - Allows to create records from a record set

## [2.0.0] - 2024-11-12

### Added
 - Allows to use orm with a synthax close to the Odoo orm
 - Add record cache
 - Allows to save record set by batch

## [1.0.9] - 2024-10-02

### Added
   - "load_batch" method
   - added "context" keyword to stay consistent with other methods
   - added "ignored_fields" keyword to remove specific keys from data to be loaded
### Fixed
 - "search", "search_ids" methods
   - to improve clarity: replaced empty list by empty string in "order" keyword default values, as the expected type is a string and sending a list raises an error

## [1.0.8] - 2024-09-30

### Added
 - get fields function

## [1.0.7] - 2024-09-10

### Fixed
 - read function

## [1.0.6] - 2024-08-01

### Added
 - add write function

## [1.0.5] - 2024-07-26

### Added
 - Improve connection error handling

## [1.0.4] - 2024-07-12

### Added
 - Add methods: 
   - get_id_ref_dict --> {1: 'base.main_company'}
   - get_xmlid_dict --> {'base.main_company': 1}


## [1.0.3] - 2024-03-29

### Added
 - Introduce the new class OdooModel to use syntax such:
```python
m_order = odoo_cli.model('sale.order')
order_ids = m_order.search([('partner_id', '=', 5)])
```

 - Add methods:
      - read
      - read_group
      - search_count

## [1.0.2] - 2024-02-05

### Added
 - Add methods:
    - load_batch
    - create
    - unlink
    - unlink_domain
    - create_attachment
    - create_attachment_from_local_file
    - init_logger


## [1.0.1] - 2024-01-18

### Added
 - Improve error handling in get_id_from_xml_id and get_xml_id_from_id
 - Add search, read_search, get_record, default_get and load methods
