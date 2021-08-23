# lowatt-grdf

A command-line tool and Python library to access
[GrDF Addict](https://sites.grdf.fr/web/portail-api-grdf-adict) API, provided by
[Lowatt](https://www.lowatt.fr).

## Licensing

It is published under the terms of the MIT license.

## Installation

``pip install lowatt-grdf``

## Command line usage

```
$ lowatt-grdf --help
Usage: lowatt-grdf [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  declare-acces
  donnees-consos-informatives
  donnees-consos-publiees
  donnees-contractuelles
  donnees-techniques
  droits-acces
```

Each subcommand implement the related API endpoint and output json that can easily be piped to [jq](https://stedolan.github.io/jq/) for reading.
Also each command will require to supply ``--client-id`` and ``--client-secret``, or via corresponding environment variables ``CLIENT_ID`` and ``CLIENT_SECRET``. These access are only provided by GRDF.


The ``droits-acces`` subcommand has also a ``--check`` parameter which will check consent validation:

* ``statut_controle_preuve`` must not be ``Preuve en attente`` or ``Preuve Vérifiée KO``
* ``etat_droit_acces`` must be ``Active``

This command is intended to be used at a daily basis in CI or cron, raising an alert in case of error, because it will require a manual correction.


## Python library usage

Here is a sample code to access to the ``donnees-consos-publiees`` endpoint:

```python
from lowatt_grdf.api import API

client_id = "ID"
client_secret = "SECRET"
pce = "23000000000000"

grdf = API(client_id, client_secret)
for releve in grdf.donnees_consos_publiees(pce, from_date="2021-01-01", to_date="2021-08-23"):
  conso = releve["consommation"]
  print(conso["date_debut_consommation"], conso["date_fin_consommation"], conso["energie"])
```


## Contributions

Contribution are welcome through the [Github
repository](https://github.com/lowatt/lowatt-grdf).

Feel free to contact for more info by writing at info@lowatt.fr.
