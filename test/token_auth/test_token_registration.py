import logging
import pytest

from unittest.mock import ANY
from main import token_command
from token_auth_db.models import AuthUser, AuthToken

import telegram
from telegram.ext import ContextTypes


@pytest.fixture
def update(mocker):
    message = mocker.Mock(spec=telegram.Message)
    message.from_user = mocker.Mock(spec=telegram.User)
    message.reply_text = mocker.AsyncMock()

    update = mocker.Mock(spec=telegram.Update)
    update.message = message
    update.effective_user = mocker.Mock()
    update.effective_user.username = "Alice"
    update.effective_user.id = "tg1234"
    update.effective_chat = mocker.Mock(spec=telegram.Chat)
    return update


@pytest.fixture
def context(mocker):
    context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = list()
    return context


@pytest.mark.asyncio
async def test_token_not_set(update, context, caplog):
    """Check case when token is not passed to the command"""
    caplog.set_level(logging.WARNING)
    await token_command(update, context)

    assert "No parameters passed" in caplog.text


@pytest.mark.asyncio
async def test_non_existed_token(update, context, mocker, caplog):
    """Check case when passed non exixted token"""
    caplog.set_level(logging.WARNING)

    context.args.append("non_existing_token")

    await token_command(update, context)

    assert f"user='{update.effective_user.id}' passed token" in caplog.text

    update.message.reply_text.assert_called_once_with(
        "Passed token is not valid, please check that it is correct"
    )


@pytest.mark.asyncio
async def test_new_user(update, context, mocker):
    """Check case with new token but when user is not registered yet.
    In that case new user is created"""
    token = mocker.Mock(spec=AuthToken)
    token.id = "token1234"
    token.user = None

    context.args.append(token.id)

    mocker.patch("token_auth_db.models.AuthToken.find_by_id", return_value=token)
    mocker.patch("token_auth_db.models.AuthUser.find_by_id", return_value=None)
    mocker.patch("token_auth_db.models.AuthUser.create")

    await token_command(update, context)

    AuthUser.create.assert_called_once_with(
        update.effective_user.id,
        update.effective_user.username,
        ANY,  # it's session, we don't have access to check
    )


@pytest.mark.asyncio
async def test_existing_user(update, context, mocker, caplog):
    """Check case with new token for exsiting user.
    In that case new token is appended to other user's tokens"""
    caplog.set_level(logging.INFO)

    user = mocker.Mock(spec=AuthUser)
    user.id = "tg1234"
    user.name = "Alice"
    user.tokens = []

    token = mocker.Mock(spec=AuthToken)
    token.id = "token1234"
    token.user = None

    context.args.append(token.id)

    mocker.patch("token_auth_db.models.AuthToken.find_by_id", return_value=token)
    mocker.patch("token_auth_db.models.AuthUser.find_by_id", return_value=user)
    mocker.patch("token_auth_db.models.AuthUser.create")

    await token_command(update, context)

    assert len(user.tokens) == 1
    assert user.tokens[0].id == "token1234"

    # check case when user already as token
    user.tokens = [token]
    mocker.patch("token_auth_db.models.AuthUser.find_by_id", return_value=user)

    await token_command(update, context)

    assert "Nothing to do, token already registered" in caplog.text


@pytest.mark.asyncio
async def test_assigned_user(update, context, mocker, caplog):
    """Check case with when a passed token already assigned to an user.
    In that case new we check matching current usser with assigned"""
    caplog.set_level(logging.INFO)

    alice = mocker.Mock(spec=AuthUser)
    alice.id = "tg1234"
    alice.name = "Alice"
    alice.tokens = []

    bob = mocker.Mock(spec=AuthUser)
    bob.id = "tg5678"
    bob.name = "Bob"
    bob.tokens = []

    token = mocker.Mock(spec=AuthToken)
    token.id = "token1234"
    token.user_id = alice.id
    token.user = alice

    context.args.append(token.id)

    mocker.patch("token_auth_db.models.AuthToken.find_by_id", return_value=token)
    mocker.patch("token_auth_db.models.AuthUser.find_by_id", return_value=alice)
    mocker.patch("token_auth_db.models.AuthUser.create")

    await token_command(update, context)

    assert "Token belongs to the same user, everything is Ok" in caplog.text

    # change assigned user to Bob
    token.user_id = bob.id
    token.user = bob
    mocker.patch("token_auth_db.models.AuthToken.find_by_id", return_value=token)

    await token_command(update, context)

    update.message.reply_text.assert_called_once_with(
        "Passed token is not valid, please check that it is correct"
    )
