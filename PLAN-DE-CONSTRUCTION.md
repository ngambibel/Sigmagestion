# SigmaGestion — Plan de construction détaillé

**Document de pilotage du développement**
Basé sur le cahier des charges v1.0 · Construction étape par étape

---

## Comment on travaille (le rituel de chaque étape)

À **chaque étape** de ce plan, on répète le même cycle en 4 temps :

1. **Je construis** — j'écris le code de l'étape (back et/ou front).
2. **Je teste** — je lance les tests automatiques et je vérifie que ça démarre sans erreur. Je te dis ce que j'ai vérifié.
3. **Tu testes en local** — je te donne les commandes exactes à taper et **quoi observer** (ce que tu dois voir à l'écran, ce que tu dois pouvoir faire).
4. **Tu valides** — si ça te plaît, on passe à l'étape suivante. Sinon, tu me dis ce qui ne va pas et je corrige avant d'avancer.

> Règle d'or : **on n'avance jamais à l'étape N+1 tant que l'étape N ne te plaît pas.**

Chaque étape ci-dessous précise :
- 🎯 **Objectif** — ce qu'on obtient à la fin
- 🔨 **Ce que je construis** — le contenu technique
- ✅ **Comment tu testes** — les commandes et ce que tu dois voir
- 🏁 **Critère de validation** — comment on sait que c'est bon

---

## Convention d'avancement

- Je coche `[x]` les étapes terminées **et validées par toi** au fur et à mesure, directement dans ce fichier.
- Une étape marquée `[~]` = construite par moi, en attente de ton test.
- Une étape `[ ]` = pas encore commencée.

---

# PHASE 0 — Fondations et outillage

> Objectif de la phase : avoir un socle qui démarre, un « hello world » authentifié de bout en bout, et l'outillage prêt. C'est le Lot 0 du cahier des charges, découpé finement.

## Étape 0.1 — Installer les outils manquants `[x]`

🎯 **Objectif** : ta machine peut faire tourner tout le projet.

🔨 **Ce que je construis** : rien à coder ici — je te guide pour installer ce qui manque.

✅ **Comment tu testes** :
- Installer **Docker Desktop** pour Windows (avec le backend WSL2). Je te donnerai le lien et les réglages.
- Installer **Node.js 20 LTS**.
- Vérifier dans un terminal :
  ```powershell
  docker --version
  docker compose version
  node --version
  python --version
  git --version
  ```
  Tu dois voir un numéro de version pour chacun, sans erreur.

🏁 **Critère de validation** : les 5 commandes répondent une version. Docker Desktop est démarré (icône baleine active).

---

## Étape 0.2 — Squelette du dépôt et Docker Compose `[x]`

🎯 **Objectif** : `docker compose up` démarre PostgreSQL + Redis, et on a la structure de dossiers du projet.

🔨 **Ce que je construis** :
- Arborescence du dépôt (`backend/`, `frontend/`, `docker-compose.yml`, `.gitignore`, `.env.example`, `README.md`).
- `docker-compose.yml` avec les services **PostgreSQL 16** et **Redis 7** (Django et Celery viendront à l'étape suivante).
- Fichier `.env` local à partir de `.env.example`.
- Initialisation du dépôt Git (`git init`, premier commit).

✅ **Comment tu testes** :
```powershell
docker compose up -d db redis
docker compose ps
```
Tu dois voir `db` et `redis` avec le statut **running / healthy**.

🏁 **Critère de validation** : les deux conteneurs tournent et sont sains.

---

## Étape 0.3 — Projet Django + DRF qui démarre `[x]`

🎯 **Objectif** : le backend Django répond sur `http://localhost:8000`.

🔨 **Ce que je construis** :
- Projet Django 5.x avec la structure du cahier des charges (`config/` avec settings base/dev/prod, `apps/`, `core/`).
- Dépendances : DRF, django-environ, psycopg, structlog.
- Connexion à PostgreSQL via `DATABASE_URL`.
- Ajout du service `web` (Gunicorn/runserver) dans Docker Compose.
- Un endpoint de santé `GET /api/v1/sante/` qui vérifie la base et Redis.

✅ **Comment tu testes** :
```powershell
docker compose up -d
```
Ouvre dans ton navigateur : `http://localhost:8000/api/v1/sante/`
Tu dois voir une réponse JSON du type `{"base": "ok", "redis": "ok"}`.

🏁 **Critère de validation** : la page de santé répond `ok` partout.

---

## Étape 0.4 — Modèle Utilisateur + authentification JWT `[x]`

🎯 **Objectif** : on peut créer un utilisateur et obtenir un token.

🔨 **Ce que je construis** :
- App `comptes` avec le modèle `Utilisateur` personnalisé (téléphone comme identifiant, rôle, `doit_changer_mdp`, `code_pin_hash`).
- Hachage **Argon2**.
- `djangorestframework-simplejwt` : endpoints `/auth/connexion/`, `/auth/rafraichir/`, `/auth/deconnexion/`.
- Endpoint `/moi/` (profil courant).
- Admin Django activé + un super-administrateur.
- `drf-spectacular` : documentation API sur `/api/docs/`.

✅ **Comment tu testes** :
```powershell
docker compose exec web python manage.py createsuperuser
```
- Va sur `http://localhost:8000/admin/` → connecte-toi → tu vois l'admin Django.
- Va sur `http://localhost:8000/api/docs/` → tu vois la doc interactive de l'API.
- Teste `/auth/connexion/` depuis la doc → tu reçois un `access` et un `refresh` token.

🏁 **Critère de validation** : tu te connectes à l'admin et tu obtiens un token via l'API.

---

## Étape 0.5 — Frontend React + Vite + Tailwind qui démarre `[x]`

🎯 **Objectif** : le front s'affiche sur `http://localhost:5173` avec le design de base.

🔨 **Ce que je construis** :
- Projet **Vite + React 18 + TypeScript**.
- **Tailwind CSS** configuré avec les jetons de couleur du cahier des charges (palette quadrichromie : cyan, magenta, jaune, noir/encre, vert), les polices (Bricolage Grotesque + Public Sans), l'échelle typographique.
- Quelques **primitives UI** (Button, Input) conformes à la DA.
- **Client API typé** (axios/fetch wrapper) pointant vers le backend.
- Une page d'accueil de démonstration montrant la palette et la typo.

✅ **Comment tu testes** :
```powershell
cd frontend
npm install
npm run dev
```
Ouvre `http://localhost:5173`. Tu dois voir une page aux couleurs SigmaGestion (fond papier, accents cyan/magenta/jaune/vert), avec les bonnes polices et des boutons de démonstration.

🏁 **Critère de validation** : la page s'affiche avec la charte graphique correcte.

---

## Étape 0.6 — Connexion bout-en-bout (front ↔ back) `[x]`

🎯 **Objectif** : le « hello world authentifié » — je me connecte depuis le front et je vois mon profil.

🔨 **Ce que je construis** :
- Écran de **connexion** minimal côté front (téléphone + mot de passe).
- Stockage du token, appel à `/moi/`, affichage du nom de l'utilisateur connecté.
- Génération automatique des **types TypeScript depuis OpenAPI** (openapi-typescript).
- Mise en place de **TanStack Query** et **Zustand** (auth store).
- CI GitHub Actions de base (lint + tests) — *optionnel selon si tu veux un dépôt distant*.

✅ **Comment tu testes** :
- Sur `http://localhost:5173`, connecte-toi avec le compte créé à l'étape 0.4.
- Tu dois arriver sur une page qui affiche « Bonjour, {ton nom} » et un bouton de déconnexion.

🏁 **Critère de validation** : connexion réelle du front vers le back, profil affiché, déconnexion fonctionnelle.

> **🎉 Fin de Phase 0** — Livrable : un socle authentifié déployable, aux couleurs du produit.

---

# PHASE 1 — Comptes, secrétariats et isolation (Lot 1)

## Étape 1.1 — Inscription du propriétaire `[x]`

🎯 **Objectif** : un nouveau propriétaire crée son compte depuis le front.

🔨 **Ce que je construis** :
- Endpoint `POST /auth/inscription/` (nom, téléphone `+237 6XX XXX XXX`, e-mail facultatif, mot de passe).
- Validation du format de téléphone camerounais.
- Politique de mot de passe (8 car. min, pas 100 % numérique, liste des mots de passe courants).
- Écran d'inscription front avec **React Hook Form + Zod**.

✅ **Comment tu testes** : depuis le front, crée un nouveau compte propriétaire → tu es connecté automatiquement.

🏁 **Critère de validation** : inscription réussie, redirection vers l'app.

---

## Étape 1.2 — Modèle Secretariat + isolation multi-locataire `[x]`

🎯 **Objectif** : chaque donnée est rattachée à un secrétariat, et un secrétariat ne voit jamais les données d'un autre. **C'est le point de sécurité le plus critique du projet.**

🔨 **Ce que je construis** :
- App `secretariats` : modèle `Secretariat` (nom, code, ville, quartier, téléphone, propriétaire, devise).
- Middleware qui résout le secrétariat actif depuis le token.
- `TenantQuerySetMixin` appliqué à tous les ViewSets.
- Classes de permission DRF : `EstProprietaire`, `EstGerantOuPlus`, `EstMembreDuSecretariat`.
- Endpoints `/secretariats/` (liste/création/détail).
- **Tests d'isolation automatiques** : un utilisateur du secrétariat A reçoit un `404` sur une ressource du secrétariat B.

✅ **Comment tu testes** :
- Je te montre le résultat des tests d'isolation (ils doivent tous passer au vert).
- Depuis le front / la doc API, tu crées un secrétariat et tu le vois listé.

🏁 **Critère de validation** : les tests d'isolation sont au vert + création de secrétariat fonctionnelle.

---

## Étape 1.3 — Assistant d'installation en 3 écrans `[x]`

> Découpée en **1.3a** (back : modèles Service/Consommable + catalogue de démarrage — ✅ validé) et **1.3b** (front : assistant 3 écrans — en cours).


🎯 **Objectif** : un nouveau propriétaire configure son premier secrétariat en moins de 3 minutes.

🔨 **Ce que je construis** :
- Écran 1 : identité du secrétariat (nom, quartier, ville, téléphone affiché sur les reçus).
- Écran 2 : sélection des services parmi la liste pré-remplie (annexe B du cahier), prix par défaut modifiables.
- Écran 3 : déclaration du stock initial des consommables.
- Assistant **interruptible** (reprise possible plus tard).
- Données de démarrage (services et consommables pré-remplis).

✅ **Comment tu testes** : avec un compte neuf, tu parcours les 3 écrans → à la fin, ton secrétariat existe avec ses services et son stock initial. Teste aussi de quitter au milieu et de reprendre.

🏁 **Critère de validation** : parcours complet en moins de 3 min, reprise possible.

---

## Étape 1.4 — Coquille applicative (navigation, routes protégées) `[x]`

🎯 **Objectif** : l'ossature de navigation de l'app est en place.

🔨 **Ce que je construis** :
- **AppShell** : en-tête compact sticky, navigation basse mobile (Caisse / Stock / Bilan / Plus), barre latérale desktop.
- **React Router 6** : routes protégées par rôle, chargement paresseux (`React.lazy`).
- Bandeau d'état hors ligne (préparé, actif en phase 7).
- Cloche de notifications (préparée, active en phase 4).

✅ **Comment tu testes** : après connexion, tu navigues entre les sections vides. Sur mobile (mode responsive du navigateur), la navigation basse s'affiche ; sur desktop, la barre latérale.

🏁 **Critère de validation** : navigation fluide, responsive mobile/desktop, routes protégées selon le rôle.

> **🎉 Fin de Phase 1** — Livrable : un propriétaire crée son compte et son secrétariat.

---

# PHASE 2 — Catalogue et stock (Lot 2)

## Étape 2.1 — Catalogue de services `[x]`

> Réalisée pendant la Phase 1 (modèle Service + CRUD isolé + écrans liste/création/édition/suppression côté front).


🎯 **Objectif** : gérer les services et leurs prix.

🔨 **Ce que je construis** :
- App `catalogue` : modèle `Service` (nom, catégorie, unité, prix, actif, `consomme_stock`, couleur, icône).
- Endpoints CRUD `/services/`.
- Historique des prix (le prix est figé dans la prestation au moment de la vente — préparé ici).
- Écrans de gestion des services côté front (liste, création, édition).

✅ **Comment tu testes** : tu crées, modifies, désactives un service depuis le front. Tu changes un prix.

🏁 **Critère de validation** : gestion complète des services fonctionnelle.

---

## Étape 2.2 — Consommables `[x]`

> Réalisée (modèle Consommable + CRUD isolé + écrans + endpoint `/consommables/alertes/`).


🎯 **Objectif** : gérer les fiches consommables.

🔨 **Ce que je construis** :
- App `stocks` : modèle `Consommable` (nom, unité, prix d'achat unitaire, quantité en stock, seuil d'alerte, seuil critique, fournisseur, actif).
- Endpoints CRUD `/consommables/` + `/consommables/alertes/`.
- Écrans de gestion des consommables.

✅ **Comment tu testes** : tu crées un consommable (ex. Papier A4, seuil 100), tu le vois dans la liste.

🏁 **Critère de validation** : gestion des consommables fonctionnelle.

---

## Étape 2.3 — Nomenclature des services `[x]`

🎯 **Objectif** : décrire quels consommables un service prélève, et en quelle quantité.

🔨 **Ce que je construis** :
- Modèle `NomenclatureService` (service, consommable, quantité par unité, décimale précision 4).
- Endpoint `PUT /services/{id}/nomenclature/`.
- Règle RG-06 : un service `consomme_stock=true` doit avoir au moins une ligne de nomenclature pour être activable.
- Écran de définition de la nomenclature (ex. Impression N&B → 1 feuille A4 + 0,004 cartouche toner).

✅ **Comment tu testes** : tu définis la recette d'un service (ex. reliure = 1 spirale + 1 couverture + 1 dos). Tu vérifies qu'un service consommateur sans nomenclature ne peut pas être activé.

🏁 **Critère de validation** : nomenclature définissable, règle RG-06 respectée.

---

## Étape 2.4 — Entrées de stock avec CUMP `[~]`

🎯 **Objectif** : réapprovisionner et calculer automatiquement le coût moyen pondéré.

🔨 **Ce que je construis** :
- Modèle `MouvementStock` (type ENTREE/SORTIE_VENTE/AJUSTEMENT/ANNULATION, quantité signée, stock avant/après, prix d'achat, auteur, motif).
- Endpoint `POST /consommables/{id}/entree-stock/`.
- Calcul **CUMP** (RG-07) à chaque entrée.
- Couche `stocks/services.py` (logique métier isolée).
- Écran d'entrée de stock.

✅ **Comment tu testes** : tu fais une entrée de 500 feuilles à un prix, puis une autre à un prix différent → le prix d'achat unitaire affiché est la moyenne pondérée correcte. La quantité en stock augmente.

🏁 **Critère de validation** : le CUMP est calculé correctement, le stock est mis à jour.

---

## Étape 2.5 — Ajustements et journal des mouvements `[ ]`

🎯 **Objectif** : corriger un stock (casse, vol, erreur) et tout tracer.

🔨 **Ce que je construis** :
- Endpoint `POST /consommables/{id}/ajustement/` (motif obligatoire).
- Endpoint `GET /mouvements-stock/` (journal filtrable, horodaté, avec auteur).
- Écran de journal des mouvements + écran d'ajustement.
- Commande de management `recalculer_stocks`.

✅ **Comment tu testes** : tu fais un ajustement négatif (ex. -10 feuilles cassées) avec motif → le stock baisse, le mouvement apparaît dans le journal avec ton nom et l'heure.

🏁 **Critère de validation** : ajustement tracé, journal complet et filtrable.

> **🎉 Fin de Phase 2** — Livrable : catalogue et stock pilotables intégralement.

---

# PHASE 3 — Point de vente, le cœur du produit (Lot 3)

## Étape 3.1 — Sessions de caisse `[ ]`

🎯 **Objectif** : un employé ouvre sa session avec un fond de caisse.

🔨 **Ce que je construis** :
- App `caisse` : modèle `SessionCaisse` (employé, secrétariat, fond initial, théorique, compté, écart, statut).
- Endpoints `/sessions-caisse/` (ouverture) + règle RG-11 (une seule session ouverte à la fois).
- Écran d'ouverture de session.

✅ **Comment tu testes** : tu ouvres une session en déclarant un fond de caisse (ex. 10 000 F). Tu vérifies qu'on ne peut pas en ouvrir une deuxième.

🏁 **Critère de validation** : ouverture de session fonctionnelle, RG-11 respectée.

---

## Étape 3.2 — Écran de saisie et ticket en cours `[ ]`

🎯 **Objectif** : l'écran de vente avec les tuiles services et le ticket.

🔨 **Ce que je construis** :
- Grille de **tuiles services** tactiles (88×88 px min), triées par fréquence.
- **Ticket en cours** (tiroir bas mobile / colonne droite desktop) : lignes, quantité éditable, remise, **total en gros caractères**.
- Store **Zustand** du ticket.
- Animation d'ajout de ligne (180 ms).
- *Pas encore d'encaissement réel ici — juste construire le panier.*

✅ **Comment tu testes** : tu appuies sur des tuiles → les lignes s'ajoutent au ticket, le total se met à jour en gros. Tu modifies une quantité, tu enlèves une ligne.

🏁 **Critère de validation** : construction du ticket fluide et lisible, total correct.

---

## Étape 3.3 — Encaissement avec décrémentation atomique du stock `[ ]`

🎯 **Objectif** : valider une vente qui décrémente le stock en une transaction atomique. **C'est l'étape la plus importante du produit.**

🔨 **Ce que je construis** :
- App `ventes` : modèles `Prestation` + `LignePrestation` (prix et coût figés, numéro séquentiel `SEC-AAAAMMJJ-0001`).
- Couche `ventes/services.py::enregistrer_prestation()` — **une seule transaction atomique** (RG-04) : création prestation + prix/coûts figés + mouvements de stock + évaluation des seuils + mise à jour session.
- Verrouillage pessimiste `select_for_update` sur les consommables (saisie concurrente).
- Modes de règlement : Espèces (avec monnaie à rendre), MoMo, Orange Money, Crédit.
- Endpoint `POST /prestations/` (retour avec `alertes_stock` immédiat).
- Écran d'encaissement : mode de paiement, montant reçu, calcul de la monnaie.
- Toast vert de confirmation + retour haptique + animation du compteur de CA.
- Réglage « bloquer / autoriser en négatif » sur stock insuffisant (RG-06).

✅ **Comment tu testes** :
- Tu vends 25 photocopies, tu paies en espèces → tu vois « Encaissé. Ticket XXX. Rendre X F. »
- Tu vas dans le stock → le papier A4 a bien baissé de 25 feuilles.
- Tu vends une reliure → 3 consommables baissent simultanément.
- Tu vends une saisie (sans stock) → aucun mouvement de stock.

🏁 **Critère de validation** : la vente décrémente exactement le bon stock, atomiquement, et affiche la monnaie à rendre.

---

## Étape 3.4 — Annulation avec contre-passation `[ ]`

🎯 **Objectif** : annuler une prestation sans jamais la supprimer.

🔨 **Ce que je construis** :
- Endpoint `POST /prestations/{id}/annuler/` (motif obligatoire, propriétaire/gérant seulement).
- Statut `ANNULEE` + mouvements de stock inverses (RG-03).
- Écran/action d'annulation.

✅ **Comment tu testes** : tu annules une vente de 25 photocopies avec un motif → la prestation passe en « annulée » (pas supprimée), et les 25 feuilles reviennent au stock.

🏁 **Critère de validation** : contre-passation exacte du stock, traçabilité totale.

---

## Étape 3.5 — Dépenses et clôture de session `[ ]`

🎯 **Objectif** : enregistrer des sorties de caisse et clôturer en comptant.

🔨 **Ce que je construis** :
- Modèle `Depense` (session, catégorie, montant, description, justificatif photo facultatif).
- Endpoints `/depenses/` + `/sessions-caisse/{id}/cloturer/`.
- Calcul de l'écart (théorique vs compté), commentaire obligatoire si écart (RG-12).
- Écrans de dépense et de clôture.

✅ **Comment tu testes** : tu enregistres une dépense (ex. 2 000 F carburant), tu clôtures la session en déclarant le montant compté → le système affiche l'écart et exige un commentaire s'il est non nul.

🏁 **Critère de validation** : clôture avec calcul d'écart correct, commentaire imposé si écart.

---

## Étape 3.6 — Reçu imprimable et partage WhatsApp `[ ]`

🎯 **Objectif** : générer un reçu ticket.

🔨 **Ce que je construis** :
- Endpoint `GET /prestations/{id}/recu/` (PDF).
- Reçu format ticket 58 mm / 80 mm.
- Lien de partage WhatsApp.

✅ **Comment tu testes** : après une vente, tu ouvres le reçu → il s'affiche au format ticket avec le nom du secrétariat, les lignes, le total. Le bouton WhatsApp génère un lien.

🏁 **Critère de validation** : reçu lisible et partageable.

> **🎉 Fin de Phase 3** — Livrable : **le logiciel devient utilisable en production réelle.** C'est ici qu'on pourrait faire un pilote dans un vrai secrétariat.

---

# PHASE 4 — Notifications push (Lot 4)

## Étape 4.1 — Celery + Beat + VAPID `[ ]`

🎯 **Objectif** : l'infrastructure de tâches asynchrones et de push fonctionne.

🔨 **Ce que je construis** :
- Services `celery_worker` et `celery_beat` dans Docker Compose.
- Génération des clés **VAPID**.
- `pywebpush`, tâche `envoyer_notification_push` (gestion des abonnements expirés 410).
- App `notifications` : modèle `AbonnementPush`.

✅ **Comment tu testes** : je te montre les workers Celery actifs (`docker compose logs celery_worker`). L'admin Django affiche les tâches Beat.

🏁 **Critère de validation** : workers actifs, clés VAPID générées.

---

## Étape 4.2 — Abonnement push et service worker `[ ]`

🎯 **Objectif** : le navigateur s'abonne aux notifications.

🔨 **Ce que je construis** :
- Explication contextuelle **avant** la demande de permission navigateur.
- Service worker de réception des push.
- Endpoints `POST/DELETE /push/abonnement/`.
- Hook `usePush` côté front.

✅ **Comment tu testes** : tu actives les notifications depuis l'app → tu vois une explication, puis la popup du navigateur. Une notification de test s'affiche.

🏁 **Critère de validation** : tu reçois une notification push de test sur ton appareil.

---

## Étape 4.3 — Alerte de stock faible `[ ]`

🎯 **Objectif** : être prévenu avant la rupture.

🔨 **Ce que je construis** :
- Tâche `verifier_seuils_stock` déclenchée après chaque mouvement.
- Notification « Stock faible » (RG-08 : anti-spam 1/24h par consommable).
- Persistance en base (centre de notifications).

✅ **Comment tu testes** : tu vends assez pour faire passer un consommable sous son seuil → tu reçois la notification « Papier A4 : il reste X feuilles sur un seuil de 100. »

🏁 **Critère de validation** : notification reçue au franchissement du seuil, pas de spam.

---

## Étape 4.4 — Plages horaires et notification de CA périodique `[ ]`

🎯 **Objectif** : **l'exigence phare** — le propriétaire reçoit son CA toutes les 2 heures pendant ses horaires.

🔨 **Ce que je construis** :
- Modèles `PlageHoraire` (par jour) et `ParametreNotification` (intervalle, seuils, dernier envoi).
- Endpoints de configuration des plages et paramètres.
- Tâche `notifier_ca_periodique` (toutes les 15 min) : vérifie plage active + intervalle écoulé, calcule CA intervalle + CA jour + top service + comparaison veille (RG-09, RG-10).
- Tâche `bilan_fin_journee`.
- Écran de configuration des horaires et notifications.
- Tests avec temps figé (`freezegun`) sur tous les cas limites.

✅ **Comment tu testes** : tu configures une plage horaire et un intervalle court pour tester → tu reçois la notification de CA avec le bon montant. Je te montre les tests des cas limites au vert (hors plage, jour fermé, CA nul, passage de minuit).

🏁 **Critère de validation** : notification de CA reçue aux bons moments, cas limites testés.

---

## Étape 4.5 — Centre de notifications et réglages fins `[ ]`

🎯 **Objectif** : consulter dans l'app les notifications (une push peut être manquée).

🔨 **Ce que je construis** :
- Endpoints `/notifications/` + `/notifications/tout-lire/`.
- Cloche avec compteur, états non lue / lue / archivée.
- Réglages fins : activer/désactiver chaque type, mode « Ne pas déranger ».
- Autres notifications (écart de caisse, annulation, ouverture/clôture de session).

✅ **Comment tu testes** : la cloche affiche un compteur, tu ouvres le centre, tu marques comme lu. Tu désactives un type de notif dans les réglages.

🏁 **Critère de validation** : centre de notifications fonctionnel, réglages appliqués.

> **🎉 Fin de Phase 4** — Livrable : l'exigence différenciante du produit est opérationnelle.

---

# PHASE 5 — Tableau de bord et rapports (Lot 5)

## Étape 5.1 — Tableau de bord propriétaire `[ ]`

🎯 **Objectif** : piloter l'activité d'un coup d'œil.

🔨 **Ce que je construis** :
- Endpoint `GET /tableau-de-bord/` (agrégats du jour, cache Redis TTL 60 s).
- CA du jour en très grand + variation vs veille.
- Courbe CA 30 jours (**Recharts**), répartition par service (barres horizontales), top 5, bloc consommables sous seuil, performance par employé, marge brute estimée.

✅ **Comment tu testes** : tu ouvres le tableau de bord → tu vois ton CA du jour en grand, la courbe, les tops, les alertes stock.

🏁 **Critère de validation** : tableau de bord complet et juste.

---

## Étape 5.2 — Tableau de bord employé `[ ]`

🎯 **Objectif** : vue limitée pour l'employé.

🔨 **Ce que je construis** : sa session en cours, son total encaissé, ses dernières prestations, l'état du stock — **jamais** les marges ni les prix d'achat.

✅ **Comment tu testes** : connecté en tant qu'employé, tu vois ta session et ton total, mais pas les marges.

🏁 **Critère de validation** : cloisonnement des informations respecté.

---

## Étape 5.3 — Rapports et exports `[ ]`

🎯 **Objectif** : les rapports historiques.

🔨 **Ce que je construis** :
- App `rapports` : endpoints ventes / stock / rentabilité / caisse.
- Filtres par période, service, employé, mode de règlement.
- Exports **CSV** (listes) et **PDF** (synthèses).

✅ **Comment tu testes** : tu génères un rapport de ventes sur une période, tu l'exportes en CSV et en PDF.

🏁 **Critère de validation** : rapports justes, exports fonctionnels.

> **🎉 Fin de Phase 5** — Livrable : le propriétaire pilote son activité par les chiffres.

---

# PHASE 6 — Employés et clients (Lot 6)

## Étape 6.1 — Gestion des employés `[ ]`

🎯 **Objectif** : créer et gérer les comptes employés.

🔨 **Ce que je construis** :
- Endpoints `/employes/` + `/employes/{id}/desactiver/`.
- Création avec mot de passe provisoire (partage WhatsApp), changement obligatoire à la première connexion.
- Désactivation (jamais de suppression), clôture auto de la session ouverte.
- Fiche de suivi d'activité (sessions, CA généré, écarts, annulations).

✅ **Comment tu testes** : tu crées un employé, tu récupères son mot de passe provisoire, tu te connectes avec (changement imposé), puis tu le désactives.

🏁 **Critère de validation** : cycle de vie complet d'un employé.

---

## Étape 6.2 — Clients et créances `[ ]`

🎯 **Objectif** : gérer les ventes à crédit.

🔨 **Ce que je construis** :
- App `clients` : modèle `Client` (nom, téléphone, type, plafond de crédit, encours).
- Endpoints `/clients/` + `/clients/{id}/reglement/`.
- Vente en mode Crédit rattachée à un client (RG-13).
- Suivi de l'encours, règlements partiels, relance WhatsApp, rappel de créances échues.

✅ **Comment tu testes** : tu crées un client, tu lui fais une vente à crédit, tu enregistres un règlement partiel → l'encours diminue.

🏁 **Critère de validation** : gestion des créances fonctionnelle.

> **🎉 Fin de Phase 6** — Livrable : gestion du personnel et des clients à crédit.

---

# PHASE 7 — Hors ligne et PWA (Lot 7)

## Étape 7.1 — PWA installable `[ ]`

🎯 **Objectif** : l'app s'installe sur l'écran d'accueil.

🔨 **Ce que je construis** :
- `vite-plugin-pwa` (Workbox), manifeste, icônes.
- Stratégies de cache du service worker (shell, catalogue, polices).

✅ **Comment tu testes** : sur mobile/Chrome, tu vois « Ajouter à l'écran d'accueil ». L'app s'ouvre en plein écran comme une appli.

🏁 **Critère de validation** : PWA installable et lancée en mode standalone.

---

## Étape 7.2 — Lecture et écriture hors ligne `[ ]`

🎯 **Objectif** : vendre même sans réseau, **zéro perte de saisie**.

🔨 **Ce que je construis** :
- **Dexie.js** (IndexedDB) : cache du catalogue, consommables, session, prestations du jour.
- File de synchronisation locale avec `client_uuid` (idempotence).
- Badge « en attente de synchronisation », bandeau ambre hors ligne permanent.

✅ **Comment tu testes** : tu coupes le réseau (mode avion / DevTools offline), tu fais 3 ventes → elles s'enregistrent avec un badge « en attente ».

🏁 **Critère de validation** : ventes possibles hors ligne, aucune perte.

---

## Étape 7.3 — Synchronisation idempotente `[ ]`

🎯 **Objectif** : au retour du réseau, tout remonte sans doublon.

🔨 **Ce que je construis** :
- Endpoint `POST /prestations/synchroniser/` (envoi par lots, idempotent via `client_uuid`).
- Résolution de conflit : le serveur fait autorité sur le stock, acceptation en négatif avec alerte de régularisation (RG côté stock).
- Background Sync API.

✅ **Comment tu testes** : après tes 3 ventes hors ligne, tu réactives le réseau → les ventes remontent, le badge disparaît. Tu relances la synchro → aucun doublon créé.

🏁 **Critère de validation** : synchronisation sans doublon, stock recalculé côté serveur.

> **🎉 Fin de Phase 7** — Livrable : fonctionnement hors ligne robuste, testé sur coupure réelle.

---

# PHASE 8 — Finition, tests et production (Lot 8)

## Étape 8.1 — Thème sombre et accessibilité `[ ]`

🔨 Thème sombre (papier `#101215`), audit d'accessibilité (contraste AA/AAA, focus clavier, ARIA, navigation clavier de la grille de services).
✅ Tu bascules en thème sombre, tu navigues au clavier. Score Lighthouse Accessibilité ≥ 95.

## Étape 8.2 — Journal d'audit `[ ]`

🔨 App `audit` : middleware, `JournalAudit` (opérations sensibles avec valeurs avant/après, RG-16), endpoint `/audit/`.
✅ Tu changes un prix / fais un ajustement → l'action apparaît dans le journal d'audit avec l'avant/après.

## Étape 8.3 — Passe de performance `[ ]`

🔨 Découpage de code, virtualisation des listes, budget de bundle (≤ 200 Ko gzip), `select_related`/`prefetch_related`, tests `assertNumQueries`.
✅ Score Lighthouse Performance ≥ 85 sur mobile, bundle sous budget.

## Étape 8.4 — Pages d'erreur, tests E2E et documentation `[ ]`

🔨 Pages d'erreur soignées, **8 parcours Playwright** (§15.2 du cahier), documentation utilisateur (guide de démarrage, aide-mémoire caisse).
✅ Les 8 parcours critiques passent au vert.

## Étape 8.5 — Déploiement et mise en production `[ ]`

🔨 Configuration production (Nginx, Gunicorn, HTTPS/HSTS, en-têtes de sécurité, WhiteNoise), sauvegardes, supervision (Sentry, UptimeRobot), checklist de mise en production (annexe D).
✅ On déroule la checklist de mise en production ensemble.

> **🎉 Fin de Phase 8** — Livrable : SigmaGestion v1.0 en production.

---

## Récapitulatif des phases

| Phase | Contenu | Lot cahier | Étapes |
|---|---|---|---|
| 0 | Fondations et outillage | Lot 0 | 6 |
| 1 | Comptes, secrétariats, isolation | Lot 1 | 4 |
| 2 | Catalogue et stock | Lot 2 | 5 |
| 3 | Point de vente (cœur) | Lot 3 | 6 |
| 4 | Notifications push | Lot 4 | 5 |
| 5 | Tableaux de bord et rapports | Lot 5 | 3 |
| 6 | Employés et clients | Lot 6 | 2 |
| 7 | Hors ligne et PWA | Lot 7 | 3 |
| 8 | Finition, tests, production | Lot 8 | 5 |

**Prochaine action** : dès que tu me donnes le feu vert, on démarre par l'**Étape 0.1** (installation de Docker Desktop et Node.js). Je te guiderai pas à pas.

---

*Document de pilotage — à mettre à jour au fil de l'avancement.*
