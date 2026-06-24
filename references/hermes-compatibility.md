# Guia de Compatibilidade: Skills → Agente Hermes

## Diferenças entre Claude/ClawdBot e Hermes

### Nomes de ferramentas

| Claude/ClawdBot (antigo) | Hermes (correto) | Observação |
|--------------------------|-----------------|------------|
| `Read` | `read` | Minúsculo |
| `Write` | `write` | Minúsculo |
| `Bash` | `bash` | Minúsculo |
| `Glob` | `glob` | Minúsculo |
| `Grep` | `grep` | Minúsculo |
| `WebSearch` | `web_search` | Snake_case |
| `TodoWrite` | `todowrite` | Concatenado |
| `Skill` | `load_skill` | Nome completo |
| `AskUserQuestion` | _(chat direto)_ | Hermes pergunta via chat |

### Variáveis de ambiente

| Claude | Hermes |
|--------|--------|
| `${CLAUDE_SKILL_DIR}` | `${HERMES_SKILL_DIR}` |
| `${CLAUDE_PLUGIN_ROOT}` | `${HERMES_PLUGIN_ROOT}` |

### Metadados de frontmatter

```yaml
# ANTES (clawdbot)
metadata: {"clawdbot":{"emoji":"✨","requires":{"bins":[]}}}

# DEPOIS (hermes)
metadata: {"hermes":{"emoji":"✨","requires":{"bins":[]}}}
```

### Idioma padrão

- Placeholder `{{ product_language }}` → substituir por `Português (Brasil)`
- Instruções internas podem ser em inglês
- Respostas ao usuário Victor sempre em Português (Brasil)

## Skills e seus status de compatibilidade

| Skill | Problemas encontrados | Ação necessária |
|-------|-----------------------|-----------------|
| `animations` | metadata clawdbot | substituir clawdbot→hermes |
| `architecture-designer` | nenhum crítico | ✅ compatível |
| `artifacts-builder` | nenhum crítico | ✅ compatível |
| `content_marketing` | metadata clawdbot | substituir clawdbot→hermes |
| `create-prd` | nenhum crítico | ✅ compatível |
| `ds` | tools capitalizados (Bash, Read...), hooks com ${CLAUDE_PLUGIN_ROOT} | substituir tools + vars |
| `extract-design` | tools capitalizados (Bash, Read, Write, Glob) | substituir tools |
| `frontend-design` | nenhum crítico | ✅ compatível |
| `marketing-psychology` | nenhum crítico | ✅ compatível |
| `short-drama-writer` | metadata clawdbot | substituir clawdbot→hermes |
| `stock-market-industry-analyst-and-predictor` | nenhum crítico | ✅ compatível |
| `template-based-apa-professional-paper` | {{ product_language }} não resolvido | substituir placeholder |
| `template-based-business-analysis-report` | {{ product_language }} não resolvido | substituir placeholder |
| `template-based-competitive-analysis` | {{ product_language }} não resolvido | substituir placeholder |
| `template-based-general-service-agreement` | {{ product_language }} não resolvido | substituir placeholder |
| `web-design-engineer` | nenhum crítico | ✅ compatível |
| `youtube-watcher` | metadata clawdbot, {baseDir} placeholder | substituir clawdbot + baseDir |
| `skill-repo-manager` | ✅ nativa Hermes | nenhuma |

## Regra de compatibilidade mínima

Uma skill é considerada **compatível com Hermes** quando:
1. Tem `name:` no frontmatter
2. Não tem referencias a ferramentas com capitalização errada
3. Não tem `{{ product_language }}` não resolvido
4. Não tem `${CLAUDE_*}` nas instruções
5. Metadata usa `hermes` em vez de `clawdbot`
