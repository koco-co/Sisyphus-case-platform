"""
Tests for user configuration management API.
"""
import pytest
from app.tests.conftest import test_client_with_db, db_session
from sqlalchemy import select
from app.models.user_config import UserConfig


@pytest.mark.asyncio
async def test_create_config(test_client_with_db):
    """Test creating a new configuration."""
    response = await test_client_with_db.post(
        "/api/configs/",
        json={
            "provider": "glm",
            "api_key_encrypted": "encrypted_key_123",
            "generator_model": "glm-4",
            "reviewer_model": "glm-4-plus"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "glm"
    assert data["api_key_encrypted"] == "encrypted_key_123"
    assert data["generator_model"] == "glm-4"
    assert data["reviewer_model"] == "glm-4-plus"
    assert data["is_active"] is False
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_config_invalid_provider(test_client_with_db):
    """Test creating a config with invalid provider."""
    response = await test_client_with_db.post(
        "/api/configs/",
        json={
            "provider": "invalid_provider",
            "api_key_encrypted": "encrypted_key_123"
        }
    )
    assert response.status_code == 400
    assert "Invalid provider" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_configs(test_client_with_db, db_session):
    """Test listing all configurations."""
    # Create test configs
    config1 = UserConfig(
        provider="glm",
        api_key_encrypted="key1",
        generator_model="glm-4",
        reviewer_model="glm-4-plus",
        is_active=False
    )
    config2 = UserConfig(
        provider="minimax",
        api_key_encrypted="key2",
        generator_model="abab6.5s",
        reviewer_model="abab6.5s-chat",
        is_active=True
    )
    db_session.add(config1)
    db_session.add(config2)
    await db_session.commit()

    response = await test_client_with_db.get("/api/configs/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(c["provider"] == "glm" for c in data)
    assert any(c["provider"] == "minimax" for c in data)


@pytest.mark.asyncio
async def test_get_active_config(test_client_with_db, db_session):
    """Test getting the active configuration."""
    # Create test configs
    config1 = UserConfig(
        provider="glm",
        api_key_encrypted="key1",
        is_active=False
    )
    config2 = UserConfig(
        provider="minimax",
        api_key_encrypted="key2",
        is_active=True
    )
    db_session.add(config1)
    db_session.add(config2)
    await db_session.commit()

    response = await test_client_with_db.get("/api/configs/active")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "minimax"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_active_config_not_found(test_client_with_db):
    """Test getting active config when none exists."""
    response = await test_client_with_db.get("/api/configs/active")
    assert response.status_code == 404
    assert "No active configuration" in response.json()["detail"]


@pytest.mark.asyncio
async def test_activate_config(test_client_with_db, db_session):
    """Test activating a specific configuration."""
    # Create test configs
    config1 = UserConfig(
        provider="glm",
        api_key_encrypted="key1",
        is_active=True
    )
    config2 = UserConfig(
        provider="minimax",
        api_key_encrypted="key2",
        is_active=False
    )
    db_session.add(config1)
    db_session.add(config2)
    await db_session.commit()
    await db_session.refresh(config2)

    # Activate config2
    response = await test_client_with_db.patch(f"/api/configs/{config2.id}/activate")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Configuration activated"

    # Verify config1 is deactivated and config2 is activated
    result = await db_session.execute(select(UserConfig).where(UserConfig.id == config1.id))
    config1_updated = result.scalar_one()
    assert config1_updated.is_active is False

    result = await db_session.execute(select(UserConfig).where(UserConfig.id == config2.id))
    config2_updated = result.scalar_one()
    assert config2_updated.is_active is True


@pytest.mark.asyncio
async def test_activate_config_not_found(test_client_with_db):
    """Test activating a non-existent configuration."""
    response = await test_client_with_db.patch("/api/configs/999/activate")
    assert response.status_code == 404
    assert "Configuration not found" in response.json()["detail"]
