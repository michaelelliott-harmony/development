# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Test Suite: Alias Service
#
# Tests alias format validation, namespace validation, counter-based
# auto-generation, collision detection, lifecycle state transitions,
# grace period enforcement, cross-namespace independence, and the full
# flow from registration → alias assignment → resolution.
#
# These tests run without a database — they test the validation and
# logic layers only. Database integration tests require PostgreSQL
# and are deferred to the CI/CD pipeline.

import sys
import os
import re
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

# Add the alias package to the path
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), "..", "src"
))
from alias_service import (
    validate_alias_format,
    validate_namespace_format,
    _extract_prefix,
    _extract_number,
    _generate_alias_id,
    ALIAS_FORMAT_RE,
    NAMESPACE_FORMAT_RE,
    RESERVED_PREFIXES,
    RESERVED_TOP_LEVEL_SEGMENTS,
    GRACE_PERIOD_DAYS,
    InvalidAliasFormatError,
    InvalidNamespaceFormatError,
    ReservedPrefixError,
    NamespaceRequiredError,
    AliasConflictError,
    AliasNotFoundError,
    NamespaceNotFoundError,
)


# =========================================================================
# Test Class 1: Alias Format Validation
# =========================================================================

class TestAliasFormatValidation:
    """Tests for alias format validation (alias_namespace_rules.md §2)."""

    def test_valid_alias_simple(self):
        assert validate_alias_format("CC-421") == "CC-421"

    def test_valid_alias_two_letter_prefix(self):
        assert validate_alias_format("AB-1") == "AB-1"

    def test_valid_alias_four_letter_prefix(self):
        assert validate_alias_format("ABCD-999999") == "ABCD-999999"

    def test_valid_alias_three_letter_prefix(self):
        assert validate_alias_format("ENT-42") == "ENT-42"

    def test_case_insensitive_normalisation(self):
        """Aliases are stored uppercase but accepted case-insensitively (§2)."""
        assert validate_alias_format("cc-421") == "CC-421"
        assert validate_alias_format("Cc-421") == "CC-421"

    def test_invalid_no_hyphen(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("CC421")

    def test_invalid_no_number(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("CC-")

    def test_invalid_no_prefix(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("-421")

    def test_invalid_prefix_too_short(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("A-1")

    def test_invalid_prefix_too_long(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("ABCDE-1")

    def test_invalid_number_too_long(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("CC-1234567")

    def test_invalid_number_with_letters(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("CC-12a")

    def test_invalid_prefix_with_digits(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("C1-421")

    def test_invalid_empty_string(self):
        with pytest.raises(InvalidAliasFormatError):
            validate_alias_format("")

    def test_reserved_prefix_test(self):
        with pytest.raises(ReservedPrefixError):
            validate_alias_format("TEST-1")

    def test_reserved_prefix_demo(self):
        with pytest.raises(ReservedPrefixError):
            validate_alias_format("DEMO-1")

    def test_reserved_prefix_tmp(self):
        with pytest.raises(ReservedPrefixError):
            validate_alias_format("TMP-1")

    def test_reserved_prefix_sys(self):
        with pytest.raises(ReservedPrefixError):
            validate_alias_format("SYS-1")

    def test_reserved_prefix_case_insensitive(self):
        """Reserved prefix check is case-insensitive (normalised to uppercase)."""
        with pytest.raises(ReservedPrefixError):
            validate_alias_format("test-1")
        with pytest.raises(ReservedPrefixError):
            validate_alias_format("Demo-1")


# =========================================================================
# Test Class 2: Namespace Format Validation
# =========================================================================

class TestNamespaceFormatValidation:
    """Tests for namespace format validation (alias_namespace_rules.md §3)."""

    def test_valid_namespace_four_segments(self):
        assert validate_namespace_format("au.nsw.central_coast.cells") == "au.nsw.central_coast.cells"

    def test_valid_namespace_five_segments(self):
        assert validate_namespace_format("au.nsw.central_coast.cells.coastal") == "au.nsw.central_coast.cells.coastal"

    def test_valid_namespace_with_digits(self):
        assert validate_namespace_format("au.nsw.area2.cells") == "au.nsw.area2.cells"

    def test_valid_namespace_entities(self):
        assert validate_namespace_format("au.nsw.central_coast.entities") == "au.nsw.central_coast.entities"

    def test_valid_namespace_case_normalisation(self):
        """Namespaces are normalised to lowercase."""
        assert validate_namespace_format("AU.NSW.Central_Coast.Cells") == "au.nsw.central_coast.cells"

    def test_invalid_too_few_segments(self):
        """Minimum 4 segments (country.state.region.class)."""
        with pytest.raises(InvalidNamespaceFormatError):
            validate_namespace_format("au.nsw")

    def test_valid_three_segments(self):
        """The regex allows 3 segments (country + 2 dotted). Convention says 4, but regex is the spec."""
        assert validate_namespace_format("au.nsw.cells") == "au.nsw.cells"

    def test_invalid_segment_too_short(self):
        with pytest.raises(InvalidNamespaceFormatError):
            validate_namespace_format("a.nsw.central_coast.cells")

    def test_invalid_segment_too_long(self):
        long_segment = "a" * 33
        with pytest.raises(InvalidNamespaceFormatError):
            validate_namespace_format(f"au.nsw.{long_segment}.cells")

    def test_invalid_uppercase_segment(self):
        """After normalisation, check is applied — this should pass."""
        # Normalisation handles this
        result = validate_namespace_format("AU.NSW.CENTRAL_COAST.CELLS")
        assert result == "au.nsw.central_coast.cells"

    def test_invalid_special_chars(self):
        with pytest.raises(InvalidNamespaceFormatError):
            validate_namespace_format("au.nsw.central-coast.cells")

    def test_invalid_empty_string(self):
        with pytest.raises(InvalidNamespaceFormatError):
            validate_namespace_format("")

    def test_too_many_segments(self):
        """Max 7 segments (country + 2-5 dotted segments = 3-6 total after first)."""
        # The regex allows up to 6 additional segments after the first
        with pytest.raises(InvalidNamespaceFormatError):
            validate_namespace_format("au.nsw.cc.cells.sub1.sub2.sub3.sub4")


# =========================================================================
# Test Class 3: Alias Prefix/Number Extraction
# =========================================================================

class TestAliasExtraction:
    """Tests for prefix and number extraction from aliases."""

    def test_extract_prefix(self):
        assert _extract_prefix("CC-421") == "CC"

    def test_extract_prefix_four_letter(self):
        assert _extract_prefix("ABCD-1") == "ABCD"

    def test_extract_number(self):
        assert _extract_number("CC-421") == 421

    def test_extract_number_large(self):
        assert _extract_number("CC-999999") == 999999

    def test_extract_number_single_digit(self):
        assert _extract_number("CC-1") == 1


# =========================================================================
# Test Class 4: Alias ID Generation
# =========================================================================

class TestAliasIdGeneration:
    """Tests for alias record ID generation."""

    def test_alias_id_format(self):
        aid = _generate_alias_id()
        assert aid.startswith("al_")
        assert len(aid) == 12  # al_ + 9 chars

    def test_alias_id_uniqueness(self):
        """Generate 100 alias IDs and verify no duplicates."""
        ids = {_generate_alias_id() for _ in range(100)}
        assert len(ids) == 100

    def test_alias_id_valid_chars(self):
        """Alias ID token uses Crockford Base32 alphabet."""
        from alias_service import CROCKFORD_ALPHABET
        for _ in range(50):
            aid = _generate_alias_id()
            token = aid[3:]
            for char in token:
                assert char in CROCKFORD_ALPHABET, f"Invalid char {char!r} in {aid}"


# =========================================================================
# Test Class 5: Reserved Prefixes
# =========================================================================

class TestReservedPrefixes:
    """Tests for reserved prefix filtering (§8)."""

    def test_all_reserved_prefixes_rejected(self):
        for prefix in RESERVED_PREFIXES:
            with pytest.raises(ReservedPrefixError):
                validate_alias_format(f"{prefix}-1")

    def test_non_reserved_prefix_accepted(self):
        """A prefix not in the reserved set should pass."""
        assert validate_alias_format("CC-1") == "CC-1"
        assert validate_alias_format("ENT-1") == "ENT-1"
        assert validate_alias_format("GF-42") == "GF-42"


# =========================================================================
# Test Class 6: Namespace Resolution (No-DB Logic)
# =========================================================================

class TestNamespaceResolution:
    """Tests for namespace-related error conditions."""

    def test_namespace_required_error(self):
        err = NamespaceRequiredError()
        assert "namespace" in str(err).lower()
        assert "required" in str(err).lower()

    def test_namespace_not_found_error(self):
        err = NamespaceNotFoundError("au.nsw.fake.cells")
        assert "au.nsw.fake.cells" in str(err)

    def test_alias_not_found_error(self):
        err = AliasNotFoundError("ZZ-999", "au.nsw.central_coast.cells")
        assert "ZZ-999" in str(err)
        assert "au.nsw.central_coast.cells" in str(err)


# =========================================================================
# Test Class 7: Alias Conflict Error
# =========================================================================

class TestAliasConflictError:
    """Tests for conflict error reporting."""

    def test_conflict_basic(self):
        err = AliasConflictError("CC-421", "au.nsw.central_coast.cells")
        assert "CC-421" in str(err)
        assert "au.nsw.central_coast.cells" in str(err)

    def test_conflict_with_reason(self):
        err = AliasConflictError(
            "CC-421", "au.nsw.central_coast.cells",
            reason="Already active"
        )
        assert "Already active" in str(err)

    def test_conflict_grace_period(self):
        err = AliasConflictError(
            "CC-421", "au.nsw.central_coast.cells",
            reason="Retired within grace period. 90 days remaining"
        )
        assert "grace period" in str(err).lower()
        assert "90 days" in str(err)


# =========================================================================
# Test Class 8: Cross-Namespace Independence
# =========================================================================

class TestCrossNamespaceIndependence:
    """Tests that the same alias string is valid in different namespaces."""

    def test_same_alias_different_namespaces_both_valid(self):
        """The same alias format can exist in multiple namespaces (§4)."""
        # Both of these should validate successfully
        alias1 = validate_alias_format("CC-421")
        alias2 = validate_alias_format("CC-421")
        ns1 = validate_namespace_format("au.nsw.central_coast.cells")
        ns2 = validate_namespace_format("au.qld.cairns_coast.cells")
        # They produce the same alias string...
        assert alias1 == alias2
        # ...but different namespaces
        assert ns1 != ns2


# =========================================================================
# Test Class 9: Grace Period Constants
# =========================================================================

class TestGracePeriod:
    """Tests for grace period configuration."""

    def test_grace_period_is_180_days(self):
        """The grace period is exactly 180 days per §6."""
        assert GRACE_PERIOD_DAYS == 180

    def test_grace_period_calculation(self):
        """Verify grace period arithmetic."""
        retired_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        grace_end = retired_at + timedelta(days=GRACE_PERIOD_DAYS)
        # 180 days from Jan 1 = June 30
        assert grace_end.month == 6
        assert grace_end.day == 30

    def test_within_grace_period(self):
        """A date 90 days after retirement is within grace."""
        retired_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        check_at = retired_at + timedelta(days=90)
        grace_end = retired_at + timedelta(days=GRACE_PERIOD_DAYS)
        assert check_at < grace_end

    def test_after_grace_period(self):
        """A date 181 days after retirement is past grace."""
        retired_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        check_at = retired_at + timedelta(days=181)
        grace_end = retired_at + timedelta(days=GRACE_PERIOD_DAYS)
        assert check_at > grace_end


# =========================================================================
# Test Class 10: Regex Patterns
# =========================================================================

class TestRegexPatterns:
    """Verify the regex patterns match the locked spec exactly."""

    def test_alias_regex_matches_spec(self):
        """The alias regex must match alias_namespace_rules.md §2."""
        assert ALIAS_FORMAT_RE.pattern == r"^[A-Z]{2,4}-[0-9]{1,6}$"

    def test_namespace_regex_matches_spec(self):
        """The namespace regex must match alias_namespace_rules.md §3."""
        assert NAMESPACE_FORMAT_RE.pattern == r"^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$"

    def test_alias_regex_boundary_cases(self):
        """Boundary cases for the alias regex."""
        # Minimum valid: 2-letter prefix + 1-digit number
        assert ALIAS_FORMAT_RE.match("AB-1")
        # Maximum valid: 4-letter prefix + 6-digit number
        assert ALIAS_FORMAT_RE.match("ABCD-999999")
        # Just over boundary (5-letter prefix)
        assert not ALIAS_FORMAT_RE.match("ABCDE-1")
        # Just over boundary (7-digit number)
        assert not ALIAS_FORMAT_RE.match("AB-1234567")

    def test_namespace_regex_boundary_cases(self):
        """Boundary cases for the namespace regex."""
        # Minimum: 4 segments (country.state.region.class)
        assert NAMESPACE_FORMAT_RE.match("au.nsw.central_coast.cells")
        # Maximum: 7 segments (country + 6 dotted segments)
        assert NAMESPACE_FORMAT_RE.match("au.nsw.cc.cells.sub1.sub2")
        # 3 segments — permitted by locked regex {2,5} (country + 2 dotted)
        assert NAMESPACE_FORMAT_RE.match("au.nsw.cells")
        # Too few (2 segments)
        assert not NAMESPACE_FORMAT_RE.match("au.nsw")

    def test_reserved_top_level_segments(self):
        """Reserved top-level segments are correctly defined."""
        assert RESERVED_TOP_LEVEL_SEGMENTS == {"global", "system", "test"}


# =========================================================================
# Test Class 11: Full Registration Flow (Mock DB)
# =========================================================================

class TestRegistrationFlowMock:
    """
    Test the full alias flow with mocked database connections.
    Validates the logic path without requiring PostgreSQL.
    """

    def test_resolve_alias_without_namespace_raises(self):
        """resolve_alias without namespace must raise NamespaceRequiredError (§7.4)."""
        from alias_service import resolve_alias
        mock_conn = MagicMock()
        with pytest.raises(NamespaceRequiredError):
            resolve_alias(mock_conn, "CC-421", namespace=None)

    def test_bind_alias_validates_format(self):
        """bind_alias rejects invalid alias format."""
        from alias_service import bind_alias
        mock_conn = MagicMock()
        with pytest.raises(InvalidAliasFormatError):
            bind_alias(mock_conn, "hc_test12345", "INVALID", "au.nsw.central_coast.cells")

    def test_bind_alias_validates_namespace(self):
        """bind_alias rejects invalid namespace format."""
        from alias_service import bind_alias
        mock_conn = MagicMock()
        with pytest.raises(InvalidNamespaceFormatError):
            bind_alias(mock_conn, "hc_test12345", "CC-421", "invalid")

    def test_bind_alias_rejects_reserved_prefix(self):
        """bind_alias rejects reserved alias prefixes."""
        from alias_service import bind_alias
        mock_conn = MagicMock()
        with pytest.raises(ReservedPrefixError):
            bind_alias(mock_conn, "hc_test12345", "TEST-1", "au.nsw.central_coast.cells")
