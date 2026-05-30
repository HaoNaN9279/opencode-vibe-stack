# ---- OMO Config (oh-my-openagent.jsonc) ----
#
# Creates/updates the project-level oh-my-openagent.jsonc to register
# domain skill sources and agent definitions with OMO.

OMO_SCHEMA="https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json"

activate_omo_config() {
    local project_omo=".opencode/oh-my-openagent.jsonc"
    mkdir -p ".opencode"

    if [ ! -f "$project_omo" ]; then
        printf '{\n  "$schema": "%s",\n  "skills": {\n    "sources": [\n      {\n        "path": "skills",\n        "recursive": true\n      }\n    ]\n  },\n  "agent_definitions": [\n    "agents/"\n  ]\n}\n' \
            "$OMO_SCHEMA" > "$project_omo"
        ok "Created $project_omo with skills/agents sources"
    else
        info "oh-my-openagent.jsonc already exists -- skipping"
    fi
}

deactivate_omo_config() {
    local project_omo=".opencode/oh-my-openagent.jsonc"
    [ ! -f "$project_omo" ] && return 0

    local has_skills=false
    local has_agents=false
    if [ -d ".opencode/skills" ] && [ -n "$(ls -A ".opencode/skills" 2>/dev/null)" ]; then
        has_skills=true
    fi
    if [ -d ".opencode/agents" ] && [ -n "$(ls -A ".opencode/agents" 2>/dev/null)" ]; then
        has_agents=true
    fi

    if ! $has_skills && ! $has_agents; then
        rm -f "$project_omo"
        info "Removed $project_omo -- no active domains remain"
    fi
}
