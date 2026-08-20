#!/bin/bash

# Color theme: gray, orange, blue, teal, green, lavender, rose, gold, slate, cyan
# Preview colors with: bash scripts/color-preview.sh
COLOR="blue"

# Manual "clear the chat" budget. The gauge fills toward THIS, not the real
# model window (1M on Opus 4.8). Set it to the token count you want to clear at.
CLEAR_BUDGET=200000

# Echo your last message on a second row. 0 = single-row status line.
SHOW_LAST_MSG=0

# Color codes
C_RESET='\033[0m'
C_GRAY='\033[38;5;245m'  # explicit gray for default text
C_BAR_EMPTY='\033[38;5;238m'
# Context-gauge zone colors. These mirror the canonical zone table in
# 52_context-management.md § "The 70% Rule" — that table is the single source of
# truth; change it there first, then follow here. The Green zone (0-50%) uses
# C_ACCENT so the gauge still honors the COLOR theme; escalation bands are fixed.
C_GOLD='\033[38;5;178m'      # Yellow   50-70%: start thinking about compacting
C_ORANGE='\033[38;5;208m'    # Orange   70-85%: don't read more files; prepare to compact
C_RED='\033[38;5;203m'       # Red      85-95%: stop new work, compact now
C_CRIT='\033[1;38;5;196m'    # Critical   95%+: /clear immediately (write a handoff first)

# Per-model name colors (by capability tier)
C_MODEL_FABLE='\033[38;5;203m'   # red    — Fable (most capable)
C_MODEL_OPUS='\033[38;5;208m'    # orange — Opus
C_MODEL_SONNET='\033[38;5;71m'   # green  — Sonnet
C_MODEL_HAIKU='\033[38;5;255m'   # white  — Haiku
case "$COLOR" in
    orange)   C_ACCENT='\033[38;5;173m' ;;
    blue)     C_ACCENT='\033[38;5;74m' ;;
    teal)     C_ACCENT='\033[38;5;66m' ;;
    green)    C_ACCENT='\033[38;5;71m' ;;
    lavender) C_ACCENT='\033[38;5;139m' ;;
    rose)     C_ACCENT='\033[38;5;132m' ;;
    gold)     C_ACCENT='\033[38;5;136m' ;;
    slate)    C_ACCENT='\033[38;5;60m' ;;
    cyan)     C_ACCENT='\033[38;5;37m' ;;
    *)        C_ACCENT="$C_GRAY" ;;  # gray: all same color
esac

input=$(cat)

# Extract model, directory, and cwd
model=$(echo "$input" | jq -r '.model.display_name // .model.id // "?"')

# Pick a color for the model name by capability tier (case-insensitive match).
# Falls back to the theme accent for anything unrecognized.
# cur_tier (4=Fable 3=Opus 2=Sonnet 1=Haiku) feeds the model-advisor hint below.
shopt -s nocasematch
case "$model" in
    *fable*)  C_MODEL="$C_MODEL_FABLE";  cur_tier=4 ;;
    *opus*)   C_MODEL="$C_MODEL_OPUS";   cur_tier=3 ;;
    *sonnet*) C_MODEL="$C_MODEL_SONNET"; cur_tier=2 ;;
    *haiku*)  C_MODEL="$C_MODEL_HAIKU";  cur_tier=1 ;;
    *)        C_MODEL="$C_ACCENT";       cur_tier=0 ;;
esac
shopt -u nocasematch

# --- Model-advisor handshake (paired with hooks/model-advisor.sh) ---
# Write the live model so the hook can read it, and read back any pending
# model-switch suggestion to render a persistent " ⮕ sonnet?" hint.
session_id=$(echo "$input" | jq -r '.session_id // empty')
model_hint=""
if [[ -n "$session_id" ]]; then
    printf '%s' "$model" > "$HOME/.claude/.current-model-$session_id" 2>/dev/null
    sugg_file="$HOME/.claude/.model-suggestion-$session_id"
    if [[ -f "$sugg_file" ]]; then
        sugg_label=$(cut -d'|' -f1 "$sugg_file" 2>/dev/null)
        case "$sugg_label" in
            fable)  sugg_tier=4 ;;
            opus)   sugg_tier=3 ;;
            sonnet) sugg_tier=2 ;;
            haiku)  sugg_tier=1 ;;
            *)      sugg_tier=0 ;;
        esac
        # Only show the hint while the mismatch still stands.
        if (( sugg_tier > 0 && sugg_tier != cur_tier )); then
            # LOUD alarm: bold white on a filled bright-red bar (bg 256-color 196)
            # + CAPS + imperative, so a wrong-tier session can't be skimmed past.
            # A filled block reads as "alarm" far more than colored text alone, and
            # background fills are supported everywhere (unlike ANSI blink). Inner
            # padding spaces give the bar margins; 1;97 = bold white, 48;5;196 = red bg.
            sugg_upper=$(printf '%s' "$sugg_label" | tr '[:lower:]' '[:upper:]')
            model_hint=" \033[1;97;48;5;196m ⮕ /MODEL ${sugg_upper} \033[0m"
        else
            rm -f "$sugg_file" 2>/dev/null   # resolved — clear it
        fi
    fi
