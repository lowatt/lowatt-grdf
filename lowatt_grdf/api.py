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
from typing import Any, Dict, List, Optional

import ndjson
import requests

from . import LOGGER, models

OPENID_ENDPOINT = "https://sofit-sso-oidc.grdf.fr/openam/oauth2/realms/externeGrdf"


def parse_grdf_bool(data: Dict[str, Any]) -> Dict[str, Any]:
    """Turn 'Vrai' and 'Faux' items from input dict into regular booleans

    >>> parse_grdf_bool({"foo": "Vrai", "bar": "Faux"})
    {'foo': True, 'bar': False}
    """
    data = dict(data)
    for key, value in data.items():
        if isinstance(value, str) and value.lower() in ("vrai", "faux"):
            data[key] = True if value.lower() == "vrai" else False
    return data


class BaseAPI(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def scope(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def api(self) -> str:
        raise NotImplementedError()

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._last_request: Optional[float] = None

    def request(self, verb: str, *args: Any, **kwargs: Any) -> Any:
        headers = kwargs.setdefault("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        if self._last_request is not None:
            time.sleep(min(max(time.time() - self._last_request, 1), 1))
        resp = requests.request(verb, *args, **kwargs)
        self._last_request = time.time()
        resp.raise_for_status()
        # XXX: duno why but without strip it doesn't work.
        # Either an implementation error of ndjson module
        # or bad response from GrDF API (at least on staging environment)
        return ndjson.loads(resp.content.strip())

    get = functools.partialmethod(request, "GET")
    post = functools.partialmethod(request, "POST")
    put = functools.partialmethod(request, "PUT")

    @property
    def access_token(self) -> str:
        if self._access_token is None:
            self._access_token = self._authenticate()
        return self._access_token

    def _authenticate(self) -> str:
        resp = requests.post(
            f"{OPENID_ENDPOINT}/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope,
            },
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        assert isinstance(token, str)
        return token

    def droits_acces(self, pce: Optional[List[str]] = None) -> Any:
        if not pce:
            return self.get(f"{self.api}/droits_acces")
        return self.post(f"{self.api}/droits_acces", json={"id_pce": pce})

    def check_consent_validation(self, pce: Optional[List[str]] = None) -> None:
        resp = self.droits_acces(pce)
        # XXX: this looks like a bug, "liste_acces" should be part of the response
        if resp and "liste_acces" in resp[0]:
            droits = resp[0]["liste_acces"]
        else:
            droits = resp
        errors = []
        for droit in droits:
            if "code_statut_traitement" in droit:
                continue
            access = models.Access(**parse_grdf_bool(droit))
            if not access.check_consent():
                errors.append(droit)
            if access.is_active():
                LOGGER.info("Access to %s OK", access)
        if errors:
            raise RuntimeError(f"Theses consents have validation issues: {errors!r}")

    def declare_acces(self, access: models.DeclareAccess) -> None:
        data = access.json(exclude={"pce"}, exclude_none=True)
        self.put(
            f"{self.api}/pce/{access.pce}/droit_acces",
            headers={"Content-Type": "application/json"},
            data=data,
        )
        LOGGER.info("Successfully declared access to %s", access.pce)

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

    def donnees_contractuelles(self, pce: str) -> Any:
        (payload,) = self.get(f"{self.api}/pce/{pce}/donnees_contractuelles")
        return payload

    def donnees_techniques(self, pce: str) -> Any:
        (payload,) = self.get(f"{self.api}/pce/{pce}/donnees_techniques")
        return payload


class StagingAPI(BaseAPI):
    scope = "/adict/bas/v3"
    api = "https://api.grdf.fr/adict/bas/v3"


class API(BaseAPI):
    scope = "/adict/v1"
    api = "https://api.grdf.fr/adict/v1"
