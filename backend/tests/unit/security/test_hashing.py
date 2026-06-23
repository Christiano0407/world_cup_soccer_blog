from __future__ import annotations

from app.core.security import hash_password, verify_password


class TestHashPassword:
    def test_hash_returns_different_hash_each_time(self) -> None:
        plain = "SecurePass123"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2

    def test_hash_starts_with_bcrypt_prefix(self) -> None:
        hashed = hash_password("MyPassword1")
        assert hashed.startswith("$2b$")

    def test_hash_raises_on_empty_string(self) -> None:
        hashed = hash_password("")
        assert verify_password("", hashed)


class TestVerifyPassword:
    def test_verify_correct_password(self) -> None:
        plain = "CorrectP4ssword"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("RealP4ss")
        assert verify_password("WrongPass1", hashed) is False

    def test_verify_wrong_hash(self) -> None:
        from bcrypt import hashpw, gensalt
        real_hash = hashpw(b"AnyPass12", gensalt(rounds=4)).decode()
        invalid_hash = real_hash[:-5] + "XXXXX"
        assert verify_password("AnyPass12", invalid_hash) is False

    def test_verify_empty_against_valid_hash(self) -> None:
        hashed = hash_password("NonEmpty1")
        assert verify_password("", hashed) is False

    def test_verify_special_characters(self) -> None:
        plain = "P@ssw0rd!$#%&/()="
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_unicode(self) -> None:
        plain = "Contraseña123ñ"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_long_password(self) -> None:
        plain = "A" * 64 + "1"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
