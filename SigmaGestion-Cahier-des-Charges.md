# SigmaGestion — Cahier des charges

**Logiciel de gestion de secrétariat bureautique**
Version 1.0 · Document de référence projet
Cible : Cameroun (Afrique centrale, zone CEMAC)

---

## Sommaire

1. [Présentation du projet](#1-présentation-du-projet)
2. [Contexte et réalités du terrain](#2-contexte-et-réalités-du-terrain)
3. [Objectifs et indicateurs de succès](#3-objectifs-et-indicateurs-de-succès)
4. [Acteurs et rôles](#4-acteurs-et-rôles)
5. [Périmètre fonctionnel](#5-périmètre-fonctionnel)
6. [Spécifications fonctionnelles détaillées](#6-spécifications-fonctionnelles-détaillées)
7. [Règles de gestion](#7-règles-de-gestion)
8. [Modèle de données](#8-modèle-de-données)
9. [Architecture technique](#9-architecture-technique)
10. [Spécification de l'API](#10-spécification-de-lapi)
11. [Direction artistique et UX/UI](#11-direction-artistique-et-uxui)
12. [Sécurité](#12-sécurité)
13. [Performance et contraintes locales](#13-performance-et-contraintes-locales)
14. [Découpage en lots et planning](#14-découpage-en-lots-et-planning)
15. [Stratégie de tests et recette](#15-stratégie-de-tests-et-recette)
16. [Déploiement et mise en production](#16-déploiement-et-mise-en-production)
17. [Exploitation et maintenance](#17-exploitation-et-maintenance)
18. [Évolutions envisagées (hors périmètre v1)](#18-évolutions-envisagées-hors-périmètre-v1)
19. [Annexes](#19-annexes)

---

## 1. Présentation du projet

### 1.1 Identité

| Élément | Valeur |
|---|---|
| Nom du logiciel | **SigmaGestion** |
| Nature | Application web progressive (PWA) multi-locataire |
| Domaine | Gestion opérationnelle et commerciale d'un secrétariat bureautique |
| Langue principale | Français |
| Devise | Franc CFA (XAF), sans décimales |
| Fuseau horaire | Africa/Douala (UTC+1) |

### 1.2 Description en une phrase

SigmaGestion permet au propriétaire d'un secrétariat bureautique de piloter son activité au quotidien : enregistrer chaque prestation vendue, suivre automatiquement la consommation de ses consommables, être alerté avant la rupture de stock, connaître son chiffre d'affaires en temps réel, et déléguer la saisie à ses employés sans perdre le contrôle.

### 1.3 Proposition de valeur

Aujourd'hui la majorité des secrétariats camerounais tiennent leur comptabilité dans un cahier de brouillon. Trois problèmes en découlent :

- **La fuite de recette.** Le propriétaire ne peut pas vérifier ce que l'employé a réellement encaissé quand il n'est pas là.
- **La rupture surprise.** On découvre qu'il n'y a plus de ramettes ou de spirales quand un client est déjà au comptoir.
- **L'absence de vision.** Impossible de dire quel service rapporte le plus, ni si la journée a été meilleure que la veille.

SigmaGestion répond à ces trois points par : une saisie de prestation en moins de 10 secondes, un décompte automatique du stock à chaque vente, et des notifications push (stock faible + bilan de chiffre d'affaires toutes les 2 heures) adressées au propriétaire même quand il est loin de la boutique.

---

## 2. Contexte et réalités du terrain

### 2.1 Les services d'un secrétariat bureautique camerounais

Le catalogue standard, tel qu'observé sur le terrain, se répartit en deux familles selon qu'une vente **prélève ou non du stock physique**.

**Services consommateurs de stock**

| Service | Consommables prélevés | Unité de facturation typique |
|---|---|---|
| Impression noir & blanc | Papier A4, toner noir | La page |
| Impression couleur | Papier A4, toners C/M/J/N | La page |
| Photocopie | Papier A4/A3, toner noir | La page |
| Reliure spirale | Spirale plastique, couverture transparente, dos cartonné | Le document |
| Plastification | Pochette à plastifier (A4, A5, format carte) | La pièce |

**Services non consommateurs de stock**

| Service | Nature | Unité de facturation typique |
|---|---|---|
| Saisie de document | Main-d'œuvre | La page saisie |
| Numérisation (scan) | Usage machine | La page ou le document |
| Envoi par e-mail / transfert de fichier | Service annexe | Le forfait |
| Recherche internet / impression de documents en ligne | Main-d'œuvre + connexion | Le forfait |

> **Note de conception majeure.** Le système ne doit pas coder en dur cette distinction. Chaque service porte un booléen `consomme_stock`, et lorsqu'il est vrai, une **nomenclature** décrit quel consommable est prélevé et en quelle quantité par unité vendue. Le propriétaire peut donc créer ses propres services sans intervention du développeur.

### 2.2 Contraintes spécifiques au contexte camerounais

| Contrainte | Impact sur la conception |
|---|---|
| Coupures d'électricité fréquentes (délestage ENEO) | L'application doit fonctionner hors ligne en lecture et en saisie, puis se synchroniser au retour du réseau. Aucune perte de saisie tolérée. |
| Connexion internet instable et coûteuse (données mobiles) | Bundle JS léger, images optimisées, requêtes API minimisées et mises en cache, pas de rechargement complet. |
| Parc majoritairement mobile (Android d'entrée de gamme) | Conception **mobile-first**, PWA installable, cible de performance sur appareil à 2 Go de RAM. |
| Paiements en espèces majoritaires + Mobile Money (MTN MoMo, Orange Money) | Le mode de règlement est un champ obligatoire. Intégration MoMo prévue en v2, mais le modèle de données la prépare dès la v1. |
| Prix bas et arrondis (25, 50, 100 FCFA) | Montants en entiers, jamais de décimales. Pas de centimes. |
| Clients réguliers payant « à crédit » (fin de mois) | Gestion d'un statut de règlement `payé / partiel / crédit` et d'une fiche client optionnelle. |
| Employés à faible littératie numérique | Interface de saisie extrêmement simple, gros boutons tactiles, vocabulaire métier local, zéro jargon technique. |
| Rotation du personnel | Création et désactivation d'un compte employé en moins de 30 secondes. Aucune suppression de données historiques. |

---

## 3. Objectifs et indicateurs de succès

### 3.1 Objectifs fonctionnels

1. Enregistrer une prestation complète (service, quantité, montant, mode de paiement) en **moins de 10 secondes** et **moins de 4 interactions**.
2. Mettre à jour le stock **automatiquement et immédiatement** à chaque prestation, sans double saisie.
3. Prévenir le propriétaire **avant** la rupture, via un seuil d'alerte qu'il définit lui-même.
4. Informer le propriétaire de son chiffre d'affaires **toutes les 2 heures**, uniquement pendant sa plage horaire de travail configurée.
5. Restituer un journal de caisse quotidien vérifiable et non modifiable a posteriori sans trace.

### 3.2 Indicateurs de succès mesurables

| Indicateur | Cible v1 |
|---|---|
| Temps de saisie d'une prestation (médiane, mobile) | ≤ 10 s |
| Temps de chargement initial (3G, cache vide) | ≤ 3 s |
| Temps de chargement (cache chaud) | ≤ 1 s |
| Poids du bundle JS initial (gzip) | ≤ 200 Ko |
| Score Lighthouse Performance (mobile) | ≥ 85 |
| Score Lighthouse Accessibilité | ≥ 95 |
| Disponibilité mensuelle | ≥ 99 % |
| Délai d'envoi d'une alerte stock après franchissement du seuil | ≤ 60 s |
| Taux de perte de saisie en mode hors ligne | 0 % |

---

## 4. Acteurs et rôles

### 4.1 Les quatre rôles

| Rôle | Description | Portée |
|---|---|---|
| **Super-administrateur** | Éditeur du logiciel. Gère les comptes secrétariats, les abonnements, la supervision technique. | Toute la plateforme |
| **Propriétaire** | Détient un ou plusieurs secrétariats. Configure tout, voit tout, reçoit les notifications. | Ses secrétariats |
| **Gérant** *(optionnel)* | Employé de confiance délégué à la gestion d'un point de vente. Peut faire des entrées de stock et voir les rapports du jour, mais ne peut pas modifier les prix ni gérer les comptes. | Un secrétariat |
| **Employé** | Opérateur au comptoir. Enregistre les prestations, encaisse, consulte le stock. | Un secrétariat, sa propre session de caisse |

### 4.2 Matrice des permissions

| Action | Propriétaire | Gérant | Employé |
|---|:---:|:---:|:---:|
| Créer / modifier un secrétariat | ✅ | ❌ | ❌ |
| Créer / désactiver un compte employé | ✅ | ❌ | ❌ |
| Créer / modifier un service et son prix | ✅ | ❌ | ❌ |
| Définir la nomenclature d'un service | ✅ | ❌ | ❌ |
| Créer un consommable, fixer son seuil d'alerte | ✅ | ❌ | ❌ |
| Enregistrer une entrée de stock (réapprovisionnement) | ✅ | ✅ | ❌ |
| Enregistrer une prestation / encaisser | ✅ | ✅ | ✅ |
| Annuler une prestation *(avec motif)* | ✅ | ✅ | ❌ |
| Ouvrir / clôturer une session de caisse | ✅ | ✅ | ✅ |
| Enregistrer une dépense | ✅ | ✅ | ❌ |
| Voir le tableau de bord du jour | ✅ | ✅ | Version limitée |
| Voir les rapports historiques et les marges | ✅ | ❌ | ❌ |
| Configurer la plage horaire et les notifications | ✅ | ❌ | ❌ |
| Exporter les données (CSV / PDF) | ✅ | ❌ | ❌ |
| Consulter le journal d'audit | ✅ | ❌ | ❌ |

> L'employé voit son propre chiffre de session (pour justifier sa caisse) mais **jamais** les marges, les prix d'achat, ni l'historique global.

---

## 5. Périmètre fonctionnel

### 5.1 Modules de la version 1

| # | Module | Priorité |
|---|---|---|
| M1 | Authentification, comptes et multi-locataire | Indispensable |
| M2 | Gestion du catalogue de services et tarifs | Indispensable |
| M3 | Gestion des consommables et du stock | Indispensable |
| M4 | Point de vente — enregistrement des prestations | Indispensable |
| M5 | Caisse : sessions, dépenses, journal quotidien | Indispensable |
| M6 | Notifications push (stock bas + bilan périodique) | Indispensable |
| M7 | Tableau de bord et rapports | Indispensable |
| M8 | Gestion des employés | Indispensable |
| M9 | Clients et créances | Souhaitable |
| M10 | Reçus imprimables / partageables | Souhaitable |
| M11 | Mode hors ligne et synchronisation | Indispensable |
| M12 | Journal d'audit | Souhaitable |

### 5.2 Explicitement hors périmètre v1

- Intégration directe aux API Mobile Money (MTN MoMo Collections, Orange Money) — préparée mais non implémentée.
- Application mobile native (Android/iOS) — la PWA fait office.
- Comptabilité normalisée OHADA / liasse fiscale.
- Gestion de la paie des employés.
- Multi-devise.
- Portail client en libre-service (dépôt de fichiers à imprimer en ligne).

---

## 6. Spécifications fonctionnelles détaillées

### M1 — Authentification, comptes et multi-locataire

**M1.1 — Inscription du propriétaire**
Formulaire : nom complet, numéro de téléphone (format camerounais `+237 6XX XXX XXX`), e-mail (facultatif), mot de passe. Le téléphone est l'identifiant principal, car plus fiable que l'e-mail dans ce contexte.

**M1.2 — Création du premier secrétariat**
Immédiatement après l'inscription, un assistant en 3 écrans :
1. Identité du secrétariat (nom, quartier, ville, téléphone affiché sur les reçus).
2. Sélection des services proposés parmi une liste pré-remplie (impression N&B, photocopie, saisie, reliure, plastification, numérisation) avec un prix par défaut modifiable.
3. Déclaration du stock initial pour les consommables des services retenus.

> Cet assistant est critique : c'est lui qui détermine si l'utilisateur adopte le logiciel ou l'abandonne. Il doit être franchissable en moins de 3 minutes et **interruptible** (reprise possible plus tard).

**M1.3 — Connexion**
Par téléphone + mot de passe. Session persistante longue durée (30 jours) car les employés se reconnectent chaque matin. Option « code PIN à 4 chiffres » pour le déverrouillage rapide sur un appareil déjà authentifié.

**M1.4 — Isolation multi-locataire**
Toute donnée métier est rattachée à un `secretariat`. Une requête ne peut jamais retourner de données appartenant à un autre secrétariat. L'isolation est appliquée au niveau de la couche d'accès aux données (voir §12.3), pas seulement au niveau de la vue.

**M1.5 — Réinitialisation du mot de passe**
Par code à 6 chiffres envoyé par SMS. En v1, un fallback administrateur est prévu si le fournisseur SMS n'est pas encore branché.

---

### M2 — Catalogue de services et tarifs

**M2.1 — Créer un service**
Champs : nom, catégorie, unité de facturation (page / document / pièce / forfait), prix de vente unitaire (entier XAF), actif oui/non, `consomme_stock` oui/non, couleur et icône (pour le repérage visuel au comptoir).

**M2.2 — Définir la nomenclature d'un service**
Si `consomme_stock` est vrai, le propriétaire associe un ou plusieurs consommables avec la quantité prélevée **par unité vendue**.

*Exemple : « Reliure spirale A4 » →*
- *1 × spirale plastique 12 mm*
- *1 × couverture transparente*
- *1 × dos cartonné*

*Exemple : « Impression N&B » →*
- *1 × feuille A4*
- *0,004 × cartouche toner noir* (soit 250 pages par cartouche)

La quantité accepte des décimales (précision 4) pour modéliser le rendement des toners.

**M2.3 — Tarification dégressive** *(souhaitable)*
Possibilité de définir des paliers : 1–9 pages à 50 F, 10–49 pages à 40 F, 50+ à 30 F. Le prix appliqué est calculé automatiquement à la saisie.

**M2.4 — Historique des prix**
Un changement de prix ne modifie jamais les prestations déjà enregistrées. Le prix unitaire est **copié** dans la ligne de prestation au moment de la vente.

---

### M3 — Consommables et stock

**M3.1 — Fiche consommable**
Champs : nom, unité de mesure (feuille, spirale, pochette, cartouche, ramette…), **prix d'achat unitaire** (XAF), **quantité en stock**, **seuil d'alerte**, seuil critique (facultatif), fournisseur habituel (facultatif), actif oui/non.

Le prix d'achat unitaire est ce qui permet de calculer le coût de revient et donc la marge par prestation.

**M3.2 — Entrée de stock (réapprovisionnement)**
Formulaire : consommable, quantité entrante, prix d'achat total du lot, date, fournisseur, référence de facture (facultatif).
Le système recalcule le **prix d'achat unitaire moyen pondéré** (CUMP) :

```
nouveau_pu = (stock_actuel × pu_actuel + qte_entrante × pu_lot) / (stock_actuel + qte_entrante)
```

Cette méthode est retenue plutôt que le FIFO car elle est plus simple à comprendre pour l'utilisateur final et suffisante pour ce niveau d'activité.

**M3.3 — Sortie automatique**
À chaque prestation validée portant sur un service consommateur, le stock est décrémenté selon la nomenclature × la quantité vendue. Un mouvement de stock de type `SORTIE_VENTE` est enregistré et lié à la prestation.

**M3.4 — Ajustement d'inventaire**
Le propriétaire peut corriger un stock (casse, vol, erreur de comptage, perte). Un motif est **obligatoire**. Mouvement de type `AJUSTEMENT`, signé positif ou négatif.

**M3.5 — Alerte de stock faible**
Dès qu'un mouvement fait passer la quantité **sous ou au niveau du seuil d'alerte**, une notification push part vers le propriétaire (et le gérant si activé). Anti-spam : une seule alerte par consommable toutes les 24 h tant que le stock n'est pas remonté au-dessus du seuil.

**M3.6 — Blocage sur stock insuffisant**
Si une prestation demandée nécessite plus de stock que disponible, l'interface affiche un avertissement clair indiquant le consommable manquant et la quantité maximale réalisable. Deux comportements, au choix du propriétaire dans les réglages :
- **Bloquer** la vente (rigueur d'inventaire) ;
- **Autoriser en négatif** avec avertissement (pragmatisme terrain — recommandé par défaut, car dans la réalité on sert le client puis on régularise).

**M3.7 — Journal des mouvements**
Liste filtrable et horodatée de tous les mouvements : entrée, sortie de vente, ajustement, annulation. Chaque ligne indique l'auteur.

---

### M4 — Point de vente (le cœur du produit)

**M4.1 — Écran de saisie**
Grille de « tuiles services » tactiles, triées par fréquence d'usage. Un appui ajoute la ligne au ticket en cours avec une quantité de 1. Un second appui incrémente.

**M4.2 — Ticket en cours**
Panneau latéral (desktop) ou tiroir bas (mobile) affichant les lignes, la quantité éditable, le montant par ligne, une remise éventuelle, et le **total en gros caractères**.

**M4.3 — Encaissement**
Sélection du mode de règlement : `Espèces`, `MTN MoMo`, `Orange Money`, `Crédit (à payer plus tard)`.
Pour les espèces : champ « montant reçu » avec calcul automatique de la monnaie à rendre — fonction très demandée au comptoir.
Pour le crédit : rattachement obligatoire à un client.

**M4.4 — Validation**
À la validation, en une seule transaction atomique :
- la prestation est créée avec son numéro séquentiel (`SEC001-20260902-0042`) ;
- les prix unitaires et coûts de revient sont figés ;
- les mouvements de stock sont générés ;
- les seuils d'alerte sont évalués ;
- la session de caisse est mise à jour.

**M4.5 — Annulation**
Uniquement par le propriétaire ou le gérant, avec motif obligatoire. L'annulation **ne supprime pas** la prestation : elle passe au statut `ANNULEE` et génère des mouvements de stock inverses. La traçabilité est totale.

**M4.6 — Reçu**
Génération d'un reçu au format ticket (58 mm et 80 mm) imprimable, et d'un lien de partage WhatsApp — canal de communication dominant au Cameroun.

---

### M5 — Caisse

**M5.1 — Session de caisse**
Chaque employé ouvre une session en début de service en déclarant le **fond de caisse** initial. Toutes ses prestations y sont rattachées.

**M5.2 — Clôture**
En fin de service, l'employé déclare le **montant physiquement compté**. Le système affiche l'écart avec le montant théorique :

```
théorique = fond_initial + encaissements_espèces − dépenses_espèces
écart = compté − théorique
```

Un écart non nul exige un commentaire. Le propriétaire reçoit une notification si l'écart dépasse un seuil qu'il configure.

**M5.3 — Dépenses**
Enregistrement des sorties de caisse : achat de consommables, transport, connexion internet, carburant du groupe électrogène, salaires, divers. Catégorie + montant + justificatif photo facultatif.

**M5.4 — Journal quotidien**
Vue synthétique par jour : total encaissé par mode de règlement, total des dépenses, solde, nombre de prestations, liste des sessions.

---

### M6 — Notifications push

C'est un module structurant du projet. Il repose sur la **Web Push API** avec chiffrement VAPID, ce qui permet de notifier même quand l'application est fermée (sur Android/Chrome ; sur iOS ≥ 16.4 uniquement si la PWA est installée à l'écran d'accueil — à indiquer dans l'aide).

**M6.1 — Abonnement**
Au premier accès, une explication contextuelle précède la demande de permission navigateur (ne jamais déclencher la popup native à froid — c'est le meilleur moyen d'obtenir un refus définitif). Un utilisateur peut avoir plusieurs appareils abonnés.

**M6.2 — Notification « Stock faible »**
| Élément | Valeur |
|---|---|
| Déclencheur | Événement — franchissement du seuil lors d'un mouvement |
| Destinataires | Propriétaire, et gérant si l'option est active |
| Titre | `Stock faible — {nom du secrétariat}` |
| Corps | `Papier A4 : il reste 40 feuilles (seuil 100). Pensez à réapprovisionner.` |
| Action | Ouvre la fiche du consommable |
| Anti-répétition | 1 par consommable / 24 h |

**M6.3 — Notification « Chiffre d'affaires » toutes les 2 heures**

C'est l'exigence phare. Fonctionnement :

- Le propriétaire configure une **plage horaire de travail** par secrétariat, jour par jour (ex. lundi–vendredi 07 h 30 → 19 h 00, samedi 08 h 00 → 15 h 00, dimanche fermé).
- Il configure un **intervalle** (par défaut 2 h, valeurs possibles : 1 h, 2 h, 3 h, 4 h).
- Une tâche périodique Celery Beat s'exécute **toutes les 15 minutes**. Pour chaque secrétariat, elle vérifie : sommes-nous dans la plage horaire du jour ? l'intervalle est-il écoulé depuis le dernier envoi ? Si oui, elle calcule et envoie.

Contenu de la notification :

```
Titre : Bilan 14h00 — Sigma Bureautique Ébolowa
Corps  : 47 500 F encaissés depuis 12h00 · 68 200 F aujourd'hui
         18 prestations · Photocopie en tête
```

Détail du calcul :
- CA de l'intervalle écoulé (somme des prestations non annulées) ;
- CA cumulé du jour ;
- nombre de prestations ;
- service le plus vendu sur l'intervalle ;
- comparaison avec la même tranche horaire de la veille (flèche ↑ / ↓ en pourcentage).

Un **bilan de clôture** est envoyé à la fin de la plage horaire avec le récapitulatif complet de la journée (CA, dépenses, solde, marge estimée).

**M6.4 — Autres notifications**
| Événement | Destinataire |
|---|---|
| Écart de caisse supérieur au seuil | Propriétaire |
| Annulation d'une prestation | Propriétaire |
| Ouverture / clôture de session | Propriétaire (option désactivable) |
| Créance client échue | Propriétaire |

**M6.5 — Centre de notifications**
Toute notification push est également persistée en base et consultable dans l'application (cloche avec compteur), car une push peut être manquée. États : non lue / lue / archivée.

**M6.6 — Réglages fins**
Le propriétaire peut activer/désactiver chaque type indépendamment et définir un mode « Ne pas déranger » global.

---

### M7 — Tableau de bord et rapports

**M7.1 — Tableau de bord propriétaire**
En haut, l'information la plus consultée : le **chiffre d'affaires du jour**, en très grand, avec la variation par rapport à la veille. Ensuite :
- courbe du CA sur les 30 derniers jours ;
- répartition du CA par service (barres horizontales, pas de camembert — moins lisible) ;
- top 5 des services ;
- consommables sous seuil (bloc d'alerte visible immédiatement) ;
- performance par employé (CA généré, nombre de prestations) ;
- marge brute estimée (CA − coût des consommables consommés).

**M7.2 — Tableau de bord employé**
Réduit à l'essentiel : sa session en cours, son total encaissé, ses dernières prestations, l'état du stock.

**M7.3 — Rapports**
| Rapport | Contenu |
|---|---|
| Ventes | Par période, service, employé, mode de règlement |
| Stock | État actuel, valorisation du stock, historique des mouvements, consommation par période |
| Rentabilité | CA, coût des consommables, marge brute, marge par service |
| Caisse | Sessions, écarts, dépenses par catégorie |
| Clients | Encours de crédit, historique |

**M7.4 — Exports**
CSV pour toutes les listes, PDF pour les rapports de synthèse et les reçus.

---

### M8 — Gestion des employés

**M8.1 — Ajouter un employé**
Le propriétaire saisit : nom, téléphone, rôle (employé ou gérant), secrétariat de rattachement. Le système génère un mot de passe provisoire affiché à l'écran et envoyable par WhatsApp. Changement obligatoire à la première connexion.

**M8.2 — Désactiver un employé**
Jamais de suppression : désactivation. Les prestations historiques restent attribuées à leur auteur. Une session ouverte est automatiquement clôturée.

**M8.3 — Suivi d'activité**
Fiche employé : historique de ses sessions, CA généré, écarts de caisse, prestations annulées le concernant.

---

### M9 — Clients et créances

Fiche client légère : nom, téléphone, type (particulier / entreprise / administration), plafond de crédit facultatif.
Suivi de l'encours, historique des prestations, enregistrement des règlements partiels, relance manuelle par WhatsApp.

---

### M11 — Mode hors ligne et synchronisation

**M11.1 — Lecture hors ligne**
Le catalogue de services, les consommables, la session en cours et les prestations du jour sont mis en cache local (IndexedDB).

**M11.2 — Écriture hors ligne**
Une prestation enregistrée sans réseau est stockée dans une file locale avec un `client_uuid` généré côté navigateur. L'interface affiche un badge « en attente de synchronisation ».

**M11.3 — Synchronisation**
Au retour du réseau, la file est envoyée par lots à un endpoint dédié. Le `client_uuid` garantit l'**idempotence** : un rejeu ne crée jamais de doublon.

**M11.4 — Résolution de conflit**
Les prestations sont des faits ajoutés, non modifiés : le risque de conflit est faible. Pour le stock, le serveur fait autorité et recalcule les quantités à partir des mouvements. Si une synchronisation fait passer un stock en négatif, la prestation est acceptée et une alerte de régularisation est levée.

---

## 7. Règles de gestion

| Code | Règle |
|---|---|
| RG-01 | Tous les montants sont des **entiers** en XAF. Aucune décimale nulle part dans l'interface ni en base. |
| RG-02 | Le prix unitaire et le coût de revient unitaire sont **figés** dans la ligne de prestation au moment de la validation. |
| RG-03 | Une prestation validée n'est jamais modifiée ni supprimée : elle est annulée avec motif et contre-passation des mouvements de stock. |
| RG-04 | La décrémentation du stock, la création de la prestation et la mise à jour de la session se font dans **une seule transaction atomique**. |
| RG-05 | Un service avec `consomme_stock = false` ne génère aucun mouvement de stock. |
| RG-06 | Un service avec `consomme_stock = true` **doit** avoir au moins une ligne de nomenclature pour être activable. |
| RG-07 | Le prix d'achat unitaire d'un consommable est recalculé en CUMP à chaque entrée de stock. |
| RG-08 | L'alerte de stock faible est émise au franchissement du seuil, au plus une fois par 24 h par consommable. |
| RG-09 | La notification de CA n'est envoyée que si l'instant courant est dans la plage horaire active du secrétariat pour le jour concerné. |
| RG-10 | Aucun envoi de notification de CA si le CA de l'intervalle est nul **et** que le CA du jour est nul (évite le bruit d'un jour creux). |
| RG-11 | Un employé ne peut ouvrir qu'**une seule** session de caisse à la fois par secrétariat. |
| RG-12 | La clôture d'une session avec écart non nul exige un commentaire d'au moins 10 caractères. |
| RG-13 | Une prestation en mode « Crédit » exige un client rattaché. |
| RG-14 | Toute requête est filtrée par le `secretariat` de l'utilisateur authentifié, sans exception. |
| RG-15 | Le numéro de prestation est unique par secrétariat et suit le format `{CODE_SEC}-{AAAAMMJJ}-{séquence sur 4}`. |
| RG-16 | Les opérations sensibles (changement de prix, ajustement de stock, annulation, désactivation de compte) sont journalisées avec auteur, horodatage et valeurs avant/après. |

---

## 8. Modèle de données

### 8.1 Schéma relationnel

```
┌──────────────────┐
│  Utilisateur     │  téléphone (unique), nom, rôle, actif,
│  (AbstractUser)  │  doit_changer_mdp, code_pin_hash
└────────┬─────────┘
         │ N
         │
         │ 1  ┌──────────────────┐ 1     N ┌────────────────────┐
         └────│   Secretariat    │─────────│  PlageHoraire      │
              │  nom, code,      │         │  jour_semaine,     │
              │  ville, quartier │         │  heure_debut,      │
              │  telephone,      │         │  heure_fin, actif  │
              │  proprietaire FK │         └────────────────────┘
              │  devise, actif   │
              └──┬───┬───┬───┬───┘
                 │   │   │   │
     ┌───────────┘   │   │   └──────────────────┐
     │ N             │ N │ N                    │ 1
┌────▼────────┐ ┌────▼───▼──────┐    ┌──────────▼───────────┐
│  Service    │ │  Consommable  │    │ ParametreNotification│
│ nom, prix,  │ │ nom, unite,   │    │ intervalle_ca_min,   │
│ unite,      │ │ prix_achat_u, │    │ alerte_stock_on,     │
│ consomme_   │ │ qte_stock,    │    │ alerte_ca_on,        │
│ stock,      │ │ seuil_alerte, │    │ seuil_ecart_caisse,  │
│ actif,      │ │ seuil_crit,   │    │ dernier_envoi_ca     │
│ couleur     │ │ actif         │    └──────────────────────┘
└──┬──────────┘ └──┬────────────┘
   │ 1             │ 1
   │               │
   │ N          N  │
┌──▼───────────────▼──┐
│  NomenclatureService│   service FK, consommable FK,
│  qte_par_unite      │   quantité décimale (4 déc.)
└─────────────────────┘

┌──────────────────────┐ 1    N ┌──────────────────────┐
│    Prestation        │────────│  LignePrestation     │
│ numero (unique/sec)  │        │ service FK,          │
│ secretariat FK       │        │ quantite,            │
│ session_caisse FK    │        │ prix_unitaire (figé) │
│ employe FK           │        │ cout_unitaire (figé) │
│ client FK (null)     │        │ remise, montant      │
│ montant_total        │        └──────────────────────┘
│ montant_recu         │
│ mode_reglement       │        ┌──────────────────────┐
│ statut_reglement     │   N    │ MouvementStock       │
│ statut (VALIDEE/     │◄───────│ consommable FK,      │
│         ANNULEE)     │        │ type (ENTREE/SORTIE_ │
│ motif_annulation     │        │  VENTE/AJUSTEMENT/   │
│ client_uuid (idemp.) │        │  ANNULATION),        │
│ cree_le, synchro_le  │        │ quantite (signée),   │
└──────────────────────┘        │ stock_avant/apres,   │
                                │ prix_achat_unitaire, │
┌──────────────────────┐        │ prestation FK (null),│
│  SessionCaisse       │        │ motif, auteur FK     │
│ employe FK, sec FK   │        └──────────────────────┘
│ fond_initial,        │
│ montant_theorique,   │        ┌──────────────────────┐
│ montant_compte,      │        │      Depense         │
│ ecart, commentaire,  │        │ session FK, categorie│
│ ouverte_le,          │        │ montant, description │
│ fermee_le, statut    │        │ justificatif (image) │
└──────────────────────┘        └──────────────────────┘

┌──────────────────────┐        ┌──────────────────────┐
│      Client          │        │  AbonnementPush      │
│ nom, telephone, type │        │ utilisateur FK,      │
│ plafond_credit,      │        │ endpoint, p256dh,    │
│ encours              │        │ auth, user_agent,    │
└──────────────────────┘        │ actif, cree_le       │
                                └──────────────────────┘
┌──────────────────────┐        ┌──────────────────────┐
│    Notification      │        │   JournalAudit       │
│ destinataire FK,     │        │ auteur FK, action,   │
│ secretariat FK, type,│        │ modele, objet_id,    │
│ titre, corps, data,  │        │ valeurs_avant/apres, │
│ lue, envoyee_push,   │        │ ip, horodatage       │
│ cree_le              │        └──────────────────────┘
└──────────────────────┘
```

### 8.2 Points d'attention sur le modèle

- **`Consommable.qte_stock`** est un champ dénormalisé pour la performance de lecture. Il est **toujours** mis à jour via un mouvement de stock, jamais directement, et une commande de management `recalculer_stocks` permet de le reconstruire à partir des mouvements en cas de doute.
- **`Prestation.client_uuid`** est un UUID généré côté client, contraint en unicité. C'est la clé de l'idempotence de la synchronisation hors ligne.
- **`LignePrestation.cout_unitaire`** est calculé à la validation en sommant `qte_par_unite × prix_achat_unitaire` de la nomenclature. Il fige la marge historique même si les prix d'achat évoluent.
- **`ParametreNotification.dernier_envoi_ca`** évite les doublons et permet de calculer l'intervalle réel écoulé.
- Index composites recommandés : `(secretariat, cree_le)` sur Prestation, `(consommable, cree_le)` sur MouvementStock, `(destinataire, lue)` sur Notification.

---

## 9. Architecture technique

### 9.1 Vue d'ensemble

```
   Navigateur (PWA React)
   ├── Service Worker ── cache + file de synchro + réception push
   │
   ▼ HTTPS / JSON
┌──────────────────────────────────────────┐
│  Nginx  — TLS, compression, statiques    │
└───────────────┬──────────────────────────┘
                │
        ┌───────▼────────┐        ┌──────────────────┐
        │ Gunicorn       │        │ Celery Worker    │
        │ Django + DRF   │◄──────►│ Celery Beat      │
        └───────┬────────┘  Redis └────────┬─────────┘
                │                          │
        ┌───────▼────────┐         ┌───────▼────────┐
        │  PostgreSQL    │         │  Web Push      │
        │                │         │  (VAPID)       │
        └────────────────┘         └────────────────┘
```

### 9.2 Backend

| Composant | Choix | Justification |
|---|---|---|
| Framework | **Django 5.x** | Demandé. ORM robuste, admin natif, écosystème mature. |
| API | **Django REST Framework** | Standard de fait, sérialisation et permissions solides. |
| Base de données | **PostgreSQL 16** | Transactions fiables, contraintes, `SELECT FOR UPDATE` pour le stock concurrent. |
| Authentification | **djangorestframework-simplejwt** | Access token 60 min, refresh token 30 j, rotation + blacklist. |
| File de tâches | **Celery 5 + Redis** | Notifications asynchrones, tâches périodiques. |
| Planificateur | **Celery Beat** (`django-celery-beat`) | Tâches en base, modifiables sans redéploiement. |
| Push | **pywebpush** (VAPID) | Standard Web Push, pas de dépendance à Firebase. |
| Documentation API | **drf-spectacular** | OpenAPI 3 généré automatiquement. |
| Filtres | **django-filter** | Filtrage déclaratif des listes. |
| Variables d'env. | **django-environ** | Aucun secret dans le code. |
| Journalisation | **structlog** + Sentry | Logs structurés exploitables. |

**Structure des applications Django**

```
sigmagestion/
├── config/              # settings (base/dev/prod), urls, celery, wsgi/asgi
├── apps/
│   ├── comptes/         # Utilisateur, authentification, permissions
│   ├── secretariats/    # Secretariat, PlageHoraire, ParametreNotification
│   ├── catalogue/       # Service, NomenclatureService
│   ├── stocks/          # Consommable, MouvementStock, services de stock
│   ├── ventes/          # Prestation, LignePrestation, synchronisation
│   ├── caisse/          # SessionCaisse, Depense
│   ├── clients/         # Client, créances
│   ├── notifications/   # AbonnementPush, Notification, tâches Celery
│   ├── rapports/        # Agrégations, exports
│   └── audit/           # JournalAudit, middleware
├── core/                # Mixins, pagination, exceptions, utilitaires
└── manage.py
```

**Règle d'architecture importante.** La logique métier ne vit pas dans les vues DRF ni dans les modèles, mais dans une couche `services.py` par application (ex. `ventes/services.py::enregistrer_prestation()`). Les vues orchestrent, les services décident. Cela rend la logique testable unitairement et réutilisable depuis Celery, l'admin ou une commande de management.

### 9.3 Frontend

| Composant | Choix | Justification |
|---|---|---|
| Bibliothèque | **React 18** | Demandé. |
| Build | **Vite 5** | Demandé. Démarrage instantané, build optimisé, découpage de code natif. |
| Langage | **TypeScript** | Indispensable sur un projet de gestion : les erreurs de montant se paient cher. |
| Styles | **Tailwind CSS** | Cohérence par tokens, purge automatique, poids final minimal. |
| Composants | **Radix UI** + composants maison | Accessibilité clavier et ARIA gratuite, style entièrement libre. |
| État serveur | **TanStack Query** | Cache, revalidation, mutations optimistes, gestion hors ligne. |
| État client | **Zustand** | Léger, sans boilerplate, pour le ticket en cours et l'UI. |
| Routage | **React Router 6** | Routes protégées par rôle, chargement paresseux. |
| Formulaires | **React Hook Form + Zod** | Validation typée partagée. |
| Animations | **Framer Motion** | Transitions maîtrisées, respect de `prefers-reduced-motion`. |
| Graphiques | **Recharts** | Suffisant, léger, personnalisable. |
| Hors ligne | **Dexie.js** (IndexedDB) | File de synchronisation et cache local. |
| PWA | **vite-plugin-pwa** (Workbox) | Manifeste, service worker, stratégies de cache. |
| Tests | **Vitest + Testing Library + Playwright** | Unitaire, composant, bout-en-bout. |

**Structure du frontend**

```
src/
├── app/                 # Point d'entrée, providers, router
├── pages/               # Une page par route
│   ├── auth/  onboarding/  caisse/  stock/  catalogue/
│   ├── rapports/  employes/  clients/  parametres/
├── features/            # Logique métier par domaine
│   ├── ventes/          # hooks, store du ticket, composants
│   ├── stocks/  notifications/  ...
├── components/
│   ├── ui/              # Primitives : Button, Input, Sheet, Toast...
│   └── layout/          # AppShell, BarreNav, EnTete
├── lib/                 # client api, formatage XAF, dates, db offline
├── hooks/               # useAuth, useSecretariat, useOnline, usePush
├── styles/              # tokens.css, globals.css
└── types/               # types générés depuis OpenAPI
```

> **Astuce d'efficacité :** générer les types TypeScript directement depuis le schéma OpenAPI produit par drf-spectacular (`openapi-typescript`). Le frontend et le backend ne divergent jamais.

### 9.4 Tâches asynchrones et périodiques

| Tâche | Type | Fréquence | Rôle |
|---|---|---|---|
| `envoyer_notification_push` | Asynchrone | À la demande | Envoi VAPID, gestion des abonnements expirés (410 → désactivation) |
| `verifier_seuils_stock` | Asynchrone | Après chaque mouvement | Évalue les seuils, déclenche l'alerte |
| `notifier_ca_periodique` | Périodique | Toutes les 15 min | Balaie les secrétariats, envoie si plage active et intervalle écoulé |
| `bilan_fin_journee` | Périodique | Toutes les 15 min | Envoie le récapitulatif à la fermeture |
| `rappel_creances` | Périodique | Quotidienne 09 h | Alerte sur les crédits échus |
| `recalculer_stocks` | Manuelle | À la demande | Reconstruit les quantités depuis les mouvements |
| `purger_notifications` | Périodique | Hebdomadaire | Archive les notifications de plus de 90 jours |

---

## 10. Spécification de l'API

Base : `/api/v1/`. Authentification par en-tête `Authorization: Bearer <token>`.

### 10.1 Principales ressources

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/auth/inscription/` | Création du compte propriétaire |
| `POST` | `/auth/connexion/` | Obtention des tokens |
| `POST` | `/auth/rafraichir/` | Renouvellement de l'access token |
| `POST` | `/auth/deconnexion/` | Blacklist du refresh token |
| `GET/PATCH` | `/moi/` | Profil de l'utilisateur courant |
| `GET/POST` | `/secretariats/` | Liste / création |
| `GET/PATCH` | `/secretariats/{id}/` | Détail / modification |
| `GET/PUT` | `/secretariats/{id}/plages-horaires/` | Plage horaire hebdomadaire |
| `GET/PATCH` | `/secretariats/{id}/parametres-notification/` | Réglages de notification |
| `GET/POST` | `/services/` | Catalogue |
| `GET/PATCH/DELETE` | `/services/{id}/` | Détail |
| `PUT` | `/services/{id}/nomenclature/` | Définition des consommables prélevés |
| `GET/POST` | `/consommables/` | Fiches consommables |
| `GET` | `/consommables/alertes/` | Ceux sous le seuil |
| `POST` | `/consommables/{id}/entree-stock/` | Réapprovisionnement |
| `POST` | `/consommables/{id}/ajustement/` | Correction d'inventaire |
| `GET` | `/mouvements-stock/` | Journal filtrable |
| `GET/POST` | `/prestations/` | Liste / enregistrement |
| `POST` | `/prestations/synchroniser/` | Envoi en lot depuis le mode hors ligne |
| `POST` | `/prestations/{id}/annuler/` | Annulation avec motif |
| `GET` | `/prestations/{id}/recu/` | Reçu PDF |
| `GET/POST` | `/sessions-caisse/` | Sessions |
| `POST` | `/sessions-caisse/{id}/cloturer/` | Clôture avec comptage |
| `GET/POST` | `/depenses/` | Dépenses |
| `GET/POST` | `/clients/` | Fiches clients |
| `POST` | `/clients/{id}/reglement/` | Règlement d'une créance |
| `GET/POST` | `/employes/` | Gestion du personnel |
| `POST` | `/employes/{id}/desactiver/` | Désactivation |
| `POST` | `/push/abonnement/` | Enregistrement d'un abonnement push |
| `DELETE` | `/push/abonnement/` | Désabonnement |
| `GET` | `/notifications/` | Centre de notifications |
| `POST` | `/notifications/tout-lire/` | Marquer tout comme lu |
| `GET` | `/tableau-de-bord/` | Agrégats du jour |
| `GET` | `/rapports/ventes/` | Rapport de ventes |
| `GET` | `/rapports/rentabilite/` | Marges |
| `GET` | `/rapports/stock/` | État et valorisation |
| `GET` | `/audit/` | Journal d'audit |

### 10.2 Exemple — enregistrement d'une prestation

**Requête** `POST /api/v1/prestations/`

```json
{
  "client_uuid": "0f9d5c2a-77e1-4a1b-9c3e-2b8a4d6f1e05",
  "session_caisse": 128,
  "mode_reglement": "ESPECES",
  "montant_recu": 2000,
  "client": null,
  "lignes": [
    { "service": 3, "quantite": 25, "remise": 0 },
    { "service": 7, "quantite": 1,  "remise": 0 }
  ]
}
```

**Réponse** `201 Created`

```json
{
  "id": 4412,
  "numero": "EBO01-20260902-0042",
  "statut": "VALIDEE",
  "montant_total": 1750,
  "montant_recu": 2000,
  "monnaie_a_rendre": 250,
  "cout_total": 640,
  "marge": 1110,
  "lignes": [
    {
      "service_nom": "Photocopie A4 N&B",
      "quantite": 25,
      "prix_unitaire": 50,
      "montant": 1250
    },
    {
      "service_nom": "Reliure spirale",
      "quantite": 1,
      "prix_unitaire": 500,
      "montant": 500
    }
  ],
  "alertes_stock": [
    {
      "consommable": "Papier A4",
      "quantite_restante": 85,
      "seuil_alerte": 100,
      "niveau": "FAIBLE"
    }
  ],
  "cree_le": "2026-09-02T14:23:11+01:00"
}
```

Le champ `alertes_stock` permet à l'interface d'afficher immédiatement l'avertissement dans le toast de confirmation, sans attendre la notification push.

### 10.3 Conventions

- Pagination par curseur sur les listes volumineuses (`?cursor=`), par page sur le reste (`?page=&taille=`), 25 éléments par défaut.
- Erreurs normalisées :
  ```json
  { "code": "STOCK_INSUFFISANT", "message": "Il ne reste que 12 spirales.",
    "details": { "consommable": 9, "disponible": 12, "demande": 20 } }
  ```
- Limitation de débit : 5 tentatives de connexion / minute / IP ; 120 requêtes / minute / utilisateur authentifié.

---

## 11. Direction artistique et UX/UI

### 11.1 Le parti pris

Un logiciel de secrétariat bureautique vit dans un univers très concret : **l'encre et le papier**. La direction artistique s'ancre là plutôt que dans le vocabulaire visuel générique du tableau de bord SaaS.

La palette est bâtie sur les **quatre encres de la quadrichromie** (cyan, magenta, jaune, noir) — le langage même de l'impression et de la photocopie. Chaque encre reçoit un rôle fonctionnel, ce qui donne un code couleur immédiatement mémorisable pour l'utilisateur.

### 11.2 Jetons de couleur

```css
:root {
  /* Fond et surfaces — papier, pas crème */
  --papier:          #F6F6F3;   /* fond général */
  --papier-surface:  #FFFFFF;   /* cartes, panneaux */
  --papier-creux:    #ECECE6;   /* zones en retrait, séparateurs */

  /* Encre noire — texte et structure */
  --encre:           #14161A;   /* titres, montants */
  --encre-douce:     #4A4F58;   /* texte courant */
  --encre-pale:      #868D98;   /* libellés secondaires */

  /* Cyan — action primaire, navigation active */
  --cyan:            #0B7285;
  --cyan-clair:      #E0F2F5;

  /* Magenta — attention, annulation, écart */
  --magenta:         #B02A5B;
  --magenta-clair:   #FBE7EE;

  /* Jaune — alerte de stock, avertissement */
  --jaune:           #C98A0B;
  --jaune-clair:     #FDF3DC;

  /* Vert d'encaissement — succès, validation */
  --valide:          #157F4A;
  --valide-clair:    #E2F4EA;
}
```

Correspondance sémantique enseignée à l'utilisateur en une phrase dans l'aide : **cyan = agir, jaune = surveiller, magenta = corriger, vert = encaissé**.

Un thème sombre est fourni, utile en boutique éclairée au néon le soir et pour économiser la batterie sur écrans OLED : le papier devient `#101215`, l'encre devient `#EDEEF0`, et les accents sont désaturés d'environ 15 %.

### 11.3 Typographie

| Rôle | Famille | Usage |
|---|---|---|
| Affichage / titres | **Bricolage Grotesque** | Titres de page, montants du tableau de bord. Ses formes légèrement industrielles évoquent la signalétique d'atelier. |
| Texte courant / interface | **Public Sans** | Libellés, tableaux, formulaires. Excellente lisibilité en petit corps. |

Échelle typographique (ratio 1,25 — seconde majeure augmentée, adapté à une interface dense) :

```
12 · 14 · 16 · 20 · 25 · 31 · 39 · 49 px
```

Règles :
- Les montants utilisent impérativement `font-variant-numeric: tabular-nums` pour que les chiffres s'alignent verticalement dans les tableaux et ne « dansent » pas lors des mises à jour en direct.
- Corps de texte à 16 px minimum sur mobile (évite le zoom automatique iOS sur les champs).
- Longueur de ligne limitée à 70 caractères sur les contenus textuels.
- Casse phrase partout. Pas de libellés en capitales espacées.

### 11.4 Mise en page

**Mobile (< 768 px) — la cible prioritaire**

```
┌──────────────────────────────┐
│ Sigma Bureautique      🔔 3  │  en-tête compact, sticky
├──────────────────────────────┤
│                              │
│   68 200 F                   │  montant du jour, corps 49
│   Aujourd'hui  ↑ 12 %        │
│                              │
├──────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │Photo │ │Impr. │ │Saisie│   │  tuiles services 3 colonnes
│ │copie │ │ N&B  │ │      │   │  cible tactile 88 × 88 px
│ │ 50 F │ │ 75 F │ │200 F │   │
│ └──────┘ └──────┘ └──────┘   │
│ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │Reliure│ │Plast.│ │ Scan │  │
│ └──────┘ └──────┘ └──────┘   │
├──────────────────────────────┤
│  ▲ Ticket · 2 lignes · 1750 F│  tiroir escamotable
├──────────────────────────────┤
│  Caisse  Stock  Bilan  Plus  │  navigation basse, 4 entrées
└──────────────────────────────┘
```

**Desktop (≥ 1024 px)**

Barre latérale de navigation à gauche (240 px), zone de travail centrale, ticket en cours en colonne fixe à droite (360 px). Grille de 12 colonnes, gouttière de 24 px, largeur maximale de contenu 1440 px.

Alignement : texte aligné à gauche, **montants alignés à droite** dans tous les tableaux — convention comptable universelle qui rend la lecture verticale possible.

### 11.5 Principes d'interaction

1. **Le montant total est toujours le plus gros élément à l'écran.** C'est ce que l'employé lit pour annoncer le prix au client, souvent d'un coup d'œil rapide.
2. **Cible tactile de 88 × 88 px minimum** sur les tuiles services — bien au-delà des 44 px recommandés, car la saisie se fait debout, vite, parfois d'une seule main.
3. **Zone de pouce.** Les actions destructives (annuler une ligne) ne sont jamais dans le tiers inférieur de l'écran mobile ; le bouton « Encaisser » l'est toujours.
4. **Confirmation par retour immédiat.** Une prestation validée déclenche un retour haptique (`navigator.vibrate`), un toast vert avec le numéro de ticket et la monnaie à rendre, et l'animation du compteur de CA.
5. **Aucune modale bloquante pendant l'encaissement.** Les avertissements de stock sont des bandeaux non bloquants.
6. **L'état hors ligne est visible en permanence** : bandeau discret ambre en haut, avec le nombre de prestations en attente de synchronisation.

### 11.6 Animation

Le mouvement est un outil de compréhension, pas de décoration. Trois usages seulement :

| Moment | Animation | Durée |
|---|---|---|
| Ajout d'une ligne au ticket | La tuile pressée se contracte (`scale 0.96`) puis la ligne glisse dans le ticket | 180 ms, `ease-out` |
| Encaissement validé | Le compteur de CA défile chiffre par chiffre jusqu'à la nouvelle valeur | 600 ms, `ease-out` |
| Franchissement d'un seuil de stock | La pastille du consommable pulse une fois en jaune | 400 ms, une seule itération |

Les transitions de page utilisent un fondu simple de 150 ms. Aucune entrée en cascade des sections au défilement.

`prefers-reduced-motion: reduce` supprime toutes les animations non essentielles et réduit les transitions à 0 ms.

### 11.7 Rédaction de l'interface

| Situation | À écrire | À ne pas écrire |
|---|---|---|
| Bouton de validation | `Encaisser 1 750 F` | `Soumettre` |
| Confirmation | `Encaissé. Ticket EBO01-0042. Rendre 250 F.` | `Opération réussie` |
| Écran vide (stock) | `Aucun consommable enregistré. Ajoutez-en un pour suivre vos stocks.` + bouton | `Aucune donnée` |
| Erreur de stock | `Il ne reste que 12 spirales. Vous pouvez en vendre 12 au maximum.` | `Erreur : stock insuffisant` |
| Hors ligne | `Hors ligne. 3 ventes seront envoyées au retour du réseau.` | `Erreur de connexion` |
| Alerte push | `Papier A4 : il reste 40 feuilles sur un seuil de 100.` | `Alerte stock critique !!!` |

Un verbe garde le même nom du bouton jusqu'au message de confirmation : on « encaisse » et on obtient « Encaissé ».

### 11.8 Accessibilité

- Contraste AA minimum partout, AAA sur le texte courant.
- Focus clavier visible : contour de 2 px en cyan, décalé de 2 px.
- Navigation complète au clavier, y compris la grille de services (flèches + Entrée).
- Attributs ARIA sur tous les composants interactifs (Radix les fournit).
- `aria-live="polite"` sur le total du ticket et le compteur de CA.
- Les couleurs ne portent jamais seules l'information : une alerte de stock combine couleur, icône et texte.

---

## 12. Sécurité

### 12.1 Authentification

- Mots de passe hachés en Argon2 (`ARGON2_PASSWORD_HASHER` en tête de `PASSWORD_HASHERS`).
- Politique : 8 caractères minimum, vérification contre la liste des mots de passe courants, interdiction des mots de passe entièrement numériques.
- JWT : access 60 min, refresh 30 jours avec rotation et mise en liste noire de l'ancien.
- Verrouillage progressif après 5 échecs (`django-axes`).
- Code PIN à 4 chiffres pour le déverrouillage rapide : haché, valable uniquement sur un appareil déjà authentifié, réinitialisé au bout de 12 h d'inactivité.

### 12.2 Autorisation

Classes de permission DRF explicites par vue : `EstProprietaire`, `EstGerantOuPlus`, `EstMembreDuSecretariat`. Aucune vue ne repose sur la permission par défaut.

### 12.3 Isolation multi-locataire

Le point de sécurité le plus critique du projet. Trois barrières superposées :

1. Un middleware résout le secrétariat actif à partir du token et le place dans le contexte de la requête.
2. Un `TenantQuerySetMixin` sur tous les ViewSets filtre systématiquement `queryset.filter(secretariat=request.secretariat)`.
3. Des tests automatisés dédiés vérifient, pour **chaque** endpoint, qu'un utilisateur du secrétariat A reçoit bien un `404` sur une ressource du secrétariat B.

### 12.4 Protection applicative

| Menace | Parade |
|---|---|
| Injection SQL | ORM Django exclusivement, aucun SQL brut non paramétré |
| XSS | React échappe par défaut ; interdiction de `dangerouslySetInnerHTML` |
| CSRF | API stateless par jeton ; `SameSite=Strict` sur le cookie de refresh |
| Clickjacking | `X-Frame-Options: DENY` |
| Transport | HTTPS obligatoire, HSTS 1 an, redirection 301 |
| En-têtes | CSP stricte, `X-Content-Type-Options: nosniff`, `Referrer-Policy` |
| Force brute | Limitation de débit + verrouillage progressif |
| Téléversement | Types MIME autorisés en liste blanche, taille max 5 Mo, renommage systématique |
| Secrets | Variables d'environnement uniquement, `.env` hors dépôt, rotation documentée |

### 12.5 Données personnelles

Conformité à la loi camerounaise n° 2010/012 sur la cybersécurité et la cybercriminalité : consentement explicite à la collecte, droit d'accès et de rectification, export des données du secrétariat sur demande, chiffrement au repos des sauvegardes, journal d'accès conservé 12 mois.

---

## 13. Performance et contraintes locales

### 13.1 Optimisations backend

- `select_related` / `prefetch_related` systématiques ; un test de non-régression sur le nombre de requêtes (`assertNumQueries`) sur les endpoints critiques.
- Verrouillage pessimiste (`select_for_update`) sur les consommables lors de la décrémentation, pour éviter les stocks incohérents en cas de saisie simultanée par deux employés.
- Cache Redis sur les agrégats du tableau de bord (TTL 60 s) et sur le catalogue de services (invalidation à la modification).
- Pagination obligatoire, aucune liste non bornée.

### 13.2 Optimisations frontend

- Découpage de code par route (`React.lazy`).
- Précaching des ressources critiques par le service worker.
- Images en WebP, chargement différé.
- Debounce de 300 ms sur les champs de recherche.
- Virtualisation des listes de plus de 100 lignes.
- Budget de performance imposé dans la CI : échec du build si le bundle initial dépasse 200 Ko gzip.

### 13.3 Stratégies de cache du service worker

| Ressource | Stratégie |
|---|---|
| Shell applicatif (HTML, JS, CSS) | Cache d'abord, mise à jour en arrière-plan |
| Catalogue services / consommables | Réseau d'abord avec repli sur le cache, TTL 1 h |
| Prestations et rapports | Réseau uniquement (données sensibles à la fraîcheur) |
| Polices et icônes | Cache d'abord, 1 an |
| Écritures hors ligne | Background Sync API, file persistée en IndexedDB |

---

## 14. Découpage en lots et planning

Estimation pour **un développeur à temps plein**. Diviser par 1,7 environ pour une équipe de deux.

### Lot 0 — Fondations (1 semaine)
Dépôt Git, Docker Compose (Django + PostgreSQL + Redis), configuration multi-environnement, modèle `Utilisateur` personnalisé, DRF, JWT, drf-spectacular, projet Vite + TypeScript + Tailwind, jetons de design, primitives UI, client API typé, CI GitHub Actions.
**Livrable :** un « hello world » authentifié de bout en bout, déployable.

### Lot 1 — Comptes et secrétariats (1,5 semaine)
Inscription, connexion, refresh, profil. Modèle `Secretariat`, isolation multi-locataire et ses tests. Assistant d'installation en 3 écrans. Coquille applicative (navigation, en-tête, routes protégées).
**Livrable :** un propriétaire crée son compte et son secrétariat.

### Lot 2 — Catalogue et stock (2 semaines)
Services, nomenclature, consommables, entrées de stock avec CUMP, ajustements, journal des mouvements. Écrans de gestion associés.
**Livrable :** le catalogue et le stock sont pilotables intégralement.

### Lot 3 — Point de vente (2,5 semaines)
Sessions de caisse, ticket, encaissement, décrémentation atomique du stock, annulation, reçus, dépenses, clôture avec écart.
**Livrable :** le logiciel devient utilisable en production réelle.

### Lot 4 — Notifications (1,5 semaine)
Celery + Beat, VAPID, abonnements push, service worker de réception, alertes de stock, plages horaires, notification de CA périodique, centre de notifications, réglages.
**Livrable :** l'exigence différenciante du produit est opérationnelle.

### Lot 5 — Tableaux de bord et rapports (1,5 semaine)
Agrégats, graphiques, rapports de ventes / stock / rentabilité / caisse, exports CSV et PDF, performance par employé.
**Livrable :** le propriétaire pilote son activité par les chiffres.

### Lot 6 — Employés et clients (1 semaine)
Création et désactivation de comptes, suivi d'activité, fiches clients, créances et règlements.

### Lot 7 — Hors ligne et PWA (1,5 semaine)
Manifeste, installation, IndexedDB, file de synchronisation, endpoint idempotent, indicateurs d'état, tests de coupure réseau.

### Lot 8 — Finition, tests et production (2 semaines)
Audit d'accessibilité, passe de performance, journal d'audit, thème sombre, pages d'erreur, documentation utilisateur, tests de charge, durcissement sécurité, déploiement, supervision.

**Total : environ 14,5 semaines** (≈ 3,5 mois) pour un développeur seul, incluant les tests et la mise en production.

> Conseil de séquencement : viser une mise en service pilote dans **un seul secrétariat réel** dès la fin du lot 3. Les retours du terrain sur la saisie au comptoir valent plus que trois semaines de spécification supplémentaire.

---

## 15. Stratégie de tests et recette

### 15.1 Pyramide de tests

| Niveau | Outils | Couverture cible | Portée |
|---|---|---|---|
| Unitaire backend | pytest, pytest-django, factory-boy | ≥ 85 % sur `services.py` | Calculs de stock, CUMP, marges, plages horaires |
| Intégration API | pytest + APIClient | 100 % des endpoints | Statuts, permissions, isolation multi-locataire |
| Unitaire frontend | Vitest + Testing Library | ≥ 70 % | Hooks, formatage XAF, logique du ticket |
| Bout en bout | Playwright | 8 parcours critiques | Voir ci-dessous |

### 15.2 Parcours critiques à couvrir en bout en bout

1. Inscription → assistant d'installation → premier service créé.
2. Ouverture de session → vente de 25 photocopies → encaissement espèces → vérification du stock décrémenté de 25 feuilles.
3. Vente d'une reliure → vérification du décompte simultané de 3 consommables distincts.
4. Vente d'un service sans consommable (saisie) → vérification qu'aucun mouvement de stock n'est créé.
5. Vente faisant franchir le seuil → réception de la notification push d'alerte.
6. Annulation d'une prestation → vérification de la contre-passation exacte du stock.
7. Coupure réseau → 3 ventes hors ligne → retour du réseau → synchronisation sans doublon.
8. Clôture de session avec écart → commentaire obligatoire → notification au propriétaire.

### 15.3 Tests spécifiques aux notifications

La tâche `notifier_ca_periodique` doit être testée avec un temps figé (`freezegun`) sur ces cas :
- instant dans la plage → envoi ;
- instant hors plage → aucun envoi ;
- jour marqué fermé → aucun envoi ;
- intervalle non écoulé → aucun envoi ;
- CA nul sur l'intervalle **et** sur la journée → aucun envoi (RG-10) ;
- passage de minuit et changement de jour ;
- abonnement push expiré (réponse 410) → désactivation propre de l'abonnement.

### 15.4 Recette utilisateur

Recette menée **sur site, dans un vrai secrétariat, un jour d'affluence**. Critères d'acceptation :
- un employé non formé enregistre sa première vente en moins de 2 minutes après une démonstration de 5 minutes ;
- aucune perte de saisie sur une journée complète incluant au moins une coupure de courant ;
- le propriétaire confirme avoir reçu ses notifications de CA aux heures attendues ;
- l'écart de caisse en fin de journée s'explique intégralement.

---

## 16. Déploiement et mise en production

### 16.1 Environnements

| Environnement | Usage | Hébergement |
|---|---|---|
| Local | Développement | Docker Compose |
| Recette | Validation, démonstration client | VPS, sous-domaine `recette.` |
| Production | Exploitation | VPS |

### 16.2 Infrastructure recommandée

Un VPS suffit largement pour la v1 et les premières dizaines de secrétariats.

| Élément | Recommandation |
|---|---|
| Serveur | VPS 4 vCPU / 8 Go RAM / 100 Go SSD (Hetzner, Contabo, ou un hébergeur régional pour la latence) |
| OS | Ubuntu 24.04 LTS |
| Conteneurisation | Docker + Docker Compose |
| Serveur web | Nginx (TLS, compression Brotli, service des statiques) |
| Serveur applicatif | Gunicorn, 4 workers, `gthread` |
| Base de données | PostgreSQL 16 en conteneur, volume persistant |
| Fichiers statiques | WhiteNoise (v1) → CDN si le trafic croît |
| Médias | Volume local (v1) → S3 compatible en v2 |
| TLS | Let's Encrypt, renouvellement automatique |
| Domaine | `sigmagestion.cm` (ou `.com`), `api.sigmagestion.cm` |

### 16.3 Chaîne d'intégration continue

Sur chaque *pull request* :
1. Lint backend (ruff) et formatage (black).
2. Lint frontend (ESLint) et formatage (Prettier).
3. Vérification des types (mypy, tsc).
4. Tests unitaires et d'intégration.
5. Build frontend et contrôle du budget de bundle.
6. Analyse de sécurité des dépendances (pip-audit, npm audit).

Sur fusion dans `main` : build des images Docker, push vers le registre, déploiement automatique en recette. Le déploiement en production est **manuel et déclenché explicitement** (protection contre les mises en production accidentelles).

### 16.4 Procédure de déploiement

```
1. Sauvegarde de la base (pg_dump) et vérification de sa restaurabilité
2. Activation du mode maintenance (page statique Nginx)
3. Récupération des nouvelles images
4. python manage.py migrate --noinput
5. python manage.py collectstatic --noinput
6. Redémarrage progressif des conteneurs web puis Celery
7. Contrôle de santé sur /api/v1/sante/
8. Sortie du mode maintenance
9. Surveillance de Sentry pendant 30 minutes
```

Toute migration doit être **réversible** ou accompagnée d'un plan de retour arrière documenté. Les migrations destructrices (suppression de colonne) sont scindées en deux déploiements successifs.

### 16.5 Sauvegardes

| Élément | Fréquence | Rétention | Destination |
|---|---|---|---|
| Base de données | Quotidienne 02 h | 30 jours | Stockage objet hors du serveur |
| Base de données | Hebdomadaire | 6 mois | Idem |
| Médias | Quotidienne | 30 jours | Idem |
| Test de restauration | Mensuel | — | Obligatoire, tracé |

> Une sauvegarde jamais restaurée n'est pas une sauvegarde. Le test mensuel de restauration est non négociable.

### 16.6 Supervision

| Aspect | Outil |
|---|---|
| Erreurs applicatives | Sentry (backend et frontend) |
| Disponibilité | UptimeRobot sur `/api/v1/sante/` |
| Logs | Docker → fichiers structurés, rotation quotidienne |
| Métriques système | Netdata ou équivalent léger |
| Alertes | E-mail + WhatsApp vers l'administrateur |

Le point de santé vérifie : accès base de données, accès Redis, réactivité du worker Celery.

---

## 17. Exploitation et maintenance

### 17.1 Documentation à produire

| Document | Destinataire |
|---|---|
| Guide de démarrage (5 pages, illustré) | Propriétaire |
| Aide-mémoire de la caisse (1 page A5, plastifiable — à coller au comptoir) | Employé |
| Documentation API (OpenAPI générée) | Développeur |
| Guide d'exploitation (déploiement, sauvegarde, restauration, incidents) | Administrateur |
| Journal des versions | Tous |

### 17.2 Support

Canal principal : WhatsApp Business — le canal naturel du contexte. Engagement de réponse sous 24 h ouvrées. Incident bloquant en production : prise en charge sous 4 h.

### 17.3 Rythme de maintenance

- Correctifs de sécurité des dépendances : mensuels.
- Version mineure (améliorations, corrections) : toutes les 6 à 8 semaines.
- Revue des indicateurs d'usage et des retours utilisateurs : trimestrielle.

---

## 18. Évolutions envisagées (hors périmètre v1)

| Évolution | Intérêt |
|---|---|
| Intégration MTN MoMo et Orange Money (API Collections) | Encaissement et rapprochement automatiques |
| Multi-secrétariats consolidé | Un propriétaire suivant plusieurs points de vente sur un tableau de bord unique |
| Portail client de dépôt de fichiers | Le client envoie son document à imprimer depuis son téléphone, récupère au comptoir |
| Impression thermique Bluetooth | Reçus imprimés directement depuis le téléphone |
| Commandes vocales en français simplifié | Saisie mains libres au comptoir |
| Prévision de réapprovisionnement | Estimation de la date de rupture à partir de la consommation moyenne |
| Mode « atelier » | Suivi des travaux en cours de réalisation (mémoires, thèses) avec états d'avancement |
| Version anglophone | Régions du Nord-Ouest et du Sud-Ouest |
| Application Android native (TWA) | Distribution via Play Store |

---

## 19. Annexes

### A. Glossaire

| Terme | Définition |
|---|---|
| **Prestation** | Une vente enregistrée, composée d'une ou plusieurs lignes de service. Équivalent d'un ticket. |
| **Nomenclature** | Recette d'un service : liste des consommables prélevés et quantité par unité vendue. |
| **CUMP** | Coût unitaire moyen pondéré. Méthode de valorisation du stock retenue. |
| **Session de caisse** | Période de travail d'un employé, du fond de caisse initial à la clôture comptée. |
| **Écart de caisse** | Différence entre le montant physiquement compté et le montant théorique. |
| **Seuil d'alerte** | Quantité en dessous de laquelle une notification de réapprovisionnement est émise. |
| **VAPID** | Protocole d'authentification du serveur d'application auprès du service de push du navigateur. |
| **PWA** | Application web progressive : installable, fonctionnant hors ligne, recevant des notifications. |
| **Multi-locataire** | Architecture où une même instance sert plusieurs clients avec des données strictement cloisonnées. |

### B. Données de démarrage recommandées

Services pré-remplis proposés à l'assistant d'installation, avec des prix indicatifs à ajuster localement :

| Service | Prix indicatif | Consomme du stock |
|---|---|---|
| Photocopie A4 N&B | 50 F / page | Oui |
| Photocopie A3 N&B | 100 F / page | Oui |
| Impression A4 N&B | 75 F / page | Oui |
| Impression A4 couleur | 250 F / page | Oui |
| Saisie de document | 200 F / page | Non |
| Numérisation | 200 F / page | Non |
| Reliure spirale | 500 F / document | Oui |
| Plastification A4 | 500 F / pièce | Oui |
| Plastification format carte | 250 F / pièce | Oui |
| Envoi par e-mail | 200 F / forfait | Non |

Consommables pré-remplis : Papier A4 (feuille), Papier A3 (feuille), Toner noir (cartouche), Toner couleur (cartouche), Spirale plastique (pièce), Couverture transparente (pièce), Dos cartonné (pièce), Pochette à plastifier A4 (pièce), Pochette à plastifier carte (pièce).

### C. Variables d'environnement

```env
# Django
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=sigmagestion.cm,api.sigmagestion.cm

# Base de données
DATABASE_URL=postgres://user:pass@db:5432/sigmagestion

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1

# Web Push (générer avec: vapid --gen)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_ADMIN_EMAIL=admin@sigmagestion.cm

# Régional
TIME_ZONE=Africa/Douala
LANGUAGE_CODE=fr-cm
DEVISE=XAF

# Supervision
SENTRY_DSN=

# SMS (réinitialisation de mot de passe)
SMS_PROVIDER_KEY=
```

### D. Checklist de mise en production

- [ ] `DEBUG = False` et `SECRET_KEY` unique généré pour la production
- [ ] `ALLOWED_HOSTS` restreint aux domaines réels
- [ ] HTTPS actif, HSTS configuré, redirection HTTP → HTTPS
- [ ] En-têtes de sécurité vérifiés (securityheaders.com, note A minimum)
- [ ] Clés VAPID générées et notifications testées sur Android et iOS
- [ ] Sauvegarde automatique configurée **et restauration testée**
- [ ] Sentry actif sur backend et frontend
- [ ] Supervision de disponibilité active
- [ ] Tâches Celery Beat visibles et actives dans l'admin
- [ ] Fuseau horaire du serveur et de Django à Africa/Douala
- [ ] Lighthouse ≥ 85 (performance) et ≥ 95 (accessibilité) sur mobile
- [ ] Tests d'isolation multi-locataire au vert
- [ ] Manifeste PWA valide, installation testée sur Android
- [ ] Mode hors ligne validé sur une coupure réelle
- [ ] Compte super-administrateur créé avec mot de passe fort
- [ ] Comptes de démonstration supprimés
- [ ] Documentation utilisateur livrée au client
- [ ] Aide-mémoire de caisse imprimé et remis

---

*Fin du cahier des charges — SigmaGestion v1.0*
