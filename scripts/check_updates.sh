#!/bin/bash
# check_updates.sh — Detecta skills desatualizadas no GitHub vs fonte Skywork
# Uso: bash check_updates.sh <GITHUB_TOKEN>

TOKEN="${1:-$GITHUB_TOKEN}"
USERNAME="Victor-F-M-A-R"
BASE="/data/workspace/_shared/.oma_remote_skill"

if [ -z "$TOKEN" ]; then
  echo "❌ Token não fornecido. Uso: bash check_updates.sh <TOKEN>"
  exit 1
fi

SKILLS=(
  "animations" "architecture-designer" "artifacts-builder" "content_marketing"
  "create-prd" "ds" "extract-design" "frontend-design" "marketing-psychology"
  "short-drama-writer" "stock-market-industry-analyst-and-predictor"
  "template-based-apa-professional-paper" "template-based-business-analysis-report"
  "template-based-competitive-analysis" "template-based-general-service-agreement"
  "web-design-engineer" "youtube-watcher" "skill-repo-manager"
)

CHANGED=()
IN_SYNC=()
NOT_FOUND=()

echo ""
echo "🔍 Verificando sincronização de skills..."
echo "   Comparando: Skywork local → GitHub repos"
echo ""

for SKILL in "${SKILLS[@]}"; do
  HASH_DIR=$(ls "$BASE/$SKILL/" 2>/dev/null | head -1)
  SRC="$BASE/$SKILL/$HASH_DIR"
  SKILL_MD="$SRC/SKILL.md"
  REPO="skywork-skill-$SKILL"

  if [ ! -f "$SKILL_MD" ]; then
    echo "  ⬜ $SKILL — fonte não encontrada localmente"
    NOT_FOUND+=("$SKILL")
    continue
  fi

  REMOTE_SHA=$(curl -s \
    -H "Authorization: token $TOKEN" \
    "https://api.github.com/repos/$USERNAME/$REPO/contents/SKILL.md" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sha','NOT_FOUND'))" 2>/dev/null)

  LOCAL_SHA=$(python3 -c "
import hashlib
content = open('$SKILL_MD', 'rb').read()
header = f'blob {len(content)}\0'.encode()
print(hashlib.sha1(header + content).hexdigest())
" 2>/dev/null)

  if [ "$REMOTE_SHA" = "NOT_FOUND" ]; then
    echo "  ❓ $SKILL — repo GitHub não encontrado"
    NOT_FOUND+=("$SKILL")
  elif [ "$REMOTE_SHA" = "$LOCAL_SHA" ]; then
    echo "  ✅ $SKILL — em sincronia"
    IN_SYNC+=("$SKILL")
  else
    echo "  ⚠️  $SKILL — DESATUALIZADO"
    echo "     Local : $LOCAL_SHA"
    echo "     GitHub: $REMOTE_SHA"
    CHANGED+=("$SKILL")
  fi
  sleep 0.3
done

echo ""
echo "════════════════════════════════════════"
echo "📊 RESULTADO:"
echo "   ✅ Em sincronia : ${#IN_SYNC[@]}"
echo "   ⚠️  Desatualizados: ${#CHANGED[@]}"
echo "   ❓ Não encontrados: ${#NOT_FOUND[@]}"

if [ ${#CHANGED[@]} -gt 0 ]; then
  echo ""
  echo "🔄 Para sincronizar:"
  echo "   python3 scripts/sync_all_skills.py --token \$TOKEN --skill <nome>"
  echo ""
  echo "   Skills com mudanças:"
  for s in "${CHANGED[@]}"; do echo "     - $s"; done
fi
echo ""
