from __future__ import annotations

import json
import unittest
from uuid import UUID

import httpx

from valmar import CreatePersonInput, Valmar

ORGANIZATION_ID = "11111111-1111-4111-8111-111111111111"
PROJECT_ID = "22222222-2222-4222-8222-222222222222"
KNOWLEDGE_REQUEST_ID = "33333333-3333-4333-8333-333333333333"
KNOWLEDGE_ITEM_ID = "44444444-4444-4444-8444-444444444444"
MEMBER_ID = "55555555-5555-4555-8555-555555555555"
RUN_ID = "77777777-7777-4777-8777-777777777777"


def build_client(handler: httpx.MockTransport) -> Valmar:
    client = Valmar(
        api_key="valmr_proj_sk_test",
        base_url="https://api.example.test",
        organization_id=ORGANIZATION_ID,
        project_id=PROJECT_ID,
    )
    client._http.close()
    client._http = httpx.Client(base_url=client.base_url, transport=handler)
    return client


class ValmarTest(unittest.TestCase):
    def test_knowledge_gaps_workflow_uses_project_scoped_paths(self) -> None:
        seen: list[tuple[str, str, object | None]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content) if request.content else None
            seen.append((request.method, request.url.path, body))
            if request.url.path.endswith("/overview"):
                return httpx.Response(
                    200,
                    json={
                        "cli_command": "knowledge-gaps run",
                        "output_dir": "postgres:knowledge_gaps_runs",
                        "pipeline_ready": True,
                        "submission_ready": True,
                        "active_connection_id": None,
                        "saved_connections": [],
                        "config_fields": [],
                        "artifacts": [],
                        "runs": [],
                        "run_status": None,
                        "config_values": None,
                    },
                )
            if request.url.path.endswith("/run"):
                return httpx.Response(
                    200,
                    json={
                        "run_id": RUN_ID,
                        "status": "running",
                        "completed_steps": [],
                    },
                )
            if "/artifacts/" in request.url.path:
                return httpx.Response(200, json={"ranked_gaps": []})
            return httpx.Response(
                200,
                json={
                    "submissions": [
                        {
                            "gap_rank": 1,
                            "gap_title": "Missing rollback process",
                            "knowledge_request_id": KNOWLEDGE_REQUEST_ID,
                            "submitted_at": "2026-01-01T00:00:00Z",
                        }
                    ]
                },
            )

        client = build_client(httpx.MockTransport(handler))
        assert client.knowledge_gaps.overview().pipeline_ready is True
        assert client.knowledge_gaps.start_run(custom_instructions="Focus on incidents").run_id == UUID(RUN_ID)
        assert client.knowledge_gaps.get_run_artifact(RUN_ID, "ranking.json") == {
            "ranked_gaps": []
        }
        submissions = client.knowledge_gaps.submit_ranked_gaps(RUN_ID, gap_ranks=[1])
        assert submissions[0].knowledge_request_id == UUID(KNOWLEDGE_REQUEST_ID)
        base = f"/api/projects/{PROJECT_ID}/knowledge-gaps"
        self.assertEqual(
            seen,
            [
                ("GET", f"{base}/overview", None),
                ("POST", f"{base}/run", {"custom_instructions": "Focus on incidents"}),
                ("GET", f"{base}/runs/{RUN_ID}/artifacts/ranking.json", None),
                ("POST", f"{base}/runs/{RUN_ID}/submit", {"gap_ranks": [1]}),
            ],
        )

    def test_search_knowledge_sends_project_scope_and_parses_items(self) -> None:
        seen_body: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/knowledge/search")
            seen_body.update(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": KNOWLEDGE_ITEM_ID,
                            "created_at": "2026-01-01T00:00:00Z",
                            "updated_at": "2026-01-01T00:00:00Z",
                            "organization_id": ORGANIZATION_ID,
                            "project_id": PROJECT_ID,
                            "knowledge_request_id": KNOWLEDGE_REQUEST_ID,
                            "type": "text",
                            "title": "Deployment process",
                            "content_md": "Use the release checklist.",
                            "metadata": {
                                "expert_names": ["Employee One"],
                                "chat_participants": [
                                    {
                                        "member_id": MEMBER_ID,
                                        "display_name": "Employee One",
                                        "email": "employee@example.test",
                                        "title": "Ops Lead",
                                    }
                                ],
                                "approved_at": "2026-01-02T00:00:00Z",
                            },
                            "provenance": {},
                            "source_thread_id": "66666666-6666-4666-8666-666666666666",
                            "confidence": 0.8,
                            "review_status": "auto_accepted",
                            "source_member_ids": [MEMBER_ID],
                        }
                    ],
                    "total_count": 1,
                },
            )

        client = build_client(httpx.MockTransport(handler))
        result = client.knowledge.search("deployment", limit=3)

        self.assertEqual(
            seen_body,
            {
                "organization_id": ORGANIZATION_ID,
                "project_id": PROJECT_ID,
                "query": "deployment",
                "types": [],
                "source_member_ids": [],
                "limit": 3,
            },
        )
        self.assertEqual(result.items[0].knowledge_request_id, UUID(KNOWLEDGE_REQUEST_ID))
        self.assertIsNotNone(result.items[0].metadata)
        assert result.items[0].metadata is not None
        self.assertEqual(result.items[0].metadata.expert_names, ["Employee One"])
        self.assertEqual(len(result.items[0].metadata.chat_participants), 1)
        self.assertEqual(
            result.items[0].metadata.chat_participants[0].member_id,
            UUID(MEMBER_ID),
        )
        self.assertEqual(result.items[0].metadata.approved_at.year, 2026)
        self.assertEqual(
            result.items[0].source_thread_id,
            UUID("66666666-6666-4666-8666-666666666666"),
        )
        self.assertEqual(result.items[0].source_member_ids, [UUID(MEMBER_ID)])

    def test_create_and_get_knowledge_request_use_new_names(self) -> None:
        paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            if request.method == "POST":
                body = json.loads(request.content)
                self.assertEqual(body["project_id"], PROJECT_ID)
                self.assertEqual(body["requesting_application"], "test-agent")
                return httpx.Response(
                    200,
                    json={
                        "knowledge_request_id": KNOWLEDGE_REQUEST_ID,
                        "status": "pending",
                        "resource_uri": f"valmar://knowledge-requests/{KNOWLEDGE_REQUEST_ID}",
                        "message": "Request submitted.",
                    },
                )
            return httpx.Response(
                200,
                json={
                    "id": KNOWLEDGE_REQUEST_ID,
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "organization_id": ORGANIZATION_ID,
                    "project_id": PROJECT_ID,
                    "requesting_application": "test-agent",
                    "question": "How do releases work?",
                    "status": "completed",
                    "result_summary": "Use the checklist.",
                    "answer": {
                        "status": "resolved",
                        "answer_text": "Use the checklist.",
                        "answer_knowledge_items": [KNOWLEDGE_ITEM_ID],
                        "source_member_ids": [MEMBER_ID],
                    },
                    "created_by_actor_id": "machine:test",
                },
            )

        client = build_client(httpx.MockTransport(handler))
        handle = client.knowledge_requests.create(
            "How do releases work?",
            requesting_application="test-agent",
        )
        request = client.knowledge_requests.get(handle.knowledge_request_id)

        self.assertEqual(handle.knowledge_request_id, UUID(KNOWLEDGE_REQUEST_ID))
        self.assertEqual(request.result_summary, "Use the checklist.")
        self.assertIsNotNone(request.answer)
        assert request.answer is not None
        self.assertEqual(request.answer.source_member_ids, [UUID(MEMBER_ID)])
        self.assertEqual(
            paths,
            [
                "/api/knowledge/requests",
                f"/api/knowledge/requests/{KNOWLEDGE_REQUEST_ID}",
            ],
        )

    def test_list_knowledge_requests_and_import_people(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/knowledge-requests"):
                return httpx.Response(
                    200,
                    json=[
                        {
                            "id": KNOWLEDGE_REQUEST_ID,
                            "project_id": PROJECT_ID,
                            "requesting_application": "admin-ui",
                            "question": "Where is the policy?",
                            "status": "pending",
                            "created_at": "2026-01-01T00:00:00Z",
                            "assigned_members": [],
                        }
                    ],
                )

            body = json.loads(request.content)
            self.assertEqual(body["people"][0]["display_name"], "Ada Lovelace")
            return httpx.Response(
                200,
                json={
                    "created": [
                        {
                            "email": "ada@example.com",
                            "status": "created",
                            "member_id": "55555555-5555-4555-8555-555555555555",
                        }
                    ],
                    "skipped": [],
                    "errors": [],
                },
            )

        client = build_client(httpx.MockTransport(handler))

        requests = client.knowledge_requests.list()
        result = client.people.import_bulk(
            [CreatePersonInput(email="ada@example.com", display_name="Ada Lovelace")]
        )

        self.assertEqual(requests[0].question, "Where is the policy?")
        self.assertEqual(result.created[0].email, "ada@example.com")

    def test_manually_assign_knowledge_request(self) -> None:
        seen_body: dict[str, object] = {}
        seen_path = ""

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal seen_path
            seen_path = request.url.path
            seen_body.update(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "id": "66666666-6666-4666-8666-666666666666",
                    "knowledge_request_id": KNOWLEDGE_REQUEST_ID,
                    "member_id": MEMBER_ID,
                    "member_display_name": "Ada Lovelace",
                    "member_title": "Platform Expert",
                    "reason": "Manual assignment.",
                    "score": 0.5,
                    "evidence": [],
                    "status": "pending",
                    "agent_run_id": None,
                    "conversation_thread_id": None,
                    "answer": None,
                    "result_summary": None,
                    "completed_at": None,
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )

        client = build_client(httpx.MockTransport(handler))
        assignment = client.knowledge_requests.assign(
            KNOWLEDGE_REQUEST_ID,
            member_id=MEMBER_ID,
            reason="Manual assignment.",
        )

        self.assertEqual(
            seen_path,
            f"/api/knowledge/requests/{KNOWLEDGE_REQUEST_ID}/assignments",
        )
        self.assertEqual(
            seen_body,
            {
                "member_id": MEMBER_ID,
                "reason": "Manual assignment.",
            },
        )
        self.assertEqual(assignment.member_id, UUID(MEMBER_ID))
        self.assertEqual(assignment.status, "pending")

    def test_removed_synthesis_helpers_are_not_exposed(self) -> None:
        client = build_client(httpx.MockTransport(lambda _request: httpx.Response(200, json={})))

        self.assertFalse(hasattr(client.knowledge_requests, "synthesize"))
        self.assertFalse(hasattr(client.knowledge_requests, "ignore_synthesis"))
        self.assertFalse(hasattr(client.knowledge_requests, "exclude_assignment_from_synthesis"))


if __name__ == "__main__":
    unittest.main()
