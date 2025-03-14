"""Handle Multi-Factor Authentication (MFA) using PyOTP.

This module provides the TwoFactorAuth class which handles the generation
and verification of one-time passwords (OTP) for multi-factor authentication.
"""

import base64

from io import BytesIO

import pyotp
import qrcode

from app.config import settings


class TwoFactorAuth:
    @staticmethod
    def get_secret(secret: str = None) -> str:
        """Get or generate a secret key for OTP.

        Parameters
        ----------
        secret : str, optional
            Existing secret key. If not provided, generates a new one.

        Returns
        -------
        str
            The provided secret key or a newly generated one.

        """
        return secret if secret is not None else pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(
        username: str,
        secret: str = None,
        issuer_name: str = settings.NAME_APP_2FA,
    ) -> str:
        """Generate a provisioning URI for OTP.

        Parameters
        ----------
        username : str
            The username for whom to generate the URI.
        secret : str, optional
            Secret key for OTP generation. If not provided,
            generates a new one.
        issuer_name : str, optional
            Name of the issuing application.

        Returns
        -------
        str
            Provisioning URI for OTP setup.

        """
        s = TwoFactorAuth.get_secret(secret)
        totp = pyotp.TOTP(s)
        return totp.provisioning_uri(name=username, issuer_name=issuer_name)

    @staticmethod
    def get_provisioning_qrcode(
        username: str,
        secret: str = None,
        issuer_name: str = settings.NAME_APP_2FA,
    ) -> bytes:
        """Generate a QR code image as bytes from the provisioning URI.

        Parameters
        ----------
        username : str
            The username for whom to generate the QR code.
        secret : str, optional
            Secret key for OTP generation. If not provided,
            generates a new one.
        issuer_name : str, optional
            Name of the issuing application.

        Returns
        -------
        bytes
            PNG image data of the QR code.

        """
        uri = TwoFactorAuth.get_provisioning_uri(username, secret, issuer_name)
        img = qrcode.make(uri)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    @staticmethod
    def get_provisioning_qrcode_base64(
        username: str,
        secret: str = None,
        issuer_name: str = settings.NAME_APP_2FA,
        size: int = 250,
    ) -> str:
        """Generate a base64 encoded QR code image.

        Parameters
        ----------
        username : str
            The username for whom to generate the QR code.
        secret : str, optional
            Secret key for OTP generation.
            If not provided, generates a new one.
        issuer_name : str, optional
            Name of the issuing application.
        size : int, optional
            Size of the QR code image in pixels, default is 250.

        Returns
        -------
        str
            Base64 encoded PNG image data of the QR code.

        """
        uri = TwoFactorAuth.get_provisioning_uri(username, secret, issuer_name)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))

        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def verify_token(token: str, secret: str) -> bool:
        """Verify a given token against the current OTP.

        Parameters
        ----------
        token : str
            The token to verify.
        secret : str
            The secret key used for OTP generation.

        Returns
        -------
        bool
            True if the token is valid, False otherwise.

        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token)