fi

cwd=$(echo "$input" | jq -r '.cwd // empty')
dir=$(basename "$cwd" 2>/dev/null || echo "?")

# Get git branch, uncommitted file count, and sync status
branch=""
git_status=""
if [[ -n "$cwd" && -d "$cwd" ]]; then
    branch=$(git -C "$cwd" branch --show-current 2>/dev/null)
    if [[ -n "$branch" ]]; then
        # Count uncommitted files
        file_count=$(git -C "$cwd" --no-optional-locks status --porcelain -uall 2>/dev/null | wc -l | tr -d ' ')

        # Check sync status with upstream
        sync_status=""
        upstream=$(git -C "$cwd" rev-parse --abbrev-ref @{upstream} 2>/dev/null)
        if [[ -n "$upstream" ]]; then
            # Get last fetch time
            fetch_head="$cwd/.git/FETCH_HEAD"
            fetch_ago=""
            if [[ -f "$fetch_head" ]]; then
                fetch_time=$(stat -f %m "$fetch_head" 2>/dev/null || stat -c %Y "$fetch_head" 2>/dev/null)
                if [[ -n "$fetch_time" ]]; then
                    now=$(date +%s)
                    diff=$((now - fetch_time))
                    if [[ $diff -lt 60 ]]; then
                        fetch_ago="<1m ago"
                    elif [[ $diff -lt 3600 ]]; then
                        fetch_ago="$((diff / 60))m ago"
                    elif [[ $diff -lt 86400 ]]; then
                        fetch_ago="$((diff / 3600))h ago"
                    else
                        fetch_ago="$((diff / 86400))d ago"
                    fi
                fi
            fi

            counts=$(git -C "$cwd" rev-list --left-right --count HEAD...@{upstream} 2>/dev/null)
            ahead=$(echo "$counts" | cut -f1)
            behind=$(echo "$counts" | cut -f2)
            if [[ "$ahead" -eq 0 && "$behind" -eq 0 ]]; then
                if [[ -n "$fetch_ago" ]]; then
                    sync_status="synced ${fetch_ago}"
                else
                    sync_status="synced"
                fi
            elif [[ "$ahead" -gt 0 && "$behind" -eq 0 ]]; then
                sync_status="${ahead} ahead"
            elif [[ "$ahead" -eq 0 && "$behind" -gt 0 ]]; then
                sync_status="${behind} behind"
            else
                sync_status="${ahead} ahead, ${behind} behind"
            fi
        else
            sync_status="no upstream"
        fi

        # Build git status string
        if [[ "$file_count" -eq 0 ]]; then
            git_status="(0 files uncommitted, ${sync_status})"
        elif [[ "$file_count" -eq 1 ]]; then
            # Show the actual filename when only one file is uncommitted
            single_file=$(git -C "$cwd" --no-optional-locks status --porcelain -uall 2>/dev/null | head -1 | sed 's/^...//')
            git_status="(${single_file} uncommitted, ${sync_status})"
        else
            git_status="(${file_count} files uncommitted, ${sync_status})"
        fi
    fi
fi

# Get transcript path for context calculation and last message feature
transcript_path=$(echo "$input" | jq -r '.transcript_path // empty')

# Budget the gauge fills toward = your manual clear point (not the real window).
budget_k=$((CLEAR_BUDGET / 1000))

