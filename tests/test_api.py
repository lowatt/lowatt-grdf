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
import logging

import ndjson
import pytest
import responses

from lowatt_grdf import api, models


@pytest.fixture
def grdf() -> api.API:
    responses.add(
        responses.POST,
        f"{api.OPENID_ENDPOINT}/access_token",
        json={
            "access_token": "xxx",
            "expires_in": 14400,
        },
    )
    return api.API("id", "secret")


@responses.activate
def test_access_token(grdf: api.API) -> None:
    assert grdf.access_token == "xxx"


@responses.activate
def test_donnees_contractuelles(grdf: api.API) -> None:
    payload = {
        "pce": {"id_pce": "23000000000000"},
        "donnees_contractuelles": {
            "car": 9426,
            "cja": 0,
            "profil": {"profil_type_actuel": "P012"},
            "tarif_acheminement": "T2",
            "date_mes": "2020-12-07",
        },
        "statut_restitution": None,
    }
    responses.add(
        responses.GET,
        f"{grdf.api}/pce/23000000000000/donnees_contractuelles",
        json=payload,
    )
    assert grdf.donnees_contractuelles("23000000000000") == payload


@responses.activate
def test_donnees_techniques(grdf: api.API) -> None:
    payload = {
        "pce": {"id_pce": "23000000000000"},
        "donnees_techniques": {
            "situation_compteur": {
                "numero_rue": "4",
                "nom_rue": "RUE LAMBDA",
                "complement_adresse": None,
                "code_postal": "99099",
                "commune": "LAMBDAVILLE",
            },
            "caracteristiques_compteur": {
                "frequence": "1M",
                "client_sensible_mig": "Non",
            },
            "pitd": {"identifiant_pitd": "GD9999", "libelle_pitd": "DUMMYVILLE"},
        },
        "statut_restitution": None,
    }
    responses.add(
        responses.GET,
        f"{grdf.api}/pce/23000000000000/donnees_techniques",
        json=payload,
    )
    assert grdf.donnees_techniques("23000000000000") == payload


ACCESS_PAYLOAD = {
    "id_droit_acces": "2734291b-3df4-4aef-92de-ad0186e0be6b",
    "id_pce": "GI000000",
    "role_tiers": "AUTORISE_CONTRAT_FOURNITURE",
    "raison_sociale_du_tiers": "DUMMY",
    "nom_titulaire": None,
    "raison_sociale_du_titulaire": "John Doe Inc.",
    "courriel_titulaire": "jdoe@example.com",
    "code_postal": "99099",
    "numero_telephone_titulaire": "0600000000",
    "perim_donnees_informatives": "Vrai",
    "perim_donnees_contractuelles": "Vrai",
    "perim_donnees_techniques:": "Vrai",
    "perim_donnees_conso_debut": "2020-01-01",
    "perim_donnees_conso_fin": "2025-01-01",
    "perim_donnees_publiees": "Vrai",
    "date_creation": "2021-07-02 16:41:14",
    "date_debut_droit_acces": "2021-07-02",
    "date_fin_droit_acces": "2030-01-01",
    "etat_droit_acces": "Active",
    "date_revocation": None,
    "source_revocation": None,
    "date_passage_a_obsolete": None,
    "source_passage_a_obsolete": None,
    "date_fin_autorisation": "2023-07-02 00:00:00",
    "date_passage_a_refuse": None,
    "source_passage_a_refuse": None,
    "parcours": "CLIENT_CONNECT",
    "statut_controle_preuve": None,
    "date_limite_transmission_preuve": None,
    "date_consentement_declaree": None,
}


