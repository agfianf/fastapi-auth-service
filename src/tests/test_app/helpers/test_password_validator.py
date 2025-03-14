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
            "testuser",
            True,
            [],
        ),
        # Password != confirm  # noqa: ERA001
        (
            "Test123!",
            "Test124!",
            "testuser",
            False,
            ["Password confirmation does not match"],
        ),
        # Too similar to username
        (
            "testuser123",
            "testuser123",
            "testuser",
            False,
            ["Password is too similar to username"],
        ),
        # Contains common substitutions
        (
            "t3stuser",
            "t3stuser",
            "testuser",
            False,
            ["Password contains username in common substitutions"],
        ),
        # Complexity fail
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


# Test calculate_string_similarity
@pytest.mark.parametrize(
    "str1, str2, expected_ratio",
    [
        ("test", "test", 1.0),
        ("test", "tast", 0.75),
        ("TEST", "test", 1.0),  # Case insensitive
        ("hello", "world", 0.2),
    ],
)
def test_calculate_string_similarity(str1, str2, expected_ratio):
    """Test perhitungan similarity antar string."""
    ratio = calculate_string_similarity(str1, str2)
    assert pytest.approx(ratio, 0.01) == expected_ratio  # Toleransi 0.01


# Test contains_common_substitutions
@pytest.mark.parametrize(
    "username, password, expected",
    [
        ("test", "t3st", True),  # e -> 3
        ("best", "b3st", True),  # e -> 3
        ("test", "test123", False),
        ("admin", "4dm1n", True),  # a -> 4, i -> 1
    ],
)
def test_contains_common_substitutions(username, password, expected):
    """Test deteksi substitusi umum."""
    result = contains_common_substitutions(username, password)
    assert result == expected


# Test validate_password_complexity
@pytest.mark.parametrize(
    "password, expected_valid, expected_messages",
    [
        ("Test123!", True, []),
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
        ("TEST123!", True, []),
        ("Test123", False, ["Password must contain special characters (eg. !@#$%^&*)"]),
    ],
)
def test_validate_password_complexity(password, expected_valid, expected_messages):
    """Test validasi kompleksitas password."""
    is_valid, messages = validate_password_complexity(password)
    assert is_valid == expected_valid
    assert messages == expected_messages
