from lowatt_grdf import models


def test_structure_access() -> None:
    obj = models.converter.structure(
        {
            "role_tiers": "AUTORISE_CONTRAT_FOURNITURE",
            "id_pce": "0123",
            "perim_donnees_conso_debut": "2023-07-11",
            "perim_donnees_conso_fin": "2022-07-11",
            "perim_donnees_inj_debut": None,
            "perim_donnees_inj_fin": None,
            "date_debut_droit_acces": "2022-07-11",
            "date_fin_droit_acces": "2023-07-11",
            "statut_controle_preuve": None,
            "raison_sociale_du_titulaire": "COGIP",
            "courriel_titulaire": "cogip@example.com",
            "perim_donnees_informatives": "Vrai",
            "perim_donnees_publiees": "Faux",
            "etat_droit_acces": "Active",
            "extra_param": "dummy",  # extra are ignored
        },
        models.Access,
    )
    assert obj == models.Access(
        role_tiers="AUTORISE_CONTRAT_FOURNITURE",
        pce="0123",
        perim_donnees_conso_debut="2023-07-11",
        perim_donnees_conso_fin="2022-07-11",
        perim_donnees_inj_debut=None,
        perim_donnees_inj_fin=None,
        date_debut_droit_acces="2022-07-11",
        date_fin_droit_acces="2023-07-11",
        statut_controle_preuve=None,
        nom_titulaire=None,
        raison_sociale_du_titulaire="COGIP",
        courriel_titulaire="cogip@example.com",
        perim_donnees_informatives=True,
        perim_donnees_publiees=False,
        etat_droit_acces="Active",
    )


def test_unstructure_declare_access() -> None:
    obj = models.DeclareAccess(
        pce="0123",
        code_postal="42000",
        courriel_titulaire="cogip@example.com",
        date_debut_droit_acces="2022-07-11",
        date_fin_droit_acces="2023-07-11",
        perim_donnees_conso_debut="2023-07-11",
        perim_donnees_conso_fin="2022-07-11",
        raison_sociale="COGIP",
        perim_donnees_informatives=True,
        perim_donnees_publiees=True,
    )
    assert models.converter.unstructure(obj) == {
        "code_postal": "42000",
        "courriel_titulaire": "cogip@example.com",
        "date_debut_droit_acces": "2022-07-11",
        "date_fin_droit_acces": "2023-07-11",
        "nom_titulaire": None,
        "numero_telephone_mobile_titulaire": None,
        "perim_donnees_conso_debut": "2023-07-11",
        "perim_donnees_conso_fin": "2022-07-11",
        "perim_donnees_inj_debut": None,
        "perim_donnees_inj_fin": None,
        "perim_donnees_contractuelles": "Faux",
        "perim_donnees_informatives": "Vrai",
        "perim_donnees_publiees": "Vrai",
        "perim_donnees_techniques": "Faux",
        "raison_sociale": "COGIP",
        "role_tiers": "AUTORISE_CONTRAT_FOURNITURE",
    }
