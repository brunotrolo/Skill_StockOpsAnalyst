#!/usr/bin/env bash
# build_skill_bundle.sh
#
# Skills no claude.ai são enviadas como zip autocontido e não enxergam
# .claude/skills/_shared/ fora da própria pasta da skill. Este script:
#   1. Para cada skill em .claude/skills/<nome>/ (exceto _shared/),
#      copia portfolio_params.yaml e golden_rules.md de _shared/ para
#      dentro da pasta da skill (sobrescrevendo a cópia anterior).
#   2. Gera um .zip de cada skill em dist/, pronto para upload em claude.ai.
#
# A fonte de edição continua sendo _shared/ — nunca edite as cópias
# sincronizadas dentro da pasta de cada skill diretamente, pois serão
# sobrescritas na próxima execução.
#
# Uso:
#   .claude/skills/build_skill_bundle.sh              # todas as skills
#   .claude/skills/build_skill_bundle.sh nome-da-skill # só uma skill

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR"
SHARED_DIR="$SKILLS_DIR/_shared"
DIST_DIR="$SKILLS_DIR/dist"

SHARED_FILES=("portfolio_params.yaml" "golden_rules.md")

if [[ ! -d "$SHARED_DIR" ]]; then
  echo "ERRO: $SHARED_DIR não existe." >&2
  exit 1
fi

for f in "${SHARED_FILES[@]}"; do
  if [[ ! -f "$SHARED_DIR/$f" ]]; then
    echo "ERRO: $SHARED_DIR/$f não existe." >&2
    exit 1
  fi
done

mkdir -p "$DIST_DIR"

target_skills=()
if [[ $# -gt 0 ]]; then
  target_skills=("$@")
else
  for dir in "$SKILLS_DIR"/*/; do
    name="$(basename "$dir")"
    [[ "$name" == "_shared" || "$name" == "dist" ]] && continue
    target_skills+=("$name")
  done
fi

if [[ ${#target_skills[@]} -eq 0 ]]; then
  echo "Nenhuma skill encontrada em $SKILLS_DIR (além de _shared/)."
  exit 0
fi

for name in "${target_skills[@]}"; do
  skill_dir="$SKILLS_DIR/$name"
  if [[ ! -d "$skill_dir" ]]; then
    echo "AVISO: skill '$name' não encontrada em $SKILLS_DIR, pulando." >&2
    continue
  fi

  echo "==> Sincronizando arquivos compartilhados em '$name'"
  for f in "${SHARED_FILES[@]}"; do
    cp "$SHARED_DIR/$f" "$skill_dir/$f"
  done

  zip_path="$DIST_DIR/${name}.zip"
  echo "==> Gerando $zip_path"
  rm -f "$zip_path"
  (cd "$skill_dir" && zip -rq "$zip_path" . -x '*.DS_Store')

  echo "==> OK: $name"
done

echo ""
echo "Pacotes gerados em: $DIST_DIR"
