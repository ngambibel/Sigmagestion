# SigmaGestion — Déploiement en production

Cible : un VPS Ubuntu 24.04 (≈ 4 vCPU / 8 Go), Docker + Docker Compose, un domaine pointé vers le serveur.

## Architecture

```
Navigateur ──HTTPS──► Nginx ──► PWA statique (/)  +  proxy /api,/admin,/static ──► Gunicorn (Django)
                                                                                   │
                                      Celery worker + beat ◄── Redis ──────────────┤
                                                     PostgreSQL ◄──────────────────┘
```

- **web** : Gunicorn (4 workers `gthread`), sert l'API + l'admin ; statiques via **WhiteNoise**.
- **nginx** : termine le TLS, sert la **PWA** et les **médias**, proxyfie l'API.
- **db / redis / celery_worker / celery_beat** : comme en dev, mais en `config.settings.prod`.

## Première mise en production

1. **DNS** : `sigmagestion.cm` et `www` → IP du VPS.
2. **Secrets** : `cp .env.prod.example .env` puis renseigner (clé Django unique, mots de passe forts, VAPID). Générer la clé :
   `python -c "import secrets;print(secrets.token_urlsafe(64))"`.
3. **Clés VAPID** : placer `private_key.pem` / `public_key.pem` dans `backend/` (déjà générées en 4.1) et reporter la clé publique dans `.env`.
4. **TLS (Let's Encrypt)** : obtenir les certificats (certbot) dans `deploy/certbot/conf`. Un premier démarrage en HTTP permet le challenge ACME.
5. **Lancer** : `docker compose -f docker-compose.prod.yml up -d --build`.
   - `web` applique **migrate** puis **collectstatic** automatiquement au démarrage.
6. **Super-administrateur** : `docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser`.
7. **Santé** : vérifier `https://sigmagestion.cm/api/v1/sante/` → `{"base":"ok","redis":"ok"}`.

## Déploiement d'une mise à jour (§16.4)

1. **Sauvegarde** base + médias, et vérifier la restaurabilité (`deploy/backup.sh`).
2. (option) activer la **page de maintenance** Nginx.
3. `git pull` puis `docker compose -f docker-compose.prod.yml up -d --build`.
4. `migrate` et `collectstatic` sont joués au démarrage du conteneur `web`.
5. Contrôle de santé sur `/api/v1/sante/`, puis surveillance Sentry ~30 min.

> Migrations : toujours réversibles ou avec plan de retour arrière. Les suppressions de colonne se font en **deux** déploiements.

## Sauvegardes (§16.5)

`deploy/backup.sh` (cron 02 h) : `pg_dump` + archive des médias, rétention 30 j, à **répliquer hors serveur**. **Test de restauration mensuel obligatoire.**

## Supervision (§16.6)

- **Sentry** : renseigner `SENTRY_DSN` dans `.env` (backend) ; brancher aussi le SDK front si souhaité.
- **UptimeRobot** : surveiller `https://sigmagestion.cm/api/v1/sante/`.
- **Logs** : `docker compose -f docker-compose.prod.yml logs -f` (sortie structurée).

---

## Checklist de mise en production (annexe D du cahier)

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
