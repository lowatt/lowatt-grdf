# Staging API requests

Requests to send to the Staging API v6 of GRDF ADICT, based on `API GRDF ADICT_JDD_BAS_v1.3.xlsx`.

## Gestion des droits d'accès

### Déclarer un droit d'accès

*These endpoints return an 400 Client Error with Staging API v6. The support team is aware of this issue so it should be fixed in the next version.*

### Consulter mes droits d'accès

1. Cas passant : Consulter tous mes droits d'accès
   ```shell
   lowatt-grdf droits-acces --bas
   ```

### Consulter mes droits d'accès spécifiques

1. Cas passant : Consulter mes droits d'accès avec filtre sur plusieurs PCE
   ```shell
   lowatt-grdf droits-acces-specifiques --bas 09999999900617 GI999055
   ```
1. Cas passant : Consulter mes droits d'accès avec filtre sur l'Etat "Obsolète"
   ```shell
   # Returns an 400 Client Error with Staging API v6.
   # The support team is aware of this issue so it should be fixed in the next version.
   lowatt-grdf droits-acces-specifiques --bas --etat Obsolète
   ```
1. Cas passant : Consulter mes droits d'accès avec filtre sur le Statut de contrôle "Preuve en attente" et "Preuve en cours de vérification"
   ```shell
   lowatt-grdf droits-acces-specifiques --bas --preuve "Preuve en attente" --preuve "Preuve en cours de vérification"
   ```
1. Cas passant : Consulter mes droits d'accès avec filtres cumulatifs sur le Role et l'Etat
   ```shell
   lowatt-grdf droits-acces-specifiques --bas --role DETENTEUR_CONTRAT_FOURNITURE --role DETENTEUR_CONTRAT_INJECTION --etat Active
   ```

### Révoquer un droit d'accès

*Not implemented yet.*

### Transmettre Preuve(s) sur un droit d'accès

*Not implemented yet.*

## Consommations publiées

### Consulter les données de consommation publiées

1. Cas passant : 1M Données publiées avec données bornées par MES le 02/08/2021
   ```shell
   lowatt-grdf donnees-consos-publiees --bas 09999999900617 --from-date 2021-01-01 --to-date 2021-10-15
   ```
1. Cas passant : 6M Données publiées sur pluseurs années avec données bornées par perim_donnees_conso_debut le 15/11/2021
   ```shell
   lowatt-grdf donnees-consos-publiees --bas 09999999975102 --from-date 2021-01-01 --to-date 2023-01-01
   ```
1. Cas passant : JJ Données publiées avec changement de de fréquence le 10/02/2023
   ```shell
   lowatt-grdf donnees-consos-publiees --bas GI999055 --from-date 2023-01-11 --to-date 2023-02-11
   ```
1. Cas passant : MM Données publiées avec changement de fournisseur le 01/01/2023 et appel periode
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-publiees --bas GI999947 --period 2023-01
   ```
1. Cas passant : 1M Données publiées avec changement de compteur le 29/03/2023 et passage à l’état communicant le 14/08/2023
   ```shell
   lowatt-grdf donnees-consos-publiees --bas 09999999928289 --from-date 2023-03-29 --to-date 2023-08-15
   ```
1. Cas passant : JJ Données publiées avec changement de tarif le 01/02/2023
   ```shell
   lowatt-grdf donnees-consos-publiees --bas GI999159 --from-date 2023-01-31 --to-date 2023-02-05
   ```
1. Cas intermédiaire : Erreur sur le Bloc de consommation n°1 (appel date à date)
   ```shell
   # Raises the error "json.decoder.JSONDecodeError: Expecting ',' delimiter: line 1 column 165 (char 164)"
   # because the response returned by Staging API v6 is incorrectly formatted (missing bracket).
   # The support team is aware of this issue so it should be fixed in the next version.
   lowatt-grdf donnees-consos-publiees --bas 09999999975102 --from-date 2021-08-18 --to-date 2023-08-17
   ```
1. Cas non passant : PCE sur lequel il n'existe pas de droit d'accès
   ```shell
   lowatt-grdf donnees-consos-publiees --bas 09999999900112 --from-date 2021-01-01 --to-date 2021-10-15
   ```
1. Cas non passant : Erreur technique du serveur GRDF
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-publiees --bas GI999159 --period 2023
   ```
1. Cas non passant : MHS du PCE sur lequel il existe un droit d'accès
   ```shell
   lowatt-grdf donnees-consos-publiees --bas GI999092 --from-date 2021-08-18 --to-date 2023-08-17
   ```
