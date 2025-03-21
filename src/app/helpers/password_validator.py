import re  # noqa: D100

from difflib import SequenceMatcher

from app.config import COMMON_SUBSTITUTIONS, MIN_LENGTH, SIMILARITY_THRESHOLD


class PasswordValidate:
    """Password validator class.

    This class provides functionality to validate passwords based on various criteria
    including matching confirmation, similarity to username, common substitutions,
    and complexity requirements.
    """

    @staticmethod
    def validate_password(
        pwd: str,
        conf_pwd: str,
        username: str,
    ) -> tuple[bool, list[str]]:
        """Validate password against various security criteria.

        Parameters
        ----------
        pwd : str
            The password to validate
        conf_pwd : str
            The confirmation password to check against
        username : str
            The username to check for similarities

        Returns
        -------
        tuple[bool, list[str]]
            A tuple containing:
            - bool: True if password is valid, False otherwise
            - list[str]: List of validation error messages if any, empty if valid

        Notes
        -----
        This function checks if a password meets security requirements by validating:
        1. Password matches confirmation password
        2. Password is not too similar to username
        3. Password doesn't contain username with common character substitutions
        4. Password complexity (length, case, numbers, special chars)

        """
        is_valid = True
        messages = []

        # check if password and confirm_password are the same
        if pwd != conf_pwd:
            is_valid = False
            messages.append("Password confirmation does not match")
            # we return early if password and confirm_password are not the same
            return is_valid, messages

        # if password have similarity with username
        sim_username_pwd = calculate_string_similarity(username, pwd)
        if sim_username_pwd > SIMILARITY_THRESHOLD:
            is_valid = False
            messages.append("Password is too similar to username")

        # if password contains username in common substitutions
        is_contain = contains_common_substitutions(
            username=username,
            password=pwd,
        )
        if is_contain:
            is_valid = False
            messages.append(
                "Password contains username in common substitutions",
            )

        # check length, uppercase, lowercase, number, special character
        is_valid_complex, ls_messages = validate_password_complexity(pwd)
        if is_valid_complex is False:
            is_valid = is_valid_complex
            messages.extend(ls_messages)

        return is_valid, messages


def calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def contains_common_substitutions(username: str, password: str) -> bool:
    """Check if password contains common substitutions of username."""
    modified_username = username.lower()
    modified_password = password.lower()
    for char, num in COMMON_SUBSTITUTIONS.items():
        modified_username = modified_username.replace(char, num)
        modified_password = modified_password.replace(char, num)
    return (modified_username in modified_password) or (modified_password in modified_username)


def validate_password_complexity(password: str) -> tuple[bool, list[str]]:
    checks = [
        (
            len(password) < MIN_LENGTH,
            f"Password must be at least {MIN_LENGTH} characters",
        ),
        (
            not re.search(r"[A-Z]", password),
            "Password must contain uppercase letters",
        ),
        (
            not re.search(r"[a-z]", password),
            "Password must contain lowercase letters",
        ),
        (not re.search(r"\d", password), "Password must contain numbers"),
        (
            not re.search(r'[!@#$%^&*(),.?":{}|<>]', password),
            "Password must contain special characters (eg. !@#$%^&*)",
        ),
    ]

    is_valid = True
    ls_messages = []
    for check, message in checks:
        if check:
            is_valid = False
            ls_messages.append(message)

    return is_valid, ls_messages
