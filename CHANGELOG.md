# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
