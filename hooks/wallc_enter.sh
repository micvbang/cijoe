#!/usr/bin/env bash
#
# Logs elapsed time to file $CIJ_TEST_AUX_ROOT/wallc_perf.json
#
# on-enter: log begin timestamp
# on-exit: compute elapsed time, dump as json
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::wallc_enter() {
  if [[ ! -d "$CIJ_TEST_AUX_ROOT" ]]; then
    cij::err "hook::wallc_enter: FAILED: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    return 1
  fi

  ssh::cmd "python -c \"import time; print(time.time())\"" > "$CIJ_TEST_AUX_ROOT/wallc_perf_enter.res"

  return 0
}

hook::wallc_enter
exit $?
