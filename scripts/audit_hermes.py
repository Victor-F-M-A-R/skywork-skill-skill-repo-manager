#!/usr/bin/env python3
"""
audit_hermes.py — Audita e corrige skills para compatibilidade com Hermes
Uso: python3 audit_hermes.py [--skill nome] [--fix] [--all]
"""
import re, sys, argparse
from pathlib import Path

SKILLS_SRC = "/data/workspace/_shared/.oma_remote_skill"

TOOL_RENAMES = {
    "Read": "read", "Write": "write", "Bash": "bash",
    "Glob": "glob", "Grep": "grep", "WebSearch": "web_search",
    "TodoWrite": "todowrite", "Skill": "load_skill",
}

ENV_RENAMES = {
    "${CLAUDE_SKILL_DIR}": "${HERMES_SKILL_DIR}",
    "${CLAUDE_PLUGIN_ROOT}": "${HERMES_PLUGIN_ROOT}",
    "CLAUDE_SKILL_DIR": "HERMES_SKILL_DIR",
    "CLAUDE_PLUGIN_ROOT": "HERMES_PLUGIN_ROOT",
}

def get_skill_dir(skill_name):
    base = Path(SKILLS_SRC) / skill_name
    if not base.exists():
        return None
    subdirs = [d for d in base.iterdir() if d.is_dir()]
    return subdirs[0] if subdirs else base

def audit_skill(skill_path: Path) -> dict:
    content = skill_path.read_text(encoding="utf-8", errors="replace")
    issues, fixes = [], []

    if not re.search(r'^name:', content, re.MULTILINE):
        issues.append(("error", "Frontmatter 'name' ausente"))

    if "{{ product_language }}" in content:
        issues.append(("warn", "Placeholder {{ product_language }} não resolvido"))
        fixes.append(("{{ product_language }}", "Português (Brasil)"))

    if '"clawdbot"' in content:
        issues.append(("warn", "Metadata 'clawdbot' → deve ser 'hermes'"))
        fixes.append(('"clawdbot"', '"hermes"'))

    if "{baseDir}" in content:
        issues.append(("warn", "Placeholder {baseDir} encontrado — verificar contexto"))

    for old, new in ENV_RENAMES.items():
        if old in content:
            issues.append(("warn", f"Variável Claude: '{old}' → '{new}'"))
            fixes.append((old, new))

    in_code_block = False
    for line in content.split("\n"):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
        if not in_code_block:
            for old, new in TOOL_RENAMES.items():
                if re.search(rf'\b{re.escape(old)}\b', line):
                    if f"→ '{new}'" not in line and f"-> {new}" not in line:
                        issues.append(("info", f"Ferramenta '{old}' → renomear para '{new}'"))
                        fixes.append((old, new))
                        break

    seen = set()
    deduped_issues = []
    for issue in issues:
        key = issue[1]
        if key not in seen:
            seen.add(key)
            deduped_issues.append(issue)

    seen_fixes = set()
    deduped_fixes = []
    for fix in fixes:
        if fix[0] not in seen_fixes:
            seen_fixes.add(fix[0])
            deduped_fixes.append(fix)

    return {"issues": deduped_issues, "fixes": deduped_fixes}

def apply_fixes(skill_path: Path, fixes: list) -> int:
    content = skill_path.read_text(encoding="utf-8", errors="replace")
    applied = 0
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            applied += 1
    skill_path.write_text(content, encoding="utf-8")
    return applied

def audit_skill_name(skill_name, fix=False):
    skill_dir = get_skill_dir(skill_name)
    if not skill_dir:
        print(f"  ❌ Diretório não encontrado: {skill_name}")
        return

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"  ❌ SKILL.md não encontrado em {skill_dir}")
        return

    result = audit_skill(skill_md)
    errors   = [i for i in result["issues"] if i[0] == "error"]
    warnings = [i for i in result["issues"] if i[0] == "warn"]
    infos    = [i for i in result["issues"] if i[0] == "info"]

    if not result["issues"]:
        print(f"  ✅ {skill_name} — compatível com Hermes")
        return

    print(f"  📋 {skill_name}:")
    for level, msg in errors:   print(f"    ❌ {msg}")
    for level, msg in warnings: print(f"    ⚠️  {msg}")
    for level, msg in infos:    print(f"    ℹ️  {msg}")

    if fix and result["fixes"]:
        applied = apply_fixes(skill_md, result["fixes"])
        print(f"    🔧 {applied} correções aplicadas automaticamente")

def main():
    parser = argparse.ArgumentParser(description="Audita skills para compatibilidade com Hermes")
    parser.add_argument("--skill", help="Nome da skill específica")
    parser.add_argument("--all", action="store_true", help="Auditar todas as skills")
    parser.add_argument("--fix", action="store_true", help="Aplicar correções automáticas")
    args = parser.parse_args()

    ALL_SKILLS = [
        "animations","architecture-designer","artifacts-builder","content_marketing",
        "create-prd","ds","extract-design","frontend-design","marketing-psychology",
        "short-drama-writer","stock-market-industry-analyst-and-predictor",
        "template-based-apa-professional-paper","template-based-business-analysis-report",
        "template-based-competitive-analysis","template-based-general-service-agreement",
        "web-design-engineer","youtube-watcher",
    ]

    targets = ALL_SKILLS if args.all else ([args.skill] if args.skill else ALL_SKILLS)
    print(f"\n🔍 Auditoria Hermes — {len(targets)} skill(s){'  [--fix ativo]' if args.fix else ''}\n")
    for skill in targets:
        audit_skill_name(skill, fix=args.fix)
    print()

if __name__ == "__main__":
    main()
