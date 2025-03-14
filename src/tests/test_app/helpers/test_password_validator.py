# tests/helpers/test_password_validators.py
import pytest

from app.helpers.password_validator import (
    PasswordValidate,
    calculate_string_similarity,
    contains_common_substitutions,
    validate_password_complexity,
)


# Test PasswordValidate.validate_password
@pytest.mark.parametrize(
    "pwd, conf_pwd, username, expected_valid, expected_messages",
    [
        # Valid case
        (
            "Test123!",
            "Test123!",
            "burhan",
            True,
            [],
        ),
        # Password != confirm  # noqa: ERA001
        (
            "Test123!",
            "Test124!",
            "testuser",
            False,
            [
                "Password confirmation does not match",
            ],
        ),
        # Too similar to username
        (
            "Testuser123!",
            "Testuser123!",
            "testuser",
            False,
            [
                "Password is too similar to username",
                "Password contains username in common substitutions",
            ],
        ),
        # Contains common substitutions
        (
            "4DM1N-12m!",
            "4DM1N-12m!",
            "admin",
            False,
            ["Password contains username in common substitutions"],
        ),
        # # Complexity fail
        (
            "test",
            "test",
            "user",
            False,
            [
                "Password must be at least 8 characters",
                "Password must contain uppercase letters",
                "Password must contain numbers",
                "Password must contain special characters (eg. !@#$%^&*)",
            ],
        ),
    ],
)
def test_validate_password(pwd, conf_pwd, username, expected_valid, expected_messages):
    """Test validasi password dengan berbagai kasus."""
    is_valid, messages = PasswordValidate.validate_password(pwd, conf_pwd, username)
    assert is_valid == expected_valid
    assert messages == expected_messages


# Test contains_common_substitutions
@pytest.mark.parametrize(
    "username, password, expected",
    [
        ("test", "t3st", True),  # e -> 3
        ("best", "b3st", True),  # e -> 3
        ("test", "test123", True),  # direct inclusion
        ("admin", "4dm1n", True),  # a -> 4, i -> 1
        ("admin", "4DM1N", True),  # case insensitivity check
        ("user", "secureP@ssw0rd", False),  # no substitution or inclusion
        ("john", "j0hnny", True),  # o -> 0 with additional characters
        ("smith", "5m1th", True),  # s -> 5, i -> 1
        ("alice", "p@ssw0rd4l1c3", True),  # a -> 4, i -> 1 with prefix
        ("bob", "b0bby123!", True),  # o -> 0 with suffix
        ("carol", "strongp@ss", False),  # no relation
    ],
)
def test_contains_common_substitutions(username, password, expected):
    """Test detection of common substitutions in passwords."""
    result = contains_common_substitutions(username, password)
    assert result == expected


@pytest.mark.parametrize(
    "str1, str2, expected_ratio",
    [
        ("test", "test", 1.0),
        ("test", "tast", 0.75),
        ("TEST", "test", 1.0),  # Case insensitive
        ("hello", "world", 0.2),
        ("apple", "apples", 0.9),  # Similar strings
        ("abcde", "abxyz", 0.4),  # Different characters
        ("12345", "12345", 1.0),  # Identical numbers
        ("abc123", "ABC123", 1.0),  # Case insensitive with numbers
    ],
)
def test_calculate_string_similarity(str1, str2, expected_ratio):
    """Test string similarity calculation."""
    ratio = calculate_string_similarity(str1, str2)
    assert pytest.approx(ratio, 0.01) == expected_ratio


@pytest.mark.parametrize(
    "password, expected_valid, expected_messages",
    [
        # Valid password - meets all requirements
        ("Test123!", True, []),
        # Length requirement failures
        ("Abc1!", False, ["Password must be at least 8 characters"]),
        # Missing uppercase
        ("test123!", False, ["Password must contain uppercase letters"]),
        # Missing lowercase
        ("TEST123!", False, ["Password must contain lowercase letters"]),
        # Missing numbers
        ("TestABC!", False, ["Password must contain numbers"]),
        # Missing special characters
        ("Test1234", False, ["Password must contain special characters (eg. !@#$%^&*)"]),
        # Multiple failures
        (
            "test",
            False,
            [
                "Password must be at least 8 characters",
                "Password must contain uppercase letters",
                "Password must contain numbers",
                "Password must contain special characters (eg. !@#$%^&*)",
            ],
        ),
        # Edge cases
        ("A1!a    ", True, []),  # With spaces but valid
        ("UPPER123!", False, ["Password must contain lowercase letters"]),
        ("lower123!", False, ["Password must contain uppercase letters"]),
    ],
)
def test_validate_password_complexity(password, expected_valid, expected_messages):
    """Test password complexity validation with various cases."""
    is_valid, messages = validate_password_complexity(password)
    assert is_valid == expected_valid
    assert messages == expected_messages
