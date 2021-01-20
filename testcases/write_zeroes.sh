#!/usr/bin/env bash
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::enter

if ! ssh::cmd "xnvme_tests_lblk write_zeroes /dev/nvme0n1"; then
  test::fail "failed executing 'xnvme_tests_lblk write_zeroes /dev/nvme0n1'"
fi

test::pass
