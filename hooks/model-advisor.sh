#!/bin/bash
# UserPromptSubmit hook — nudges you toward the cost-appropriate model.
#
# It reads your prompt, infers the kind of work (planning vs execution vs
# trivial), and compares that to the model you're currently on. When there's a
# clear mismatch it prints ONE line via systemMessage and records the suggestion
# to a per-session state file that the statusline reads (persistent hint).
#
# It never blocks the prompt and never re-nags: if you ignore a suggestion, it
# stays silent until the suggestion *changes* or you switch models.
#
# Tier ranking (cost):  fable(4) > opus(3) > sonnet(2) > haiku(1)
#   Fable 5    $10/$50   hardest planning / deepest debugging
#   Opus 4.8   $5/$25    planning, architecture, debugging, review, agentic
#   Sonnet 4.6 $3/$15    executing a clear plan, bulk implementation
#   Haiku 4.5  $1/$5     trivial mechanical edits, lookups
#
# Tune the keyword lists below to taste.

input=$(cat)

prompt=$(printf '%s' "$input" | jq -r '.prompt // ""' 2>/dev/null)
session_id=$(printf '%s' "$input" | jq -r '.session_id // "default"' 2>/dev/null)
# Current model: prefer the hook payload, fall back to the file the statusline writes.
model=$(printf '%s' "$input" | jq -r '.model.id // .model.display_name // ""' 2>/dev/null)
state_dir="$HOME/.claude"
model_file="$state_dir/.current-model-$session_id"
sugg_file="$state_dir/.model-suggestion-$session_id"
[[ -z "$model" && -f "$model_file" ]] && model=$(cat "$model_file" 2>/dev/null)

# Nothing to compare against → stay quiet.
[[ -z "$prompt" || -z "$model" ]] && exit 0

# --- map a model string to a tier number ---
tier_of() {
    local m="$1"
    shopt -s nocasematch
    local t=0
    case "$m" in
        *fable*)  t=4 ;;
        *opus*)   t=3 ;;
        *sonnet*) t=2 ;;
        *haiku*)  t=1 ;;
    esac
    shopt -u nocasematch
    echo "$t"
}

p=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

# --- keyword → suggested tier (edit these) ---
# Execution verbs checked first: "implement the plan" is execution, not planning.
EXEC_RE='implement|apply the|write the|add (a|the) |create the|build the|scaffold|wire up|hook up|rename|refactor|port |translate|convert|integrate|migrate the'
PLAN_RE='plan|architect|design the|debug|root cause|investigate|diagnose|why (is|does|are|did)|figure out|trace through|strateg|think through|reason about|review the|audit'
TRIVIAL_RE='^(list|show me|format|lint|bump|fix the typo|update the version)'
HARD_RE='complex|hardest|very tricky|intricate|deeply|subtle|gnarly|thorn'

suggest_tier=0
suggest_label=""
if   printf '%s' "$p" | grep -Eq "$TRIVIAL_RE"; then suggest_tier=1; suggest_label="haiku"
elif printf '%s' "$p" | grep -Eq "$EXEC_RE";    then suggest_tier=2; suggest_label="sonnet"
elif printf '%s' "$p" | grep -Eq "$PLAN_RE"; then
    if printf '%s' "$p" | grep -Eq "$HARD_RE"; then suggest_tier=4; suggest_label="fable"
    else suggest_tier=3; suggest_label="opus"; fi
fi

# No clear intent → clear any stale suggestion and stay quiet.
if (( suggest_tier == 0 )); then
    rm -f "$sugg_file" 2>/dev/null
    exit 0
fi

cur_tier=$(tier_of "$model")

# Friendly current-model name for the message (avoid raw ids like claude-opus-4-8[1m]).
case "$cur_tier" in
    4) cur_label="Fable" ;;
    3) cur_label="Opus" ;;
    2) cur_label="Sonnet" ;;
    1) cur_label="Haiku" ;;
    *) cur_label="$model" ;;
esac

# Already on the right tier → clear suggestion, stay quiet.
if (( cur_tier == suggest_tier )); then
    rm -f "$sugg_file" 2>/dev/null
    exit 0
fi

# Debounce: if we already emitted this exact suggestion for this model, don't re-nag.
# (The statusline keeps showing the persistent hint regardless.)
last=""
[[ -f "$sugg_file" ]] && last=$(cat "$sugg_file" 2>/dev/null)
token="${suggest_label}|${model}"
printf '%s' "$token" > "$sugg_file" 2>/dev/null
[[ "$last" == "$token" ]] && exit 0

# Phrase the nudge by direction — loud, imperative, CAPS.
# NOTE: macOS ships bash 3.2 — no ${var^^} expansion. Uppercase via tr.
sugg_upper=$(printf '%s' "$suggest_label" | tr '[:lower:]' '[:upper:]')
cur_upper=$(printf '%s' "$cur_label" | tr '[:lower:]' '[:upper:]')
if (( suggest_tier < cur_tier )); then
    verb="THIS IS ${sugg_upper}-TIER WORK — SWITCH DOWN TO SAVE COST: /model ${suggest_label}"
else
    verb="THIS LOOKS DEMANDING — SWITCH UP FOR MORE CAPABILITY: /model ${suggest_label}"
fi

# systemMessage is shown to the user (not injected into my context). This channel
# renders plain text — ANSI color would leak as literal escape codes, so loudness
# comes from CAPS + 🔴 emoji. True red lives in the statusline (a terminal line).
jq -cn --arg msg "🔴 MODEL CHECK — YOU'RE ON ${cur_upper}. ${verb} 🔴" '{systemMessage: $msg}'
exit 0
