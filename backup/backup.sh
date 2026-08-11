#!/bin/sh
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/backups/pyconci_${TIMESTAMP}.sql.gz"

echo "Démarrage de la sauvegarde : ${BACKUP_FILE}"

PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
  -h "${POSTGRES_HOST}" \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  | gzip > "${BACKUP_FILE}"

echo "Sauvegarde terminée."

# Garde seulement les 7 derniers jours de sauvegardes
find /backups -name "pyconci_*.sql.gz" -mtime +7 -delete

echo "Nettoyage des anciennes sauvegardes effectué."