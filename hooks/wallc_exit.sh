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
test::require python
test::enter

hook::wallc_exit() {
  END=$(ssh::cmd "python -c \"import time; print(time.time())\"" | tail -n1)
  BEGIN=$(tail -n1 < "$CIJ_TEST_AUX_ROOT/wallc_perf_enter.res")

  ELAPSED=$(python -c "print(float($END) - float($BEGIN))")
  echo "{\"wallc\": $ELAPSED}" > "$CIJ_TEST_AUX_ROOT/wallc_perf.json"

  return 0
}

hook::wallc_exit
exit $?
