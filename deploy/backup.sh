#!/usr/bin/env bash
# Sauvegarde quotidienne de la base et des médias (§16.5).
# À planifier via cron :  0 2 * * *  /chemin/deploy/backup.sh >> /var/log/sigma-backup.log 2>&1
# Une sauvegarde jamais restaurée n'est pas une sauvegarde : testez la restauration chaque mois.
set -euo pipefail

DEST="${BACKUP_DEST:-/var/backups/sigmagestion}"
HORODATAGE="$(date +%Y%m%d-%H%M)"
RETENTION_JOURS="${BACKUP_RETENTION:-30}"
mkdir -p "$DEST"

echo "[$(date)] Sauvegarde base de données…"
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "${POSTGRES_USER:-sigma}" "${POSTGRES_DB:-sigmagestion}" \
  | gzip > "$DEST/db-$HORODATAGE.sql.gz"

echo "[$(date)] Sauvegarde médias…"
docker run --rm -v sigmagestion_media:/media -v "$DEST":/sauvegarde alpine \
  tar czf "/sauvegarde/media-$HORODATAGE.tar.gz" -C /media .

echo "[$(date)] Purge des sauvegardes de plus de $RETENTION_JOURS jours…"
find "$DEST" -name "db-*.sql.gz" -mtime +"$RETENTION_JOURS" -delete
find "$DEST" -name "media-*.tar.gz" -mtime +"$RETENTION_JOURS" -delete

echo "[$(date)] Sauvegarde terminée → $DEST"
# Pensez à répliquer $DEST vers un stockage objet HORS du serveur (rclone, aws s3 sync…).
