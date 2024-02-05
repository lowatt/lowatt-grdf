# Copyright (c) 2021 Lowatt <info@lowatt.fr>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time
from typing import Any, Optional

import attrs
import cattrs
import cattrs.gen
import cattrs.preconf.json

from . import LOGGER


def validate_date_format(
    instance: Any, attribute: "attrs.Attribute[str]", value: Any
) -> None:
    assert isinstance(value, str), type(value)
    try:
        time.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"format of {attribute} must be 'YYYY-MM-DD', got {value}"
        ) from exc


class BaseModel:
    pass


@attrs.frozen
class DeclareAccess(BaseModel):
    pce: str
    code_postal: str
    courriel_titulaire: str
    date_consentement_declaree: str = attrs.field(validator=validate_date_format)
    date_debut_droit_acces: str = attrs.field(validator=validate_date_format)
    date_fin_droit_acces: str = attrs.field(validator=validate_date_format)
    perim_donnees_conso_debut: str = attrs.field(validator=validate_date_format)
    perim_donnees_conso_fin: str = attrs.field(validator=validate_date_format)
    raison_sociale: Optional[str] = None
    nom_titulaire: Optional[str] = None
    role_tiers: str = "AUTORISE_CONTRAT_FOURNITURE"
    numero_telephone_titulaire: Optional[str] = None
    perim_donnees_contractuelles: bool = False
    perim_donnees_techniques: bool = False
    perim_donnees_informatives: bool = False
    perim_donnees_publiees: bool = False

    def __attrs_post_init__(self) -> None:
        if not self.raison_sociale and not self.nom_titulaire:
            raise ValueError("One of raison-sociale or nom-titulaire must be specified")


@attrs.frozen
class Access(BaseModel):
    pce: str
    etat_droit_acces: str
    perim_donnees_publiees: bool
    perim_donnees_informatives: bool
    courriel_titulaire: str
    statut_controle_preuve: Optional[str]
    date_debut_droit_acces: str
    date_fin_droit_acces: str
    perim_donnees_conso_debut: str
    perim_donnees_conso_fin: str
    raison_sociale_du_titulaire: Optional[str] = None
    nom_titulaire: Optional[str] = None
    date_consentement_declaree: Optional[str] = None
    numero_telephone_titulaire: Optional[str] = None
    perim_donnees_contractuelles: bool = False
    perim_donnees_techniques: bool = False

    def __attrs_post_init__(self) -> None:
        if not self.raison_sociale_du_titulaire and not self.nom_titulaire:
            raise ValueError(
                "One of raison_sociale_du_titulaire or nom_titulaire is expected"
            )

    def __str__(self) -> str:
        name = self.raison_sociale_du_titulaire or self.nom_titulaire
        return f"<PCE {self.pce} from {name} ({self.courriel_titulaire})>"

    def is_active(self, log: bool = True) -> bool:
        """Return True if we can get data for this PCE"""
        if self.etat_droit_acces != "Active":
            if log:
                LOGGER.error(
                    "Could not collect data for %s: etat_droit_acces is '%s'",
                    self,
                    self.etat_droit_acces,
                )
            return False
        if not any([self.perim_donnees_publiees, self.perim_donnees_informatives]):
            if log:
                LOGGER.error(
                    "Could not collect data for %s: both perim_donnees_publiees and "
                    "perim_donnees_informatives are not set",
                    self,
                )
            return False
        return True

    def check_consent(self) -> bool:
        """Return True if there's no pending/failed consent validation"""
        if self.statut_controle_preuve in ("Preuve en attente", "Preuve Vérifiée KO"):
            LOGGER.error(
                "statut_controle_preuve of %s is %r",
                self,
                self.statut_controle_preuve,
            )
            return False
        return True


def structure_grdf_bool(value: Any, type_: Any) -> bool:
    if not isinstance(value, str):
        raise ValueError(f"Unhandled type {type(value)} for {value!r}")
    if value.lower() == "vrai":
        return True
    if value.lower() == "faux":
        return False
    else:
        raise ValueError(f"Unhandled value {value!r}")


def unstructure_grdf_bool(value: bool) -> str:
    return "Vrai" if value else "Faux"


converter = cattrs.preconf.json.make_converter()
converter.register_structure_hook(
    Access,
    cattrs.gen.make_dict_structure_fn(
        Access,
        cattrs.global_converter,
        pce=cattrs.gen.override(rename="id_pce"),
        **{  # type: ignore[arg-type]
            f.name: cattrs.gen.override(struct_hook=structure_grdf_bool)
            for f in attrs.fields(Access)
            if f.type == bool
        },
    ),
)
converter.register_unstructure_hook(
    DeclareAccess,
    cattrs.gen.make_dict_unstructure_fn(
        DeclareAccess,
        converter,
        pce=cattrs.gen.override(omit=True),
        date_consentement_declaree=cattrs.gen.override(
            unstruct_hook=lambda v: v + " 00:00:00"
        ),
        **{  # type: ignore[arg-type]
            f.name: cattrs.gen.override(unstruct_hook=unstructure_grdf_bool)
            for f in attrs.fields(Access)
            if f.type == bool
        },
    ),
)
