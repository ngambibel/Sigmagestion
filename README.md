# SigmaGestion

PWA multi-locataire de gestion de secrétariat bureautique (Cameroun, XAF).

**Stack** : Django 5 + DRF + PostgreSQL 16 + Celery/Redis (back) · React 18 + Vite + TypeScript + Tailwind + Radix + TanStack Query + Zustand + Dexie (front).

## Prérequis

- Docker Desktop (backend WSL2)
- Node.js 20+
- Git

## Démarrage rapide

```powershell
# 1. Copier le fichier d'environnement
Copy-Item .env.example .env

# 2. Lancer l'infrastructure (PostgreSQL + Redis)
docker compose up -d db redis

# 3. Vérifier l'état
docker compose ps
```

Les deux conteneurs `db` et `redis` doivent apparaître **running / healthy**.

## Structure du dépôt

```
SigmaGestion/
├── backend/                     # API Django + DRF (étape 0.3+)
├── frontend/                    # PWA React + Vite (phase ultérieure)
├── docker-compose.yml           # Infrastructure locale
├── .env.example                 # Modèle de configuration
├── SigmaGestion-Cahier-des-Charges.md
└── PLAN-DE-CONSTRUCTION.md      # Suivi de la construction
```

## Suivi

Voir `PLAN-DE-CONSTRUCTION.md` pour l'avancement étape par étape.
