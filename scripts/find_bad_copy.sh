#!/bin/bash
echo "=== recent data_story / explain headlines ==="
sudo docker logs violyt-deploy-api-1 --since 40m 2>&1 \
  | grep -E '98000|98,000|Everything you need|data_story_prompt_built|explain_ai_prompt|Greenfield|India needs a lot' \
  | tail -40

echo
echo "=== last image gen prompt fragment (if logged) ==="
sudo docker logs violyt-deploy-api-1 --since 40m 2>&1 \
  | grep -oE 'LABEL "[^"]{0,80}"|ROW[0-9]: "[^"]{0,100}"|FIGURE "[^"]{0,40}"' \
  | tail -40
