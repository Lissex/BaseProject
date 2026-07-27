import pytest

from app.domain.exceptions.users import (InvalidEmailFormat,
                                         InvalidPhoneFormat,
                                         InvalidUsernameFormat)
from app.domain.value_objects.email import Email
from app.domain.value_objects.phone import PhoneNumber
from app.domain.value_objects.username import Username


class TestUsername:
    def test_valid_username_is_stored_as_is(self):
        assert Username("john_doe").value == "john_doe"

    def test_normalizes_to_lowercase(self):
        assert Username("John_Doe").value == "john_doe"

    def test_strips_surrounding_whitespace(self):
        assert Username("  admin  ").value == "admin"

    def test_minimum_length_boundary_valid(self):
        assert Username("abc").value == "abc"  # ровно 3 символа

    def test_maximum_length_boundary_valid(self):
        username = "a" * 20
        assert Username(username).value == username

    @pytest.mark.parametrize(
        "raw",
        [
            "ab",  # короче 3 символов
            "a" * 21,  # длиннее 20 символов
            "john-doe",  # дефис не входит в [a-z0-9_]
            "john doe",  # пробел внутри
            "john@doe",  # @ не входит в разрешённые символы
            "",  # пусто
        ],
    )
    def test_invalid_format_raises(self, raw):
        with pytest.raises(InvalidUsernameFormat):
            Username(raw)

    def test_two_usernames_with_same_value_are_equal(self):
        # dataclass(frozen=True) -> сравнение по значению, не по identity
        assert Username("john_doe") == Username("JOHN_DOE")


class TestEmail:
    def test_valid_email_is_stored_as_is(self):
        assert Email("john@mail.com").value == "john@mail.com"

    def test_domain_property(self):
        assert Email("john@mail.com").domain == "mail.com"

    def test_normalizes_to_lowercase(self):
        # До фикса Email не нормализовался (в отличие от Username) —
        # "John@Mail.com" и "john@mail.com" считались разными значениями,
        # что ломало проверку уникальности и логин по email в разном
        # регистре. См. обсуждение в чате.
        assert Email("John@Mail.com").value == "john@mail.com"

    def test_strips_surrounding_whitespace(self):
        assert Email("  john@mail.com  ").value == "john@mail.com"

    def test_two_emails_differing_only_by_case_are_equal(self):
        assert Email("John@Mail.com") == Email("john@mail.com")

    @pytest.mark.parametrize(
        "raw",
        [
            "not-an-email",
            "missing-domain@",
            "@missing-local.com",
            "spaces in@email.com",
            "",
        ],
    )
    def test_invalid_format_raises(self, raw):
        with pytest.raises(InvalidEmailFormat):
            Email(raw)


class TestPhoneNumber:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("+79991234567", "+79991234567"),
            ("89991234567", "+79991234567"),  # 8 в начале -> заменяется на 7
            ("+7 999 123-45-67", "+79991234567"),  # пробелы/дефисы удаляются
            ("8(999)123-45-67", "+79991234567"),  # скобки удаляются
        ],
    )
    def test_normalizes_to_e164_like_format(self, raw, expected):
        assert PhoneNumber(raw).value == expected

    def test_wrong_length_raises(self):
        with pytest.raises(InvalidPhoneFormat):
            PhoneNumber("+7999123456")  # на цифру короче

    def test_non_digit_characters_raise(self):
        with pytest.raises(InvalidPhoneFormat):
            PhoneNumber("+7999abc4567")

    def test_disallowed_second_digit_raises(self):
        # После "7" разрешены только [3, 4, 8, 9] вторым символом
        with pytest.raises(InvalidPhoneFormat):
            PhoneNumber("+71991234567")

    def test_wrong_leading_digit_raises(self):
        with pytest.raises(InvalidPhoneFormat):
            PhoneNumber("+19991234567")  # не начинается с 7/8