@responses.activate
def test_droits_acces(grdf: api.API) -> None:
    payload = [
        ACCESS_PAYLOAD,
        {
            "code_statut_traitement": "0000000000",
            "message_retour_traitement": "L'opération s'est déroulée avec succès.",
        },
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/droits_acces",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    assert grdf.droits_acces() == payload


@responses.activate
def test_check_constent_validation_ok(
    grdf: api.API, caplog: pytest.LogCaptureFixture
) -> None:
    payload = [
        ACCESS_PAYLOAD,
        {
            "code_statut_traitement": "0000000000",
            "message_retour_traitement": "L'opération s'est déroulée avec succès.",
        },
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/droits_acces",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    with caplog.at_level(logging.INFO, logger="lowatt.grdf"):
        grdf.check_consent_validation()
    assert [r.message for r in caplog.records] == [
        "Access to <PCE GI000000 from John Doe Inc. (jdoe@example.com)> OK",
    ]


@responses.activate
def test_check_constent_validation_inactive(
    grdf: api.API, caplog: pytest.LogCaptureFixture
) -> None:
    access = dict(ACCESS_PAYLOAD)
    access["etat_droit_acces"] = "À valider"
    payload = [
        access,
        {
            "code_statut_traitement": "0000000000",
            "message_retour_traitement": "L'opération s'est déroulée avec succès.",
        },
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/droits_acces",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    with caplog.at_level(logging.INFO, logger="lowatt.grdf"):
        grdf.check_consent_validation()
    assert [r.message for r in caplog.records] == [
        "Could not collect data for <PCE GI000000 from John Doe Inc. (jdoe@example.com)>: etat_droit_acces is 'À valider'",
    ]


@responses.activate
def test_check_constent_multiple_ok(
    grdf: api.API, caplog: pytest.LogCaptureFixture
) -> None:
    access = dict(ACCESS_PAYLOAD)
    access["etat_droit_acces"] = "À valider"
    payload = [
        ACCESS_PAYLOAD,
        access,
        {
            "code_statut_traitement": "0000000000",
            "message_retour_traitement": "L'opération s'est déroulée avec succès.",
        },
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/droits_acces",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    with caplog.at_level(logging.INFO, logger="lowatt.grdf"):
        grdf.check_consent_validation()
    assert [r.message for r in caplog.records] == [
        "Access to <PCE GI000000 from John Doe Inc. (jdoe@example.com)> OK",
    ]


@responses.activate
def test_check_constent_multiple_ko(
    grdf: api.API, caplog: pytest.LogCaptureFixture
) -> None:
    access1 = dict(ACCESS_PAYLOAD)
    access1["etat_droit_acces"] = "À valider"
    access2 = dict(ACCESS_PAYLOAD)
    access2["perim_donnees_publiees"] = "Faux"
    access2["perim_donnees_informatives"] = "Faux"
    payload = [
        access1,
        access2,
        {
            "code_statut_traitement": "0000000000",
            "message_retour_traitement": "L'opération s'est déroulée avec succès.",
        },
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/droits_acces",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    with caplog.at_level(logging.INFO, logger="lowatt.grdf"):
        grdf.check_consent_validation()
    assert [r.message for r in caplog.records] == [
        "Could not collect data for <PCE GI000000 from John Doe Inc. (jdoe@example.com)>: etat_droit_acces is 'À valider'",
        "Could not collect data for <PCE GI000000 from John Doe Inc. (jdoe@example.com)>: both perim_donnees_publiees and perim_donnees_informatives are not set",
    ]


@responses.activate
def test_check_constent_validation_preuve(
    grdf: api.API, caplog: pytest.LogCaptureFixture
) -> None:
    access = dict(ACCESS_PAYLOAD)
    access["statut_controle_preuve"] = "Preuve en attente"
    payload = [
        access,
        {
            "code_statut_traitement": "0000000000",
            "message_retour_traitement": "L'opération s'est déroulée avec succès.",
        },
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/droits_acces",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    with (
        caplog.at_level(logging.INFO, logger="lowatt.grdf"),
        pytest.raises(RuntimeError, match="Theses consents have validation issues"),
    ):
        grdf.check_consent_validation()
    assert [r.message for r in caplog.records] == [
        "statut_controle_preuve of <PCE GI000000 from John Doe Inc. (jdoe@example.com)> is 'Preuve en attente'",
        "Access to <PCE GI000000 from John Doe Inc. (jdoe@example.com)> OK",
    ]


@responses.activate
def test_donnees_consos_publiees(grdf: api.API) -> None:
    payload = [
        {
            "pce": {"id_pce": "23000000000000"},
            "periode": {
                "valeur": None,
                "date_debut": "2021-01-01",
                "date_fin": "2021-01-23",
            },
            "releve_debut": {
                "date_releve": None,
                "raison_releve": None,
                "libelle_raison_releve": None,
                "qualite_releve": "Mesure",
                "statut_releve": "Normal",
                "index_brut_debut": {
                    "valeur_index": 771,
                    "horodate_Index": "2021-01-01T06:00:00+01:00",
                },
                "index_converti_debut": {"valeur_index": None, "horodate_Index": None},
            },
            "releve_fin": {
                "date_releve": "2021-01-23T06:00:00+01:00",
                "raison_releve": "RNO",
                "libelle_raison_releve": "Relevé normal",
                "qualite_releve": "Mesure",
                "statut_releve": "Normal",
                "index_brut_fin": {
                    "valeur_index": 951,
                    "horodate_Index": "2021-01-23T06:00:00+01:00",
                },
                "index_converti_fin": {"valeur_index": None, "horodate_Index": None},
            },
            "consommation": {
                "date_debut_consommation": "2021-01-01T06:00:00+01:00",
                "date_fin_consommation": "2021-01-23T06:00:00+01:00",
                "flag_retour_zero": False,
                "volume_brut": 180,
                "coeff_calcul": {
                    "coeff_pta": None,
                    "valeur_pcs": None,
                    "coeff_conversion": 11.29,
                },
                "volume_converti": 0,
                "energie": 2032,
                "type_qualif_conso": "Mesuré",
                "sens_flux_gaz": "Consommation",
                "statut_conso": "Définitive",
                "journee_gaziere": None,
                "type_conso": "Publiée",
            },
            "bordereau_publication": {
                "date_debut_bordereau": None,
                "date_fin_bordereau": None,
                "nb_jour_gazier": None,
            },
            "statut_restitution": None,
        }
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/pce/23000000000000/donnees_consos_publiees",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    assert (
        grdf.donnees_consos_publiees(
            "23000000000000", from_date="2021-01-01", to_date="2021-01-23"
        )
        == payload
    )
    assert (
        responses.calls[-1].request.url
        == "https://api.grdf.fr/adict/v2/pce/23000000000000/donnees_consos_publiees?date_debut=2021-01-01&date_fin=2021-01-23"
    )


@responses.activate
def test_donnees_consos_informatives(grdf: api.API) -> None:
    payload = [
        {
            "pce": {"id_pce": "23000000000000"},
            "periode": {
                "valeur": None,
                "date_debut": "2021-08-16",
                "date_fin": "2021-08-19",
            },
            "releve_debut": {
                "date_releve": None,
                "index_brut_debut": {"valeur_index": None, "horodate_Index": None},
                "index_converti_debut": {"valeur_index": None, "horodate_Index": None},
            },
            "releve_fin": {
                "date_releve": "2021-08-17T06:00:00+02:00",
                "index_brut_fin": {
                    "valeur_index": 1325,
                    "horodate_Index": "2021-08-17T06:00:00+02:00",
                },
                "index_converti_fin": {"valeur_index": None, "horodate_Index": None},
            },
            "consommation": {
                "date_debut_consommation": "2021-08-16T06:00:00+02:00",
                "date_fin_consommation": "2021-08-17T06:00:00+02:00",
                "flag_retour_zero": None,
                "volume_brut": 1,
                "coeff_calcul": {
                    "coeff_pta": None,
                    "valeur_pcs": None,
                    "coeff_conversion": 11.16,
                },
                "volume_converti": None,
                "energie": 8,
                "type_qualif_conso": "Mesuré",
                "sens_flux_gaz": "Consommation",
                "statut_conso": "Provisoire",
                "journee_gaziere": "2021-08-16",
                "type_conso": "Informative Journalier",
            },
            "statut_restitution": None,
        }
    ]
    responses.add(
        responses.GET,
        f"{grdf.api}/pce/23000000000000/donnees_consos_informatives",
        headers={"Content-Type": "application/nd-json"},
        body=ndjson.dumps(payload),
    )
    assert (
        grdf.donnees_consos_informatives(
            "23000000000000", from_date="2021-08-16", to_date="2021-08-17"
        )
        == payload
    )
    assert (
        responses.calls[-1].request.url
        == "https://api.grdf.fr/adict/v2/pce/23000000000000/donnees_consos_informatives?date_debut=2021-08-16&date_fin=2021-08-17"
    )


@responses.activate
def test_declare_acces(grdf: api.API, caplog: pytest.LogCaptureFixture) -> None:
    access = models.DeclareAccess(
        pce="23000000000000",
        nom_titulaire="jdoe",
        code_postal="99099",
        courriel_titulaire="jdoe@example.com",
        numero_telephone_titulaire="0600000000",
        date_debut_droit_acces="2020-01-01",
        date_fin_droit_acces="2025-12-31",
        perim_donnees_conso_debut="2020-01-01",
        perim_donnees_conso_fin="2020-01-01",
        raison_sociale="dummy",
        date_consentement_declaree="2020-01-01",
    )
    # XXX: use a real life response
    responses.add(responses.PUT, f"{grdf.api}/pce/23000000000000/droit_acces", json={})
    with caplog.at_level(logging.INFO, logger="lowatt.grdf"):
        grdf.declare_acces(access)
    body = responses.calls[-1].request.body
    assert body is not None
    assert json.loads(body) == {
        "code_postal": "99099",
        "courriel_titulaire": "jdoe@example.com",
        "date_consentement_declaree": "2020-01-01 00:00:00",
        "date_debut_droit_acces": "2020-01-01",
        "date_fin_droit_acces": "2025-12-31",
        "nom_titulaire": "jdoe",
        "numero_telephone_titulaire": "0600000000",
        "perim_donnees_conso_debut": "2020-01-01",
        "perim_donnees_conso_fin": "2020-01-01",
        "perim_donnees_contractuelles": "Faux",
        "perim_donnees_informatives": "Faux",
        "perim_donnees_publiees": "Faux",
        "perim_donnees_techniques": "Faux",
        "raison_sociale": "dummy",
        "role_tiers": "AUTORISE_CONTRAT_FOURNITURE",
    }
    assert [r.message for r in caplog.records] == [
        "Successfully declared access to 23000000000000",
    ]