# Calculate context bar from transcript
if [[ -n "$transcript_path" && -f "$transcript_path" ]]; then
    context_length=$(jq -s '
        map(select(.message.usage and .isSidechain != true and .isApiErrorMessage != true)) |
        last |
        if . then
            (.message.usage.input_tokens // 0) +
            (.message.usage.cache_read_input_tokens // 0) +
            (.message.usage.cache_creation_input_tokens // 0)
        else 0 end
    ' < "$transcript_path")

    # 20k baseline: includes system prompt (~3k), tools (~15k), memory (~300),
    # plus ~2k for git status, env block, XML framing, and other dynamic context
    baseline=20000
    bar_width=20

    # Use the baseline at conversation start before any usage is recorded
    [[ "$context_length" -gt 0 ]] || context_length=$baseline

    # Absolute count (rounded to nearest k) and percent of the clear budget
    count_k=$(( (context_length + 500) / 1000 ))
    pct=$((context_length * 100 / CLEAR_BUDGET))
    [[ $pct -gt 100 ]] && pct=100

    # Readout color escalates through the 52_context-management.md zones:
    # Green 0-50 / Yellow 50-70 / Orange 70-85 / Red 85-95 / Critical 95+.
    if   [[ $pct -ge 95 ]]; then C_GAUGE="$C_CRIT"
    elif [[ $pct -ge 85 ]]; then C_GAUGE="$C_RED"
    elif [[ $pct -ge 70 ]]; then C_GAUGE="$C_ORANGE"
    elif [[ $pct -ge 50 ]]; then C_GAUGE="$C_GOLD"
    else                         C_GAUGE="$C_ACCENT"
    fi

    # Thresholds scale with cell size so the bar works at any width
    cell=$((100 / bar_width))                 # percent each cell represents
    full_thresh=$(( cell * 8 / 10 )); [[ $full_thresh -lt 1 ]] && full_thresh=1
    half_thresh=$(( cell * 3 / 10 )); [[ $half_thresh -lt 1 ]] && half_thresh=1

    bar=""
    for ((i=0; i<bar_width; i++)); do
        bar_start=$((i * cell))
        progress=$((pct - bar_start))
        if [[ $progress -ge $full_thresh ]]; then
            bar+="${C_GAUGE}█${C_RESET}"
        elif [[ $progress -ge $half_thresh ]]; then
            bar+="${C_GAUGE}▄${C_RESET}"
        else
            bar+="${C_BAR_EMPTY}░${C_RESET}"
        fi
    done

    ctx="${bar} ${C_GAUGE}${count_k}k / ${budget_k}k ${C_GRAY}(${pct}%)"
else
    count_k=20
    pct=10
    empty_bar="${C_ACCENT}██${C_BAR_EMPTY}"
    for ((i=0; i<18; i++)); do empty_bar+="░"; done
    ctx="${empty_bar} ${C_ACCENT}~${count_k}k / ${budget_k}k ${C_GRAY}(~${pct}%)"
fi

# Build output — row 1: Model | Dir | Context
# The branch segment moves to its own row (below) so a long branch/filename
# never pushes the context gauge off to the right.
output="${C_MODEL}${model}${model_hint}${C_GRAY} | 📁${dir} | ${ctx}${C_RESET}"

printf '%b\n' "$output"

# Row 2: git branch + status (only when inside a repo)
[[ -n "$branch" ]] && printf '%b\n' "${C_ACCENT}🔀${branch}${C_GRAY} ${git_status}${C_RESET}"

# Get user's last message (text only, not tool results, skip unhelpful messages)
if (( SHOW_LAST_MSG )) && [[ -n "$transcript_path" && -f "$transcript_path" ]]; then
    # Calculate visible length (without ANSI codes) - 10 chars for bar + content
    # Branch now lives on its own row, so it's excluded from row 1's width.
    plain_output="${model} | 📁${dir}"
    plain_output+=" | xxxxxxxxxxxxxxxxxxxx ${count_k}k / ${budget_k}k (${pct}%)"
    max_len=${#plain_output}
    last_user_msg=$(jq -rs '
        # Messages to skip (not useful as context)
        def is_unhelpful:
            startswith("[Request interrupted") or
            startswith("[Request cancelled") or
            . == "";

        [.[] | select(.type == "user") |
         select(.message.content | type == "string" or
                (type == "array" and any(.[]; .type == "text")))] |
        reverse |
        map(.message.content |
            if type == "string" then .
            else [.[] | select(.type == "text") | .text] | join(" ") end |
            gsub("\n"; " ") | gsub("  +"; " ")) |
        map(select(is_unhelpful | not)) |
        first // ""
    ' < "$transcript_path" 2>/dev/null)

    if [[ -n "$last_user_msg" ]]; then
        if [[ ${#last_user_msg} -gt $max_len ]]; then
            echo "💬 ${last_user_msg:0:$((max_len - 3))}..."
        else
            echo "💬 ${last_user_msg}"
        fi
    fi
fi
