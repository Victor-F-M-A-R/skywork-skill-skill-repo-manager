---
name: skill-repo-manager
description: >
  Gerencia, sincroniza e audita os repositórios GitHub das skills do agente Hermes.
  Use para: sincronizar skills com o Skywork, detectar atualizações, aplicar topics/descrições,
  criar novos repos de skill, auditar compatibilidade Hermes, e manter o hub central atualizado.
  Trigger quando o usuário mencionar: 'sincronizar skills', 'atualizar repos', 'verificar skills',
  'novo repo de skill', 'auditar skill', 'hub de skills', 'check skills', 'skill desatualizada'.
version: 1.0.0
author: Victor-F-M-A-R
agent: hermes
metadata:
  emoji: "🗂️"
  requires:
    bins: ["git", "curl", "python3"]
  os: ["linux", "darwin", "win32"]
allowed-tools: Bash, Read, Write, Glob, WebSearch
---

# Skill Repo Manager

Gerencia o ciclo de vida completo dos repositórios GitHub das skills do agente Hermes —
desde criação e push inicial até sincronização periódica, detecção de mudanças e auditoria
de compatibilidade.

## Contexto do Ambiente

| Variável | Valor |
|----------|-------|
| GitHub User | `Victor-F-M-A-R` |
| Hub Central | `skywork-skills-hub` |
| Skills Skywork (fonte) | `/data/workspace/_shared/.oma_remote_skill/<skill>/<hash>/` |
| Prefixo repos | `skywork-skill-<nome>` |
| Total de skills | 18 (17 originais + skill-repo-manager) |

**Nota:** O token PAT deve ser fornecido pelo usuário a cada sessão — nunca armazene tokens em memória ou arquivos.

---

## Comandos Disponíveis

O agente reconhece as seguintes intenções e executa o fluxo correspondente:

