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
C_GOLD='\033[38;5;178m'   # warning: >=70% of budget
C_RED='\033[38;5;203m'    # critical: >=95% of budget
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

# ---- Formatting helpers for the usage line ----
fmt_tok() {  # 10521657 -> 10.5M ; 59000 -> 59k
    local t=${1:-0}
    if   (( t >= 1000000 )); then printf "%d.%dM" $((t/1000000)) $(((t%1000000)/100000))
    elif (( t >= 1000 ));    then printf "%dk" $((t/1000))
    else                          printf "%d" "$t"
    fi
}
fmt_left() {  # seconds -> 2h13m / 13m
    local s=${1:-0}; (( s < 0 )) && s=0
    local m=$((s/60))
    if (( m >= 60 )); then printf "%dh%02dm" $((m/60)) $((m%60)); else printf "%dm" "$m"; fi
}

# ---- Usage limits (5h window + rolling 7-day), via ccusage, background-cached ----
# ccusage is slow (~4s cold), so we NEVER block on it. We read a cache file that a
# detached background job refreshes at most once per USAGE_TTL seconds.
USAGE_CACHE="$HOME/.claude/.usage-cache.json"
USAGE_LOCK="$HOME/.claude/.usage-refresh.lock"
USAGE_TTL=120        # min seconds between background refreshes
# 5h removed 2026-06-03: ccusage's cache-read-heavy raw tokens drift too fast
# against /usage's weighted metric to show a trustworthy 5h %. Weekly only.
CAP_WEEK=1945000000  # calibrated 2026-06-03 from /usage: 38.9M tok = 2% used (coarse; small %)

now_epoch=$(date +%s)

cache_mtime=0
[[ -f "$USAGE_CACHE" ]] && cache_mtime=$(stat -f %m "$USAGE_CACHE" 2>/dev/null || stat -c %Y "$USAGE_CACHE" 2>/dev/null || echo 0)

# Drop a stale lock left by a crashed refresh (>5 min old)
if [[ -d "$USAGE_LOCK" ]]; then
    lock_mtime=$(stat -f %m "$USAGE_LOCK" 2>/dev/null || stat -c %Y "$USAGE_LOCK" 2>/dev/null || echo 0)
    (( now_epoch - lock_mtime > 300 )) && rmdir "$USAGE_LOCK" 2>/dev/null
fi

# If cache is stale and no refresh is running, kick one off in the background.
# mkdir is atomic -> only one render wins the lock, so we never double-spawn ccusage.
if (( now_epoch - cache_mtime > USAGE_TTL )) && mkdir "$USAGE_LOCK" 2>/dev/null; then
    (
        npx ccusage@latest blocks --json 2>/dev/null | jq '
            def epoch: sub("\\.[0-9]+Z$";"Z") | fromdateiso8601;
            (([.blocks[] | select(.isActive)])[0]) as $a |
            {
              reset_epoch:  ($a.endTime // "" | if . == "" then 0 else epoch end),
              fiveh_tokens: ($a.totalTokens // 0),
              week_tokens:  ([.blocks[] | select(.isGap|not)
                              | select((.startTime|epoch) > (now - 604800))
                              | .totalTokens] | add // 0)
            }
        ' > "$USAGE_CACHE.tmp" 2>/dev/null && mv "$USAGE_CACHE.tmp" "$USAGE_CACHE"
        rmdir "$USAGE_LOCK" 2>/dev/null
    ) >/dev/null 2>&1 &
fi

# Extract model, directory, and cwd
model=$(echo "$input" | jq -r '.model.display_name // .model.id // "?"')
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

    # Readout color escalates as you approach the clear point
    if   [[ $pct -ge 95 ]]; then C_GAUGE="$C_RED"
    elif [[ $pct -ge 70 ]]; then C_GAUGE="$C_GOLD"
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

# ---- Usage segment: rolling 7-day weekly limit (appended to row 1) ----
# 5h dropped: its raw-token/weighted-% drift made the number untrustworthy.
if [[ -f "$USAGE_CACHE" ]]; then
    week_tokens=$(jq -r '.week_tokens // 0' "$USAGE_CACHE" 2>/dev/null)
    week_tokens=${week_tokens%.*}; week_tokens=${week_tokens:-0}

    week_pct=""
    if (( CAP_WEEK > 0 )); then
        p=$(( week_tokens * 100 / CAP_WEEK )); (( p > 100 )) && p=100
        c="$C_ACCENT"; (( p >= 70 )) && c="$C_GOLD"; (( p >= 90 )) && c="$C_RED"
        week_pct=" ${c}(${p}%)${C_GRAY}"
    fi

    usage_seg="${C_GRAY}⏱ 7d $(fmt_tok $week_tokens)${week_pct}"
else
    usage_seg="${C_GRAY}⏱ 7d —  ${C_BAR_EMPTY}(loading…)"
fi

# Build output — row 1: Model | Dir | Context | Usage
# The branch segment moves to its own row (below) so a long branch/filename
# never pushes the context gauge and usage off to the right.
output="${C_ACCENT}${model}${C_GRAY} | 📁${dir} | ${ctx}${C_GRAY} | ${usage_seg}${C_RESET}"

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
