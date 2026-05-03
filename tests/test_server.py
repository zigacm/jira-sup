import os

import httpx
import pytest
import respx

from jira_mcp import client as jira
from jira_mcp import server


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("JIRA_SITE", "test")
    monkeypatch.setenv("JIRA_EMAIL", "u@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "tok")
    yield


BASE = "https://test.atlassian.net"


@respx.mock
async def test_get_current_user():
    respx.get(f"{BASE}/rest/api/3/myself").mock(
        return_value=httpx.Response(200, json={"accountId": "abc", "displayName": "Me"})
    )
    out = await server.get_current_user()
    assert out["accountId"] == "abc"


@respx.mock
async def test_search_issues_uses_new_endpoint():
    route = respx.post(f"{BASE}/rest/api/3/search/jql").mock(
        return_value=httpx.Response(
            200,
            json={
                "issues": [
                    {
                        "key": "SUP-1",
                        "id": "10001",
                        "fields": {
                            "summary": "Hi",
                            "status": {"name": "Open"},
                            "assignee": {"displayName": "Me"},
                            "priority": {"name": "High"},
                            "updated": "2026-04-29T00:00:00.000+0000",
                        },
                    }
                ],
                "isLast": True,
            },
        )
    )
    out = await server.search_issues(jql="project = SUP")
    assert route.called
    body = route.calls[0].request.read()
    assert b'"jql": "project = SUP"' in body or b'"jql":"project = SUP"' in body
    assert out["issues"][0]["key"] == "SUP-1"
    assert out["issues"][0]["status"] == "Open"


@respx.mock
async def test_add_comment_wraps_in_adf():
    route = respx.post(f"{BASE}/rest/api/3/issue/SUP-1/comment").mock(
        return_value=httpx.Response(201, json={"id": "1"})
    )
    await server.add_comment(issue_key="SUP-1", body="hello")
    sent = route.calls[0].request.read()
    assert b'"type": "doc"' in sent or b'"type":"doc"' in sent
    assert b"hello" in sent


@respx.mock
async def test_transition_issue_resolves_name():
    respx.get(f"{BASE}/rest/api/3/issue/SUP-1/transitions").mock(
        return_value=httpx.Response(
            200,
            json={
                "transitions": [
                    {"id": "31", "name": "Done", "to": {"name": "Done"}},
                    {"id": "11", "name": "In Progress", "to": {"name": "In Progress"}},
                ]
            },
        )
    )
    post = respx.post(f"{BASE}/rest/api/3/issue/SUP-1/transitions").mock(
        return_value=httpx.Response(204)
    )
    out = await server.transition_issue(
        issue_key="SUP-1", transition_name="done", comment="closing"
    )
    assert post.called
    body = post.calls[0].request.read()
    assert b'"id": "31"' in body or b'"id":"31"' in body
    assert b"closing" in body  # comment included
    assert out["transitioned_to"] == "Done"


@respx.mock
async def test_assign_issue_resolves_query():
    respx.get(f"{BASE}/rest/api/3/user/assignable/search").mock(
        return_value=httpx.Response(
            200, json=[{"accountId": "u123", "displayName": "Maria"}]
        )
    )
    put = respx.put(f"{BASE}/rest/api/3/issue/SUP-1/assignee").mock(
        return_value=httpx.Response(204)
    )
    out = await server.assign_issue(issue_key="SUP-1", query="Maria")
    assert put.called
    assert out["accountId"] == "u123"
    assert out["displayName"] == "Maria"


@respx.mock
async def test_api_error_surfaces_message():
    respx.get(f"{BASE}/rest/api/3/issue/SUP-999").mock(
        return_value=httpx.Response(404, json={"errorMessages": ["Issue does not exist"]})
    )
    with pytest.raises(jira.JiraAPIError) as exc:
        await server.get_issue(issue_key="SUP-999")
    assert "Issue does not exist" in str(exc.value)


@respx.mock
async def test_link_issues():
    route = respx.post(f"{BASE}/rest/api/3/issueLink").mock(
        return_value=httpx.Response(201)
    )
    out = await server.link_issues(
        inward_key="SUP-1", outward_key="SUP-2", link_type="Blocks"
    )
    assert route.called
    assert out == {"inward": "SUP-1", "outward": "SUP-2", "type": "Blocks"}
