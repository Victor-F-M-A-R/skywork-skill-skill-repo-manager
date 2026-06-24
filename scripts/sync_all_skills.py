#!/usr/bin/env python3
"""
sync_all_skills.py — Sincroniza skills Skywork → GitHub repos
Uso: python3 sync_all_skills.py --token ghp_xxx [--skill nome] [--dry-run]
"""
import os, sys, json, base64, time, hashlib, argparse, requests
from pathlib import Path

USERNAME = "Victor-F-M-A-R"
SKILLS_SRC = "/data/workspace/_shared/.oma_remote_skill"

SKILLS = [
    "animations","architecture-designer","artifacts-builder","content_marketing",
    "create-prd","ds","extract-design","frontend-design","marketing-psychology",
    "short-drama-writer","stock-market-industry-analyst-and-predictor",
    "template-based-apa-professional-paper","template-based-business-analysis-report",
    "template-based-competitive-analysis","template-based-general-service-agreement",
    "web-design-engineer","youtube-watcher","skill-repo-manager",
]

def git_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()

def get_skill_dir(skill_name: str) -> Path | None:
    base = Path(SKILLS_SRC) / skill_name
    if not base.exists():
        return None
    subdirs = [d for d in base.iterdir() if d.is_dir()]
    return subdirs[0] if subdirs else base

def sync_skill(token: str, skill_name: str, dry_run: bool = False) -> dict:
    repo = f"skywork-skill-{skill_name}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    skill_dir = get_skill_dir(skill_name)
    if not skill_dir:
        return {"skill": skill_name, "status": "error", "reason": "source_not_found"}

    files = {}
    for f in skill_dir.rglob("*"):
        if f.is_file():
            files[str(f.relative_to(skill_dir))] = f.read_bytes()

    pushed, skipped, errors = 0, 0, 0
    for path, content in files.items():
        url = f"https://api.github.com/repos/{USERNAME}/{repo}/contents/{path}"
        r = requests.get(url, headers=headers)
        payload = {"message": f"sync: {path}", "content": base64.b64encode(content).decode()}

        if r.status_code == 200:
            remote_sha = r.json().get("sha", "")
            if remote_sha == git_sha(content):
                skipped += 1
                continue
            payload["sha"] = remote_sha

        if dry_run:
            print(f"  [DRY-RUN] Would push: {path}")
            pushed += 1
            continue

        r2 = requests.put(url, headers=headers, json=payload)
        if r2.status_code in (200, 201):
            pushed += 1
        else:
            errors += 1
            print(f"  ❌ {path}: {r2.status_code}")
        time.sleep(0.2)

    return {"skill": skill_name, "status": "ok", "pushed": pushed, "skipped": skipped, "errors": errors}

def main():
    parser = argparse.ArgumentParser(description="Sync Skywork skills to GitHub")
    parser.add_argument("--token", required=True, help="GitHub PAT token")
    parser.add_argument("--skill", help="Sync only this skill (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without pushing")
    args = parser.parse_args()

    targets = [args.skill] if args.skill else SKILLS
    results = []

    print(f"\n🔄 Sincronizando {len(targets)} skill(s){'  [DRY-RUN]' if args.dry_run else ''}...\n")
    for skill in targets:
        print(f"📦 {skill}")
        r = sync_skill(args.token, skill, args.dry_run)
        results.append(r)
        if r["status"] == "ok":
            print(f"   ✅ pushed={r['pushed']}  skipped={r['skipped']}  errors={r['errors']}")
        else:
            print(f"   ❌ {r.get('reason')}")

    ok = sum(1 for r in results if r["status"] == "ok")
    total_pushed = sum(r.get("pushed", 0) for r in results)
    print(f"\n📊 {ok}/{len(targets)} skills OK — {total_pushed} arquivos atualizados")

if __name__ == "__main__":
    main()
