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

## Testing in local environment
### Setup environment
To run the tests locally, first install pytest in your venv
```bash
pip install --upgrade pytest pytest-env
# pytest-env is an optional package to handle .env variables
```
Then from the repository root directory, install the `s6r-odoo` module in editable mode in your venv:
```bash
pip install -e ./
```
Edit `/tests/pytest.ini` to setup the tests config file
```ini
[pytest]
log_cli=true
log_level=WARNING
;WARNING produces a very nice and readable output, use DEBUG or INFO if you need to catch odoo-configurator logs or test logs 
log_format = %(asctime)s %(levelname)s %(message)s
log_date_format = %Y-%m-%d %H:%M:%S
env =
    ODOO_V16_PASSWORD=
    ODOO_V17_PASSWORD=
    ODOO_V18_PASSWORD=
; You need to fill these password env variables
```
For now, this is where we manage the passwords to access testing Odoo instances.

### Run the tests
Go to the /tests directory  `cd tests`, then just run:

```bash
pytest
```
If you are using Pycharm, this article explains in details the configuration: https://pytest-with-eric.com/integrations/pytest-pycharm-integration/#Configuring-PyCharm-for-Pytest-Optional



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