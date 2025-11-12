"""Tests for Nepali phone number normalization."""

from nes.core.utils.phone_number import normalize_nepali_phone_number


class TestNormalizeNepaliPhoneNumber:
    """Test cases for normalize_nepali_phone_number function."""

    def test_mobile_10_digits(self):
        """Test standard 10-digit mobile numbers."""
        assert normalize_nepali_phone_number("9851081379") == "+9779851081379"
        assert normalize_nepali_phone_number("9841451734") == "+9779841451734"
        assert normalize_nepali_phone_number("9860927727") == "+9779860927727"

    def test_mobile_9_digits(self):
        """Test 9-digit mobile numbers."""
        assert normalize_nepali_phone_number("982671070") == "+977982671070"
        assert normalize_nepali_phone_number("985007653") == "+977985007653"

    def test_landline_with_prefix(self):
        """Test landline numbers with 01- prefix."""
        assert normalize_nepali_phone_number("01-4569033") == "+97714569033"
        assert normalize_nepali_phone_number("01-4510568") == "+97714510568"
        assert normalize_nepali_phone_number("01-4378055") == "+97714378055"
        assert normalize_nepali_phone_number("01-4602288") == "+97714602288"

    def test_landline_7_digits(self):
        """Test 7-digit landline numbers."""
        assert normalize_nepali_phone_number("6610974") == "+9776610974"
        assert normalize_nepali_phone_number("6610026") == "+9776610026"
        assert normalize_nepali_phone_number("4381016") == "+9774381016"
        assert normalize_nepali_phone_number("5230577") == "+9775230577"

    def test_landline_with_leading_zero(self):
        """Test landline numbers with leading zero but no dash."""
        assert normalize_nepali_phone_number("014113510") == "+97714113510"
        assert normalize_nepali_phone_number("014786262") == "+97714786262"
        assert normalize_nepali_phone_number("014289380") == "+97714289380"
        assert normalize_nepali_phone_number("0159108112") == "+977159108112"
        assert normalize_nepali_phone_number("0159108113") == "+977159108113"

    def test_landline_6_digits(self):
        """Test 6-digit landline numbers."""
        assert normalize_nepali_phone_number("420374") == "+977420374"

    def test_invalid_11_digits(self):
        """Test 11-digit numbers should return None."""
        assert normalize_nepali_phone_number("98511535618") is None

    def test_landline_other_area_codes(self):
        """Test landline numbers with other area codes."""
        assert normalize_nepali_phone_number("015911555") == "+97715911555"
        assert normalize_nepali_phone_number("01-5434322") == "+97715434322"
        assert normalize_nepali_phone_number("01-5910125") == "+97715910125"

    def test_empty_and_none(self):
        """Test empty string and None inputs."""
        assert normalize_nepali_phone_number("") is None
        assert normalize_nepali_phone_number(None) is None

    def test_non_numeric(self):
        """Test non-numeric inputs."""
        assert normalize_nepali_phone_number("abc") is None

    def test_whitespace_handling(self):
        """Test numbers with whitespace."""
        assert normalize_nepali_phone_number(" 9851081379 ") == "+9779851081379"
        assert normalize_nepali_phone_number("01-4569033 ") == "+97714569033"

    def test_various_mobile_prefixes(self):
        """Test mobile numbers with different operator prefixes."""
        assert normalize_nepali_phone_number("9803051270") == "+9779803051270"
        assert normalize_nepali_phone_number("9813102391") == "+9779813102391"
        assert normalize_nepali_phone_number("9841451734") == "+9779841451734"
        assert normalize_nepali_phone_number("9851081379") == "+9779851081379"
        assert normalize_nepali_phone_number("9860927727") == "+9779860927727"
        assert normalize_nepali_phone_number("9869376916") == "+9779869376916"
        assert normalize_nepali_phone_number("9875370091") == "+9779875370091"

    def test_edge_cases_from_dataset(self):
        """Test specific edge cases from the provided dataset."""
        assert normalize_nepali_phone_number("4471071") == "+9774471071"
        assert normalize_nepali_phone_number("4784962") == "+9774784962"
        assert normalize_nepali_phone_number("4487721") == "+9774487721"
        assert normalize_nepali_phone_number("5525361") == "+9775525361"
        assert normalize_nepali_phone_number("01-6630583") == "+97716630583"
        assert normalize_nepali_phone_number("01-4106302") == "+97714106302"

    def test_with_country_code(self):
        """Test numbers already containing +977."""
        assert normalize_nepali_phone_number("+9779851081379") == "+9779851081379"
        assert normalize_nepali_phone_number("+977-9841451734") == "+9779841451734"
        assert normalize_nepali_phone_number("+977 9860927727") == "+9779860927727"
        assert normalize_nepali_phone_number("+97714569033") == "+97714569033"
        assert normalize_nepali_phone_number("+977-1-4569033") == "+97714569033"
        assert normalize_nepali_phone_number("009779851081379") == "+9779851081379"
        assert normalize_nepali_phone_number("00977-1-4569033") == "+97714569033"
