# 🗂️ Skill: `skill-repo-manager`

> **Skywork/Hermes AI Skill** — Gerencia o ciclo de vida completo dos repositórios GitHub de todas as skills do agente Hermes.

## 📋 Descrição

Sincroniza, audita e organiza os 18 repositórios de skills do agente Hermes no GitHub.
Detecta atualizações, aplica topics/descrições, cria novos repos e mantém o hub central atualizado.

## 📁 Estrutura

```
skill-repo-manager/
├── SKILL.md                          ← instruções completas para o Hermes
├── README.md                         ← este arquivo
├── references/
│   └── hermes-compatibility.md       ← guia de compatibilidade e status das skills
└── scripts/
    ├── sync_all_skills.py            ← sincronização Skywork → GitHub
    ├── audit_hermes.py               ← auditoria e correção de compatibilidade
    └── check_updates.sh              ← detecção de mudanças (SHA diff)
```

## 🚀 Comandos rápidos

```bash
# Verificar quais skills estão desatualizadas
bash scripts/check_updates.sh $GITHUB_TOKEN

# Sincronizar todas as skills
python3 scripts/sync_all_skills.py --token $GITHUB_TOKEN

# Sincronizar uma skill específica
python3 scripts/sync_all_skills.py --token $GITHUB_TOKEN --skill web-design-engineer

# Auditar compatibilidade com Hermes
python3 scripts/audit_hermes.py --all

# Auditar e corrigir automaticamente
python3 scripts/audit_hermes.py --all --fix
```

## 🔗 Hub Central

Todos os 18 repos estão organizados como submodules em:
[skywork-skills-hub](https://github.com/Victor-F-M-A-R/skywork-skills-hub)
