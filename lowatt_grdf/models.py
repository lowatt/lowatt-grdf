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

import json
from typing import Any, Dict, Optional

import pydantic

from . import LOGGER


def grdf_json_dumps(v: Dict[str, Any], *, default: Any) -> Any:
    for key, value in v.items():
        if isinstance(value, bool):
            v[key] = "Vrai" if value else "Faux"
    return json.dumps(v, default=default)


class DeclareAccess(pydantic.BaseModel):
    pce: str
    role_tiers: str = "AUTORISE_CONTRAT_FOURNITURE"
    raison_sociale: Optional[str]
    nom_titulaire: Optional[str]
    code_postal: str
    courriel_titulaire: str
    date_consentement_declaree: str
    date_fin_autorisation_demandee: str
    perim_donnees_techniques_et_contractuelles: bool = False
    perim_historique_de_donnees: bool = False
    perim_flux_de_donnees: bool = False
    perim_donnees_informatives: bool = False
    perim_donnees_publiees: bool = False

    class Config:
        json_dumps = grdf_json_dumps
        extra = "forbid"

    @pydantic.root_validator()
    def check_oneof_nom_or_raison_sociale(
        cls,  # noqa: B902 (Invalid first argument 'cls' used for instance method.)
        values: Dict[str, str],
    ) -> Dict[str, str]:
        if not any(values.get(k) for k in ("raison_sociale", "nom_titulaire")):
            raise ValueError(
                "One of raison-sociale or nom-titulaire should be specified"
            )
        return values


class Access(pydantic.BaseModel):
    pce: str = pydantic.Field(alias="id_pce")
    etat_droit_acces: str
    perim_donnees_publiees: bool
    perim_donnees_informatives: bool
    courriel_titulaire: str
    raison_sociale_du_titulaire: Optional[str]
    nom_titulaire: Optional[str]
    statut_controle_preuve: Optional[str]

    def __str__(self) -> str:
        name = self.raison_sociale_du_titulaire or self.nom_titulaire
        return f"<PCE {self.pce} from {name} ({self.courriel_titulaire})>"

    def is_active(self) -> bool:
        """Return True if we can get data for this PCE"""
        if self.etat_droit_acces != "Active":
            LOGGER.error(
                "Could not collect data for %s: status is '%s'",
                self,
                self.etat_droit_acces,
            )
            return False
        if not any([self.perim_donnees_publiees, self.perim_donnees_informatives]):
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
