#!/usr/bin/env bash
# Disposable demonstrations, not a product test runner. No app control or process signals.
set -euo pipefail
scratch=$(mktemp -d "${TMPDIR:-/tmp}/directions-test-safety.XXXXXX")
trap 'rm -rf "$scratch"' EXIT

producer() { printf 'producer progress\n'; return 7; }
formatter() { cat; return 0; }
set +e
producer 2>&1 | tee "$scratch/raw.log" | formatter > "$scratch/formatted.log"
codes=("${PIPESTATUS[@]}")
set -e
[[ ${codes[0]} -eq 7 && ${codes[1]} -eq 0 && ${codes[2]} -eq 0 ]]
cmp "$scratch/raw.log" "$scratch/formatted.log"
printf '{"producer_exit":%s,"tee_exit":%s,"formatter_exit":%s,"passed":false}\n' \
  "${codes[0]}" "${codes[1]}" "${codes[2]}" > "$scratch/result.json"
printf 'PASS: producer exit 7 survives successful formatter; raw log retained during evaluation\n'

# Recorded process inventory: a decoy has the same command text, and a PID can be reused.
# The fixture matches an explicit spawn receipt (PID + start token + executable), never a name.
cat > "$scratch/processes.tsv" <<'EOF'
2001 start-a /fixture/test-child
2002 start-b /fixture/test-child
2003 start-c /fixture/wrapper
EOF
identify() {
  awk -v pid="$1" -v started="$2" -v executable="$3" \
    '$1 == pid && $2 == started && $3 == executable { print $1 }' "$scratch/processes.tsv"
}
[[ $(identify 2001 start-a /fixture/test-child) == 2001 ]]
[[ -z $(identify 2003 start-a /fixture/test-child) ]]
[[ -z $(identify 2001 stale-start /fixture/test-child) ]]
[[ -z $(identify 2002 start-a /fixture/test-child) ]]
printf 'PASS: exact receipt selects owned child; unrelated wrapper, same-name decoy and reused PID rejected\n'

# Also collect a real, directly spawned disposable shell child, without querying/signalling apps.
bash -c 'printf "child completed\n"; exit 7' > "$scratch/child.log" &
child_pid=$!
set +e
wait "$child_pid"
child_status=$?
set -e
[[ $child_status -eq 7 ]]
[[ $(cat "$scratch/child.log") == 'child completed' ]]
printf 'PASS: wait on directly owned child returns actual exit 7\n'