1. Cas non passant : Droit d'accès expiré
   ```shell
   lowatt-grdf donnees-consos-publiees --bas 09999999930215 --from-date 2023-01-01 --to-date 2023-09-01
   ```
1. Cas non passant : Droit d'accès révoqué par le Titulaire
   ```shell
   lowatt-grdf donnees-consos-publiees --bas 09999999932770 --from-date 2023-01-01 --to-date 2023-02-01
   ```
1. Cas non passant : Droit d'accès révoqué par le Tiers
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-publiees --bas 09999999970626 --period 2023
   ```
1. Cas non passant : Date de début demandée excédant 5 ans d'historique
   ```shell
   lowatt-grdf donnees-consos-publiees --bas 09999999900617 --from-date 2018-01-01 --to-date 2021-10-15
   ```
1. Cas non passant : Erreur technique sur le streaming lors de l’exécution de la requête
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-publiees --bas GI999054 --period 2023
   ```

## Consommations informatives

### Consulter les données de consommation informatives

1. Cas passant : MM Données informatives
   ```shell
   # Doesn't work with PCE GI999947 as Staging API v6 documentation says it should, but works with GI151947.
   # The support team is aware of this issue so it should be fixed in the next version.
   lowatt-grdf donnees-consos-informatives --bas GI151947 --from-date 2023-02-26 --to-date 2023-02-28
   ```
1. Cas passant : 1M Données informatives
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-informatives --bas 09999999928289 --period 2023-09
   ```
1. Cas non passant : Format du paramètre période incorrect 
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-informatives --bas 09999999928283 --period 2023-09-01
   ```
1. Cas non passant : Format du paramètre id_pce incorrect
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-informatives --bas 0999999992828 --period 2023-09
   ```
1. Cas non passant : Erreur technique du serveur GRDF
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-informatives --bas 09999999900617 --period 2023
   ```
1. Cas non passant : Contrat avec GRDF expiré
   ```shell
   # Not implemented yet
   # lowatt-grdf donnees-consos-informatives --bas GI999055 --period 2023
   ```
1. Cas non passant : Droit d'accès révoqué par le Titulaire
   ```shell
   lowatt-grdf donnees-consos-informatives --bas 09999999932770 --from-date 2019-09-01 --to-date 2019-10-01
   ```
1. Cas non passant : Données informatives hors du périmètre du droit d'accès demandé
   ```shell
   lowatt-grdf donnees-consos-informatives --bas 09999999975102 --from-date 2023-02-26 --to-date 2023-02-28
   ```
1. Cas non passant : Date de début demandée excédant 3 ans d'historique
   ```shell
   lowatt-grdf donnees-consos-informatives --bas GI999947 --from-date 2020-02-26 --to-date 2023-02-28
   ```
1. Cas non passant : Date de fin supérieure à la date du jour
   ```shell
   lowatt-grdf donnees-consos-informatives --bas GI999947 --from-date 2023-02-26 --to-date 2050-02-28
   ```

## Injections publiées

### Consulter les données d'injection publiées

1. Cas passant : JJ Données publiées
   ```shell
   lowatt-grdf donnees-injections-publiees --bas GI999150 --from-date 2023-07-01 --to-date 2023-07-17
   ```
1. Cas non passant : Droit d'accès ayant un état différent d'Actif, Obsolète ou Révoqué
   ```shell
   lowatt-grdf donnees-injections-publiees --bas GI999602 --from-date 2023-07-01 --to-date 2023-07-17
   ```
1. Cas non passant : Date de début demandée excédant 5 ans d'historique
   ```shell
   lowatt-grdf donnees-injections-publiees --bas GI999150 --from-date 2018-07-01 --to-date 2023-07-17
   ```
1. Cas non passant : Date de fin supérieure à la date du jour
   ```shell
   lowatt-grdf donnees-injections-publiees --bas GI999947 --from-date 2023-07-01 --to-date 2050-07-17
   ```

## Données contractuelles

### Consulter les données contractuelles

1. Cas passant : Consulter les données contractuelles
   ```shell
   lowatt-grdf donnees-contractuelles --bas 09999999900617
   ```
1. Cas non passant : Données contractuelles hors du périmètre du droit d'accès demandé
   ```shell
   lowatt-grdf donnees-contractuelles --bas 09999999975102
   ```

## Données techniques

### Consulter les données techniques

1. Cas passant : Consulter les données techniques
   ```shell
   lowatt-grdf donnees-techniques --bas 09999999975102
   ```
1. Cas non passant : Données techniques hors du périmètre du droit d'accès demandé
   ```shell
   lowatt-grdf donnees-techniques --bas GI999055
   ```
