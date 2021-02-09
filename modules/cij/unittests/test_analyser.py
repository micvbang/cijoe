import unittest
from collections import namedtuple

from cij.analyser import Range, InvalidRangeError

RequirementTest = namedtuple("RequirementTest", ["rng", "n", "expected"])


class TestRequirement(unittest.TestCase):
    def test_requirement_valid_ranges_no_unit(self):
        """
        Validates that valid ranges without units are accepted, and that they
        are computed correctly.
        """

        tests = [
            # half open range with negative infinity
            RequirementTest(rng="]-inf;5]", n=-9999999999999999, expected=True),
            RequirementTest(rng="]-inf;5]", n=0, expected=True),
            RequirementTest(rng="]-inf;5]", n=5, expected=True),
            RequirementTest(rng="]-inf;5]", n=10, expected=False),
            RequirementTest(rng="]-inf;5]", n=5.0001, expected=False),

            # half open range with positive infinity
            RequirementTest(rng="[-10;inf[", n=9999999999999999, expected=True),
            RequirementTest(rng="[-10;inf[", n=0, expected=True),
            RequirementTest(rng="[-10;inf[", n=-10, expected=True),
            RequirementTest(rng="[-10;inf[", n=-100, expected=False),
            RequirementTest(rng="[-10;inf[", n=-99999999999999, expected=False),

            # closed range with absolute values
            RequirementTest(rng="[-10;10]", n=-10, expected=True),
            RequirementTest(rng="[-10;10]", n=0, expected=True),
            RequirementTest(rng="[-10;10]", n=10, expected=True),
            RequirementTest(rng="[-10;10]", n=-10.1, expected=False),
            RequirementTest(rng="[-10;10]", n=10.1, expected=False),

            # open range with absolute values
            RequirementTest(rng="]-10;10[", n=-9.99999999999999, expected=True),
            RequirementTest(rng="]-10;10[", n=9.999999999999999, expected=True),
            RequirementTest(rng="]-10;10[", n=5, expected=True),
            RequirementTest(rng="]-10;10[", n=-10, expected=False),
            RequirementTest(rng="]-10;10[", n=10, expected=False),

            # closed range, exact equality
            RequirementTest(rng="[10;10]", n=10, expected=True),
            RequirementTest(rng="[10;10]", n=10.00000000000001, expected=False),
            RequirementTest(rng="[10;10]", n=9.999999999999999, expected=False),

            # open range, no matches possible
            RequirementTest(rng="]10;10[", n=10, expected=False),

            # ranges with decimals
            RequirementTest(rng="[10.0;10.1]", n=10.05, expected=True),
            RequirementTest(rng="[10.;11.]", n=10, expected=True),
            RequirementTest(rng="[10.0;10.1[", n=10.05, expected=True),
            RequirementTest(rng="]10.0;10.1[", n=10.05, expected=True),
            RequirementTest(rng="]10.0;10.1[", n=10.1, expected=False),
            RequirementTest(rng="]10.0;10.1[", n=10.0, expected=False),

            # ranges with whitespace
            RequirementTest(rng="[1; 10]", n=5, expected=True),
            RequirementTest(rng="[1 ;10]", n=5, expected=True),
            RequirementTest(rng="[1 ; 10]", n=5, expected=True),
            RequirementTest(rng="[ 1 ; 10 ]", n=5, expected=True),
            RequirementTest(rng="[   1     ;     10   ]", n=5, expected=True),
        ]

        for test in tests:
            rng = Range(test.rng)
            self.assertEqual(
                test.expected,
                rng.contains(test.n),
                f"Expected {test.expected} for {test.n} in '{test.rng}'"
            )

    def test_requirement_invalid_ranges(self):
        """
        Validates that invalid range declarations raise exceptions.
        """

        tests = [
            # non-increasing range requirements
            RequirementTest(rng="]10;5]", n=0, expected=InvalidRangeError),
            RequirementTest(rng="]inf;5]", n=0, expected=InvalidRangeError),
            RequirementTest(rng="]1;-inf]", n=0, expected=InvalidRangeError),
            RequirementTest(rng="]-5;-10]", n=0, expected=InvalidRangeError),

            # invalid range syntax
            RequirementTest(rng="[1,10]", n=5, expected=InvalidRangeError),
            RequirementTest(rng="[1:10]", n=5, expected=InvalidRangeError),
            RequirementTest(rng="[a;10]", n=5, expected=InvalidRangeError),
            RequirementTest(rng="[1;b]", n=5, expected=InvalidRangeError),
            RequirementTest(rng="(1;10]", n=5, expected=InvalidRangeError),
            RequirementTest(rng="[1;10)", n=5, expected=InvalidRangeError),
            RequirementTest(rng="[;10]", n=5, expected=InvalidRangeError),
            RequirementTest(rng="[1;]", n=5, expected=InvalidRangeError),
            RequirementTest(rng="abc", n=5, expected=InvalidRangeError),

            # invalid units
            RequirementTest(rng="[1;5]x", n=0, expected=InvalidRangeError),
            RequirementTest(rng="[1;5]invalid", n=0, expected=InvalidRangeError),
            RequirementTest(rng="[1;5]5", n=0, expected=InvalidRangeError),
            RequirementTest(rng="[1ms;5ms]", n=0, expected=InvalidRangeError),
            RequirementTest(rng="[1ms;5ms]ms", n=0, expected=InvalidRangeError),
        ]

        for test in tests:
            msg = f"Expected {test.rng} to be invalid"
            with self.assertRaises(test.expected, msg=msg):
                Range(test.rng)

    def test_requirement_valid_ranges_with_unit(self):
        """
        Validates that valid ranges units are accepted, and that they are
        computed correctly.
        """

        tests = [
            # general
            RequirementTest(rng="[1;1]", n=1, expected=True),
            RequirementTest(rng="[1;1]B", n=1, expected=True),
            RequirementTest(rng="[1;1]k", n=1000, expected=True),
            RequirementTest(rng="[1;1]M", n=1000**2, expected=True),
            RequirementTest(rng="[1;1]G", n=1000**3, expected=True),

            # kilo
            RequirementTest(rng="[1;1]kB", n=1000**1, expected=True),
            RequirementTest(rng="[1;1]MB", n=1000**2, expected=True),
            RequirementTest(rng="[1;1]GB", n=1000**3, expected=True),
            RequirementTest(rng="[1;1]TB", n=1000**4, expected=True),

            # kibi
            RequirementTest(rng="[1;1]KiB", n=1024**1, expected=True),
            RequirementTest(rng="[1;1]MiB", n=1024**2, expected=True),
            RequirementTest(rng="[1;1]GiB", n=1024**3, expected=True),
            RequirementTest(rng="[1;1]TiB", n=1024**4, expected=True),

            # time
            RequirementTest(rng="[1;1]nsec", n=1000**3, expected=True),
            RequirementTest(rng="[1;1]usec", n=1000**2, expected=True),
            RequirementTest(rng="[1;1]msec", n=1000**1, expected=True),
            RequirementTest(rng="[1;1]sec", n=1, expected=True),
            RequirementTest(rng="[1;1]min", n=1/60, expected=True),

            # ranges with whitespace
            RequirementTest(rng="[1; 1]KiB", n=1024**1, expected=True),
            RequirementTest(rng="[1;1] KiB", n=1024**1, expected=True),
            RequirementTest(rng="[1; 1] KiB", n=1024**1, expected=True),
            RequirementTest(rng="[1 ; 1]KiB", n=1024**1, expected=True),
            RequirementTest(rng="[ 1 ; 1 ] KiB", n=1024**1, expected=True),
            RequirementTest(rng="[  1  ;  1  ]  KiB", n=1024**1, expected=True),
        ]

        for test in tests:
            rng = Range(test.rng)
            self.assertEqual(
                test.expected,
                rng.contains(test.n),
                f"Expected {test.expected} for {test.n} in '{test.rng}'"
            )