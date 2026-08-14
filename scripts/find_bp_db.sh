#!/bin/bash
# Pull the airport blueprint from DB / chat if checkpoint missed it.
sudo docker exec -i violyt-deploy-postgres-1 psql -U violyt -d violyt -tAX -q <<'SQL' 2>/dev/null | head -80
SELECT left(content::text, 500)
FROM chat_messages
WHERE content::text ILIKE '%98000%' OR content::text ILIKE '%98,000%' OR content::text ILIKE '%Everything you need%'
ORDER BY created_at DESC
LIMIT 5;
SQL
