"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="staff",
        password="pw",
        is_staff=True,
    )


@pytest.fixture
def superuser(db):
    User = get_user_model()
    return User.objects.create_superuser(
        username="root",
        password="pw",
        email="root@example.com",
    )


@pytest.fixture
def admin_client(superuser):
    client = Client()
    client.force_login(superuser)
    return client
