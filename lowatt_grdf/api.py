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

import abc
import functools
import time
from typing import Any, Literal, Optional, get_args

import ndjson
import requests

from . import LOGGER, models

OLD_AUTH_ENDPOINT = (
    "https://sofit-sso-oidc.grdf.fr/openam/oauth2/realms/externeGrdf/access_token"
)
NEW_AUTH_ENDPOINT = (
    "https://adict-connexion.grdf.fr/oauth2/aus5y2ta2uEHjCWIR417/v1/token"
)


def raise_for_status(resp: requests.Response) -> None:
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        try:
            data = resp.json()
        except requests.exceptions.JSONDecodeError:
            data = resp.text
        LOGGER.error(data)
        raise


class BaseAPI(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def scope(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def api(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def _auth_endpoint(self) -> str:
        raise NotImplementedError()

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._last_request: Optional[float] = None
        self._access_expires: Optional[float] = None

    def _parse_response(self, resp: requests.Response) -> Any:
        return ndjson.loads(resp.text)

    def request(self, verb: str, *args: Any, **kwargs: Any) -> Any:
        headers = kwargs.setdefault("headers", {})
        headers.setdefault("Accept", "application/json")
        if "files" not in kwargs:
            headers.setdefault("Content-Type", "application/json")
        headers["Authorization"] = f"Bearer {self.access_token}"
        if self._last_request is not None:
            time.sleep(min(max(time.time() - self._last_request, 1), 1))
        resp = requests.request(verb, *args, **kwargs)
        self._last_request = time.time()
        raise_for_status(resp)
        return self._parse_response(resp)

    get = functools.partialmethod(request, "GET")
    post = functools.partialmethod(request, "POST")
    put = functools.partialmethod(request, "PUT")
    patch = functools.partialmethod(request, "PATCH")

    @property
    def access_token(self) -> str:
        if self._access_token is None or (
            self._access_expires is not None and self._access_expires < time.time()
        ):
            self._access_token, self._access_expires = self._authenticate()
        return self._access_token

    def _authenticate(self) -> tuple[str, float]:
        resp = requests.post(
            self._auth_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope,
            },
        )
        raise_for_status(resp)
        data = resp.json()
        token = data["access_token"]
        assert isinstance(token, str)
        expires_in = data["expires_in"]
        assert isinstance(expires_in, int)
        access_expires = time.time() + expires_in
        return (token, access_expires)

    def droits_acces(self, pce: Optional[list[str]] = None) -> Any:
        if not pce:
            return self.get(f"{self.api}/droits_acces")
        return self.post(f"{self.api}/droits_acces", json={"id_pce": pce})

    DEFAULT_THIRD_ROLE = get_args(models.ThirdRole)
    AccessRightState = Literal[
        "Active", "A valider", "Révoquée", "A revérifier", "Obsolète", "Refusée"
    ]
    DEFAULT_ACCESS_RIGHT_STATE = get_args(AccessRightState)
    ProofControlStatus = Literal[
        "Preuve en attente",
        "Preuve en cours de vérification",
        "Preuve Vérifiée OK",
        "Preuve Vérifiée KO",
    ]
    DEFAULT_PROOF_CONTROL_STATUS = get_args(ProofControlStatus)

    def droits_acces_specifiques(
        self,
        pce: Optional[list[str]] = None,
        third_role: tuple[models.ThirdRole] = DEFAULT_THIRD_ROLE,
        access_right_state: tuple[AccessRightState] = DEFAULT_ACCESS_RIGHT_STATE,
        proof_control_status: tuple[ProofControlStatus] = DEFAULT_PROOF_CONTROL_STATUS,
    ) -> Any:
        return self.post(
            f"{self.api}/droits_acces",
            json={
                "id_pce": pce,
                "role_tiers": third_role,
                "etat_droit_acces": access_right_state,
                "statut_controle_preuve": proof_control_status,
            },
        )

    def revoke_acces(self, id_droit_acces: str) -> Any:
        return self.patch(
            f"{self.api}/droit_acces/{id_droit_acces}",
        )

    def check_consent_validation(self, pce: Optional[list[str]] = None) -> None:
        resp = self.droits_acces(pce)
        # XXX: this looks like a bug, "liste_acces" should be part of the response
        items = resp[0]["liste_acces"] if resp and "liste_acces" in resp[0] else resp
        droits: dict[str, list[models.Access]] = {}
        for item in items:
            if "code_statut_traitement" in item:
                continue
            access = models.converter.structure(item, models.Access)
            droits.setdefault(access.pce, []).append(access)
        errors = []
        for _, accesses in sorted(
            droits.items(), key=lambda x: (x[1][0].courriel_titulaire, x[0])
        ):
            for access in accesses:
                if not access.check_consent():
                    errors.append(access)

            if any(access.is_active(log=False) for access in accesses):
                LOGGER.info("Access to %s OK", accesses[0])
            else:
                for access in accesses:
                    access.is_active(log=True)
        if errors:
            raise RuntimeError(f"Theses consents have validation issues: {errors!r}")

    def declare_acces(self, access: models.DeclareAccess) -> None:
        data = {
            k: v
            for k, v in models.converter.unstructure(access).items()
            if v is not None
        }
        self.put(
            f"{self.api}/pce/{access.pce}/droit_acces",
            json=data,
        )
        LOGGER.info("Successfully declared access to %s", access.pce)

    def transmettre_preuves(
        self, id_droit_acces: str, preuves: tuple[tuple[str, bytes], ...]
    ) -> Any:
        return self.put(
            f"{self.api}/droit_acces/{id_droit_acces}/preuves",
            files=(("preuves", (fname, data)) for fname, data in preuves),
        )

    def donnees_consos_publiees(self, pce: str, from_date: str, to_date: str) -> Any:
        return self.get(
            f"{self.api}/pce/{pce}/donnees_consos_publiees",
            params={
                "date_debut": from_date,
                "date_fin": to_date,
            },
        )

    def donnees_consos_informatives(
        self,
        pce: str,
        from_date: str,
        to_date: str,
    ) -> Any:
        return self.get(
            f"{self.api}/pce/{pce}/donnees_consos_informatives",
            params={
                "date_debut": from_date,
                "date_fin": to_date,
            },
        )

    def donnees_injections_publiees(
        self, pce: str, from_date: str, to_date: str
    ) -> Any:
        return self.get(
            f"{self.api}/pce/{pce}/donnees_injections_publiees",
            params={
                "date_debut": from_date,
                "date_fin": to_date,
            },
        )

    def donnees_contractuelles(self, pce: str) -> Any:
        (payload,) = self.get(f"{self.api}/pce/{pce}/donnees_contractuelles")
        return payload

    def donnees_techniques(self, pce: str) -> Any:
        (payload,) = self.get(f"{self.api}/pce/{pce}/donnees_techniques")
        return payload


class StagingAPI(BaseAPI):
    scope = "/adict/bas/v6"
    api = "https://api.grdf.fr/adict/bas/v6"

    @property
    def _auth_endpoint(self) -> str:
        if self.client_id.startswith("grdf_"):
            return OLD_AUTH_ENDPOINT
        return NEW_AUTH_ENDPOINT

    def _parse_response(self, resp: requests.Response) -> Any:
        # XXX: Adjusts GRDF API responses to fit ndjson expected input because
        # GRDF Staging API v6 responses contain multiple-lines JSON objects
        # whereas ndjson expects one-line JSON objects
        return ndjson.loads(resp.text.replace("\n", "").replace("}{", "}\n{"))

    def donnees_injections_publiees(
        self, pce: str, from_date: str, to_date: str
    ) -> Any:
        # XXX: Temporary fix for Staging API v6 that as an incorrect endpoint
        return self.get(
            f"{self.api}/pce/{pce}/donnees_injection_publiees",
            params={
                "date_debut": from_date,
                "date_fin": to_date,
            },
        )


class API(BaseAPI):
    scope = "/adict/v2"
    api = "https://api.grdf.fr/adict/v2"

    @property
    def _auth_endpoint(self) -> str:
        if self.client_id.endswith("_grdf"):
            return OLD_AUTH_ENDPOINT
        return NEW_AUTH_ENDPOINT
