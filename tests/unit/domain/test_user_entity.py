import pytest

from app.domain.exceptions.users import (InvalidEmailFormat,
                                         InvalidPhoneFormat,
                                         InvalidUsernameFormat)
from tests.factories import UserFactory


class TestUserCreate:
    def test_create_sets_expected_defaults(self):
        user = UserFactory()

        assert user.is_active is True
        assert user.is_email_verified is False
        assert user.hashed_password == ""

    def test_create_generates_unique_ids(self):
        assert UserFactory().id != UserFactory().id

    def test_create_stores_given_fields(self):
        user = UserFactory(username="john_doe", email="john@mail.com", phone="+79991234567")

        assert user.username == "john_doe"
        assert user.email == "john@mail.com"
        assert user.phone == "+79991234567"

    def test_create_with_invalid_username_raises(self):
        with pytest.raises(InvalidUsernameFormat):
            UserFactory(username="ab")

    def test_create_with_invalid_email_raises(self):
        with pytest.raises(InvalidEmailFormat):
            UserFactory(email="not-an-email")

    def test_create_with_invalid_phone_raises(self):
        with pytest.raises(InvalidPhoneFormat):
            UserFactory(phone="123")


class TestChangeUsername:
    def test_changes_username(self):
        user = UserFactory()
        user.change_username("new_name")
        assert user.username == "new_name"

    def test_does_not_lose_email_and_phone(self):
        """
        Регрессионный тест на баг: исходная реализация change_username
        собирала UserIdentity(username=new_username, email=self.email)
        без phone -> TypeError. Даже если бы phone был передан, раньше
        передавались "сырые" строки вместо VO, минуя нормализацию/валидацию.
        """
        user = UserFactory(email="john@mail.com", phone="+79991234567")
        user.change_username("new_name")

        assert user.email == "john@mail.com"
        assert user.phone == "+79991234567"

    def test_invalid_new_username_raises(self):
        user = UserFactory()
        with pytest.raises(InvalidUsernameFormat):
            user.change_username("x")

    def test_updates_updated_at(self):
        user = UserFactory()
        before = user.updated_at
        user.change_username("new_name")
        assert user.updated_at >= before


class TestChangeEmail:
    def test_changes_email(self):
        user = UserFactory()
        user.change_email("new@mail.com")
        assert user.email == "new@mail.com"

    def test_does_not_lose_username_and_phone(self):
        user = UserFactory(username="john_doe", phone="+79991234567")
        user.change_email("new@mail.com")

        assert user.username == "john_doe"
        assert user.phone == "+79991234567"

    def test_resets_email_verification(self):
        user = UserFactory()
        user.verify_email()
        assert user.is_email_verified is True

        user.change_email("new@mail.com")
        assert user.is_email_verified is False

    def test_invalid_new_email_raises(self):
        user = UserFactory()
        with pytest.raises(InvalidEmailFormat):
            user.change_email("not-an-email")


class TestChangePhone:
    def test_changes_phone(self):
        user = UserFactory()
        user.change_phone("+79997654321")
        assert user.phone == "+79997654321"

    def test_does_not_lose_username_and_email(self):
        user = UserFactory(username="john_doe", email="john@mail.com")
        user.change_phone("+79997654321")

        assert user.username == "john_doe"
        assert user.email == "john@mail.com"

    def test_invalid_new_phone_raises(self):
        user = UserFactory()
        with pytest.raises(InvalidPhoneFormat):
            user.change_phone("123")


class TestPassword:
    def test_set_password_updates_hash(self):
        user = UserFactory()
        user.set_password("hashed-value")
        assert user.hashed_password == "hashed-value"

    def test_set_empty_password_raises(self):
        user = UserFactory()
        with pytest.raises(ValueError):
            user.set_password("")


class TestActivation:
    def test_disable_sets_is_active_false(self):
        user = UserFactory()
        user.disable()
        assert user.is_active is False

    def test_enable_sets_is_active_true(self):
        user = UserFactory()
        user.disable()
        user.enable()
        assert user.is_active is True


class TestEmailVerification:
    def test_verify_email_sets_flag(self):
        user = UserFactory()
        assert user.is_email_verified is False
        user.verify_email()
        assert user.is_email_verified is True