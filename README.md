# s6r-odoo

## Installation

```bash
    pip install s6r-odoo
```

## Usage

```python
from s6r_odoo import OdooConnection

odoo = OdooConnection(url='http://odoo.localhost',
                          dbname='odoo',
                          user='admin',
                          password='admin')
res_partner = odoo.model('res.partner')
partner_ids = res_partner.search([],  fields=['name', 'email'])
for partner_id in partner_ids:
    print(f'{partner_id.name} : {partner_id.email}')
```

## License

This project is licensed under the [GNU Lesser General Public License (LGPL) Version 3](https://www.gnu.org/licenses/lgpl-3.0.html).


## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements,
please open an issue or submit a pull request.

- GitHub Repository: [ScalizerOrg/s6r-odoo](https://github.com/ScalizerOrg/s6r-odoo)

## Contributors

* David Halgand - [GitHub](https://github.com/halgandd)
* Michel Perrocheau - [GitHub](https://github.com/myrrkel)


## Maintainer

This software is maintained by [Scalizer](https://www.scalizer.fr).


<div style="text-align: center;">

[![Scaliser](./logo_scalizer.png)](https://www.scalizer.fr)

</div>