#!/usr/bin/env bash
# Backup van database en bestanden van de Shopware-stack.
# Draai vanuit de projectmap (waar compose.yaml staat). Doelmap als eerste argument.
set -euo pipefail

DOEL="${1:-/var/backups/shop}"
STEMPEL="$(date +%Y%m%d-%H%M%S)"
PROJECT="$(basename "$PWD")"
mkdir -p "$DOEL"

# Database: het root-wachtwoord staat al in de omgeving van de databasecontainer
docker compose exec -T database sh -c \
  'mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" --single-transaction --routines --triggers shopware' \
  | gzip > "$DOEL/db-$STEMPEL.sql.gz"

# Bestanden: media (productfoto's) en files (facturen, uploads).
# theme, thumbnail en sitemap zijn opnieuw te genereren en gaan niet mee.
for vol in media files; do
  docker run --rm \
    -v "${PROJECT}_${vol}":/data:ro \
    -v "$DOEL":/backup \
    alpine tar czf "/backup/${vol}-$STEMPEL.tar.gz" -C /data .
done

# ponytail: 14 dagen lokaal bewaren; externe kopie is een aparte stap
find "$DOEL" -name '*.gz' -mtime +14 -delete
echo "backup klaar: $DOEL/*-$STEMPEL.*"
