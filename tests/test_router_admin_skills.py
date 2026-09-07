# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing skill management endpoints in admin panel
# =============================================================================
# Description:
#   Module contains tests for REST API endpoints /api/admin/skills/*
#
# File: test_router_admin_skills.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from header import __root__
from main import app

client = TestClient(app)

class TestAdminSkillsAPI:
    """Testing skill management endpoints in admin panel."""

    def test_list_skills(self):
        """Check retrieval of skills list via admin route."""
        response = client.get("/api/admin/skills")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert isinstance(data["skills"], list)
        assert data["total"] >= 1

        skill_names = [s["name"] for s in data["skills"]]
        assert "skill-factory" in skill_names or "cert-installer" in skill_names

    def test_list_skills_user_endpoint(self):
        """Check retrieval of skills list via user /api/skills route."""
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert isinstance(data["skills"], list)
        assert data["total"] >= 1

    def test_get_skill_details(self):
        """Check retrieval of specific skill details."""
        list_resp = client.get("/api/admin/skills")
        assert list_resp.status_code == 200
        skills = list_resp.json()["skills"]
        assert len(skills) > 0
        first_skill_name = skills[0]["name"]

        response = client.get(f"/api/admin/skills/{first_skill_name}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "skill" in data
        assert data["skill"]["name"] == first_skill_name
        assert "skill_md_raw" in data["skill"]
        assert "files" in data["skill"]
        assert isinstance(data["skill"]["files"], list)

    def test_get_nonexistent_skill(self):
        """Check 404 response for nonexistent skill."""
        response = client.get("/api/admin/skills/nonexistent-dummy-skill-xyz")
        assert response.status_code == 404

    def test_create_skill_validation(self):
        """Check invalid name validation."""
        response = client.post(
            "/api/admin/skills",
            json={"name": "Invalid Name With Spaces!", "description": "test"}
        )
        assert response.status_code == 400

    def test_skill_full_lifecycle(self):
        """Test creating, updating, packaging, and deleting a skill."""
        test_skill_name = "test-temp-admin-skill"

        # Cleanup if previously left over
        client.delete(f"/api/admin/skills/{test_skill_name}")

        # 1. Create skill
        create_resp = client.post(
            "/api/admin/skills",
            json={
                "name": test_skill_name,
                "description": "Temporary unit test skill",
                "instructions": "## Purpose\nUnit test instructions."
            }
        )
        assert create_resp.status_code == 200
        assert create_resp.json()["status"] == "ok"

        # 2. Verify it shows in list and details
        get_resp = client.get(f"/api/admin/skills/{test_skill_name}")
        assert get_resp.status_code == 200
        skill_data = get_resp.json()["skill"]
        assert skill_data["name"] == test_skill_name
        assert "Unit test instructions" in skill_data["instructions"]

        # 3. Update skill
        update_resp = client.put(
            f"/api/admin/skills/{test_skill_name}",
            json={
                "description": "Updated description",
                "instructions": "## Purpose\nUpdated instructions content."
            }
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "ok"

        # Verify update
        get_updated = client.get(f"/api/admin/skills/{test_skill_name}")
        assert "Updated instructions content" in get_updated.json()["skill"]["instructions"]

        # 4. Package skill
        pkg_resp = client.post(f"/api/admin/skills/{test_skill_name}/package")
        assert pkg_resp.status_code == 200
        pkg_data = pkg_resp.json()
        assert pkg_data["status"] == "ok"
        assert pkg_data["archive"]["filename"] == f"{test_skill_name}.skill"
        assert pkg_data["archive"]["size"] > 0

        # 5. Delete skill
        del_resp = client.delete(f"/api/admin/skills/{test_skill_name}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "ok"

        # Verify deletion
        get_deleted = client.get(f"/api/admin/skills/{test_skill_name}")
        assert get_deleted.status_code == 404