| Intenção do usuário | Fluxo a executar |
|---|---|
| "sincronizar skills" / "sync skills" | [Fluxo 1: Sincronização Completa](#fluxo-1-sincronização-completa) |
| "verificar atualizações" / "check updates" | [Fluxo 2: Detecção de Mudanças](#fluxo-2-detecção-de-mudanças) |
| "criar repo skill X" | [Fluxo 3: Novo Repositório](#fluxo-3-novo-repositório) |
| "auditar skill X" | [Fluxo 4: Auditoria Hermes](#fluxo-4-auditoria-hermes) |
| "atualizar topics" / "organizar repos" | [Fluxo 5: Organização GitHub](#fluxo-5-organização-github) |
| "status do hub" / "hub status" | [Fluxo 6: Status Hub Central](#fluxo-6-status-hub-central) |

---

## Fluxo 1: Sincronização Completa

Sincroniza o conteúdo atual de todas as skills Skywork com os repos GitHub.

```python
# scripts/sync_all_skills.py
import os, json, base64, time, requests
from pathlib import Path

def sync_skill(token, username, skill_name, skill_src_dir):
    """Sincroniza um diretório de skill com o repo GitHub correspondente."""
    repo = f"skywork-skill-{skill_name}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    files = {}
    for f in Path(skill_src_dir).rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(skill_src_dir))
            files[rel] = f.read_bytes()
    
    pushed, skipped = 0, 0
    for path, content in files.items():
        url = f"https://api.github.com/repos/{username}/{repo}/contents/{path}"
        existing = requests.get(url, headers=headers)
        payload = {
            "message": f"sync: update {path}",
            "content": base64.b64encode(content).decode()
        }
        if existing.status_code == 200:
            remote_sha = existing.json()["sha"]
            # Só atualiza se o conteúdo mudou
            remote_content = base64.b64decode(existing.json()["content"].replace("\n",""))
            if remote_content == content:
                skipped += 1
                continue
            payload["sha"] = remote_sha
        
        r = requests.put(url, headers=headers, json=payload)
        if r.status_code in (200, 201):
            pushed += 1
        time.sleep(0.2)
    
    return {"pushed": pushed, "skipped": skipped, "total": len(files)}
```

**Passos do fluxo:**
1. Solicitar token PAT ao usuário (se não fornecido)
2. Mapear diretórios fonte em `/data/workspace/_shared/.oma_remote_skill/`
3. Para cada skill: comparar SHA dos arquivos com o repo GitHub
4. Fazer push apenas dos arquivos que mudaram
5. Atualizar submodule no hub central
6. Reportar resumo: `N arquivos atualizados, M sem mudanças`

---

## Fluxo 2: Detecção de Mudanças

Verifica quais skills foram atualizadas no Skywork sem fazer push.

```bash
#!/bin/bash
# scripts/check_updates.sh
BASE="/data/workspace/_shared/.oma_remote_skill"
TOKEN="$1"
USERNAME="Victor-F-M-A-R"

echo "🔍 Verificando atualizações das skills..."
echo ""

CHANGED=()
UPDATED=()

for SKILL_DIR in "$BASE"/*/; do
    SKILL_NAME=$(basename "$SKILL_DIR")
    HASH_DIR=$(ls "$SKILL_DIR" 2>/dev/null | head -1)
    SRC="$SKILL_DIR/$HASH_DIR"
    REPO="skywork-skill-$SKILL_NAME"
    
    if [ ! -f "$SRC/SKILL.md" ]; then continue; fi
    
    # Buscar SHA do SKILL.md no GitHub
    REMOTE=$(curl -s -H "Authorization: token $TOKEN" \
        "https://api.github.com/repos/$USERNAME/$REPO/contents/SKILL.md" \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sha',''))" 2>/dev/null)
    
    # Calcular SHA local (formato Git: "blob <size>\0<content>")
    LOCAL=$(python3 -c "
import sys, hashlib
content = open('$SRC/SKILL.md', 'rb').read()
header = f'blob {len(content)}\0'.encode()
sha1 = hashlib.sha1(header + content).hexdigest()
print(sha1)
" 2>/dev/null)
    
    if [ "$REMOTE" != "$LOCAL" ]; then
        echo "  ⚠️  MUDANÇA DETECTADA: $SKILL_NAME"
        echo "     Local:  $LOCAL"
        echo "     GitHub: $REMOTE"
        CHANGED+=("$SKILL_NAME")
    else
        echo "  ✅ $SKILL_NAME — em sincronia"
        UPDATED+=("$SKILL_NAME")
    fi
done

echo ""
echo "📊 Resultado: ${#CHANGED[@]} com mudanças, ${#UPDATED[@]} em sincronia"
if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "   Skills desatualizadas: ${CHANGED[*]}"
    echo "   Execute o Fluxo 1 para sincronizar."
fi
```

---

## Fluxo 3: Novo Repositório

Cria um novo repositório GitHub para uma skill.

**Passos:**
1. Verificar se repo já existe: `GET /repos/{username}/{repo_name}`
2. Criar repo: `POST /user/repos` com nome, descrição e topics
3. Criar `README.md` com documentação inicial
4. Fazer push de todos os arquivos da skill
5. Adicionar como submodule no hub central
6. Atualizar `README.md` do hub com novo entry

**Estrutura mínima de um repo de skill:**
```
skywork-skill-<nome>/
├── README.md          ← documentação gerada
├── SKILL.md           ← instruções/prompts principais (obrigatório)
├── skill-card.md      ← cartão de apresentação (se existir)
├── references/        ← arquivos de referência (se existir)
└── scripts/           ← scripts auxiliares (se existir)
```

---

## Fluxo 4: Auditoria Hermes

Verifica e adapta uma skill para compatibilidade com o agente Hermes.

**Checklist de compatibilidade:**

| Item | O que verificar | Ação se falhar |
|------|----------------|----------------|
| Frontmatter `name` | Existe e é snake_case ou kebab-case | Adicionar/corrigir |
| Frontmatter `description` | Presente e em Português ou bilíngue | Traduzir/complementar |
| Referências de ferramentas | Usa nomes corretos do Hermes (`bash`, `read`, `write`, `glob`, `web_search`) | Substituir aliases incorretos |
| Placeholder `{{ product_language }}` | Resolução para `Português (Brasil)` | Substituir |
| Metadados `clawdbot` | Converter para `hermes` | Atualizar bloco metadata |
| Dependências binárias | Documentadas em `requires.bins` | Adicionar seção de instalação |
| Variáveis de ambiente | `${CLAUDE_SKILL_DIR}` → `${HERMES_SKILL_DIR}` | Substituir |
| `allowed-tools` | Listar apenas ferramentas disponíveis no Hermes | Revisar lista |
| Hooks | Paths de scripts existem no repo | Verificar e ajustar |
| Idioma das instruções | Compatível com uso em Português | Adicionar notas PT-BR se necessário |

**Script de auditoria automática:**
```python
# scripts/audit_hermes.py
import re, sys
from pathlib import Path

TOOL_MAP = {
    "Read": "read", "Write": "write", "Bash": "bash",
    "Glob": "glob", "WebSearch": "web_search", "Grep": "grep",
    "TodoWrite": "todowrite", "Skill": "load_skill",
}

HERMES_TOOLS = {"bash","read","write","glob","web_search","grep",
                "todowrite","load_skill","web_crawl","jupyter_execute"}

def audit_skill(skill_path: Path) -> dict:
    content = skill_path.read_text(encoding="utf-8")
    issues = []
    fixes = []
    
    # 1. Verificar frontmatter name
    if not re.search(r'^name:', content, re.MULTILINE):
        issues.append("❌ Frontmatter 'name' ausente")
    
    # 2. Verificar placeholder de idioma
    if "{{ product_language }}" in content:
        issues.append("⚠️  Placeholder {{ product_language }} não resolvido")
        fixes.append(("{{ product_language }}", "Português (Brasil)"))
    
    # 3. Verificar metadados clawdbot
    if "clawdbot" in content:
        issues.append("⚠️  Metadados 'clawdbot' devem ser convertidos para 'hermes'")
    
    # 4. Verificar variáveis de ambiente do Claude
    for var in ["${CLAUDE_SKILL_DIR}", "${CLAUDE_PLUGIN_ROOT}"]:
        if var in content:
            issues.append(f"⚠️  Variável Claude detectada: {var} → use ${{{var[2:-1].replace('CLAUDE','HERMES')}}}")
    
    # 5. Verificar referências de ferramentas com capitalização errada
    for old, new in TOOL_MAP.items():
        pattern = rf'\b{old}\b'
        if re.search(pattern, content):
            issues.append(f"ℹ️  Ferramenta '{old}' → renomear para '{new}'")
            fixes.append((old, new))
    
    return {"issues": issues, "fixes": fixes, "path": str(skill_path)}

def apply_fixes(skill_path: Path, fixes: list):
    content = skill_path.read_text(encoding="utf-8")
    for old, new in fixes:
        content = content.replace(old, new)
    # Atualizar metadata clawdbot → hermes
    content = content.replace('"clawdbot":', '"hermes":')
    skill_path.write_text(content, encoding="utf-8")
    return content

if __name__ == "__main__":
    skill_path = Path(sys.argv[1])
    result = audit_skill(skill_path)
    
    print(f"\n🔍 Auditoria: {skill_path}")
    if not result["issues"]:
        print("  ✅ Skill compatível com Hermes — nenhum problema encontrado")
    else:
        for issue in result["issues"]:
            print(f"  {issue}")
    
    if "--fix" in sys.argv and result["fixes"]:
        apply_fixes(skill_path, result["fixes"])
        print(f"\n  🔧 {len(result['fixes'])} correções aplicadas automaticamente")
```

---

## Fluxo 5: Organização GitHub

Aplica topics e descrições padronizadas nos repos.

**Padrão de topics por categoria:**

| Categoria | Topics obrigatórios | Topics específicos |
|-----------|--------------------|--------------------|
| Todas as skills | `skywork`, `ai-skill`, `prompt-engineering`, `hermes-agent` | — |
| Frontend/Web | + `frontend`, `web`, `html`, `css` | nome do framework |
| Backend/Arquitetura | + `backend`, `architecture`, `system-design` | padrão usado |
| Marketing | + `marketing`, `strategy` | canal ou método |
| Documentos/Templates | + `template`, `document`, `word` | tipo de doc |
| Data Science | + `data-science`, `python`, `analysis` | — |
| Finanças | + `finance`, `trading` | mercado |

**Formato de descrição:**
```
<emoji> Skywork/Hermes Skill: <descrição cursa em inglês, max 100 chars>
```

---

## Fluxo 6: Status Hub Central

Exibe o status atual do hub e de todos os submodules.

```bash
# Ver status dos submodules
cd skywork-skills-hub
git submodule status

# Ver quais estão desatualizados (atrás do remote)
git submodule foreach 'git fetch --quiet && \
  BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null); \
  [ "$BEHIND" -gt 0 ] && echo "⚠️  $name: $BEHIND commit(s) atrás" || echo "✅ $name"'
```

---

## Referências de Configuração

### GitHub API endpoints usados

| Operação | Método | Endpoint |
|----------|--------|----------|
| Criar repo | POST | `/user/repos` |
| Atualizar repo | PATCH | `/repos/{owner}/{repo}` |
| Criar/atualizar arquivo | PUT | `/repos/{owner}/{repo}/contents/{path}` |
| Aplicar topics | PUT | `/repos/{owner}/{repo}/topics` |
| Listar repos | GET | `/user/repos` |
| Verificar arquivo | GET | `/repos/{owner}/{repo}/contents/{path}` |

### Variáveis de ambiente esperadas

```bash
export GITHUB_TOKEN="ghp_..."        # Token PAT com escopo 'repo'
export GITHUB_USERNAME="Victor-F-M-A-R"
export SKILLS_HUB_DIR="./skywork-skills-hub"
export SKILLS_SRC_BASE="/data/workspace/_shared/.oma_remote_skill"
```

### Rate limits GitHub API
- Autenticado: **5.000 req/hora**
- Topics (mercy-preview): mesmos limites
- Recomendado: `time.sleep(0.2)` entre requests em batch

---

## Manutenção e Segurança

### Token PAT
- **Nunca** salvar em arquivos ou memória persistente
- Solicitar ao usuário no início de cada sessão
- Escopo mínimo necessário: `repo` (para repos públicos e privados)
- Revogar e regenerar periodicamente: [github.com/settings/tokens](https://github.com/settings/tokens)

### Checklist Periódico

| Frequência | Ação |
|-----------|------|
| **Semanal** | GitHub Action automática no hub (sync submodules) |
| **Mensal** | Executar Fluxo 2 (detecção de mudanças) + Fluxo 4 (auditoria) |
| **Trimestral** | Revisar topics/descrições + renovar PAT |
| **Ao instalar nova skill** | Executar Fluxo 3 + adicionar submodule no hub |

---

## Notas para o Agente Hermes

- Este SKILL.md está escrito primariamente em **Português (Brasil)**
- Todas as respostas ao usuário devem usar **Português (Brasil)**
- O agente deve sempre solicitar o PAT antes de executar qualquer operação de escrita no GitHub
- Logs de operações devem ser registrados em `PROGRESS.md` na workspace
- Em caso de falha de API (rate limit), aguardar 60s e tentar novamente uma vez
