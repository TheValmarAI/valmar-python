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
    def test_trace_context_uses_shared_trace_endpoint(self) -> None:
        reference_uri = f"valmar://context/{PROJECT_ID}/unstructured/{KNOWLEDGE_ITEM_ID}"

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.url.path,
                f"/api/context/resources/unstructured/{KNOWLEDGE_ITEM_ID}/trace",
            )
            resource = {
                "reference": {
                    "project_id": PROJECT_ID,
                    "module": "unstructured",
                    "resource_id": KNOWLEDGE_ITEM_ID,
                    "uri": reference_uri,
                },
                "title": "Runbook",
                "content_md": "Use the release checklist.",
                "provenance": {},
                "review_status": "auto_accepted",
                "confidence": 0.8,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
            return httpx.Response(
                200,
                json={
                    "reference": resource["reference"],
                    "resource": resource,
                    "source_thread_ids": [],
                    "conversations": {},
                    "history": [],
                    "audit_events": [],
                    "module_details": {},
                },
            )

        trace = build_client(httpx.MockTransport(handler)).context.trace(reference_uri)
        self.assertEqual(trace.reference.resource_id, UUID(KNOWLEDGE_ITEM_ID))

    def test_read_context_uses_reference_uri(self) -> None:
        reference_uri = f"valmar://context/{PROJECT_ID}/unstructured/{KNOWLEDGE_ITEM_ID}"

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.url.path,
                f"/api/context/resources/unstructured/{KNOWLEDGE_ITEM_ID}",
            )
            return httpx.Response(
                200,
                json={
                    "reference": {
                        "project_id": PROJECT_ID,
                        "module": "unstructured",
                        "resource_id": KNOWLEDGE_ITEM_ID,
                        "uri": reference_uri,
                    },
                    "title": "Runbook",
                    "content_md": "Use the release checklist.",
                    "provenance": {},
                    "review_status": "auto_accepted",
                    "confidence": 0.8,
                    "hidden_metadata": {"external_case_id": "CASE-1234"},
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                },
            )

        resource = build_client(httpx.MockTransport(handler)).context.read(reference_uri)
        self.assertEqual(resource.reference.resource_id, UUID(KNOWLEDGE_ITEM_ID))
        self.assertEqual(resource.content_md, "Use the release checklist.")
        self.assertEqual(resource.hidden_metadata, {"external_case_id": "CASE-1234"})

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
        assert submissions[0].context_request_id == UUID(KNOWLEDGE_REQUEST_ID)
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

    def test_search_context_sends_project_scope_and_parses_hits(self) -> None:
        seen_body: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/context/search")
            seen_body.update(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "hits": [
                        {
                            "reference": {
                                "project_id": PROJECT_ID,
                                "module": "unstructured",
                                "resource_id": KNOWLEDGE_ITEM_ID,
                                "uri": (
                                    f"valmar://context/{PROJECT_ID}/unstructured/"
                                    f"{KNOWLEDGE_ITEM_ID}"
                                ),
                            },
                            "created_at": "2026-01-01T00:00:00Z",
                            "title": "Deployment process",
                            "excerpt": "Use the release checklist.",
                            "score": 0.8,
                            "hidden_metadata": {"external_case_id": "CASE-1234"},
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
                            "source_thread_id": "66666666-6666-4666-8666-666666666666",
                            "source_context_request_id": KNOWLEDGE_REQUEST_ID,
                            "source_member_ids": [MEMBER_ID],
                        }
                    ],
                    "searched_modules": ["unstructured"],
                },
            )

        client = build_client(httpx.MockTransport(handler))
        result = client.context.search("deployment", limit=3)

        self.assertEqual(
            seen_body,
            {
                "organization_id": ORGANIZATION_ID,
                "project_id": PROJECT_ID,
                "query": "deployment",
                "modules": [],
                "source_member_ids": [],
                "limit": 3,
            },
        )
        self.assertEqual(
            result.hits[0].source_context_request_id, UUID(KNOWLEDGE_REQUEST_ID)
        )
        self.assertEqual(
            result.hits[0].hidden_metadata,
            {"external_case_id": "CASE-1234"},
        )
        self.assertIsNotNone(result.hits[0].metadata)
        assert result.hits[0].metadata is not None
        self.assertEqual(result.hits[0].metadata.expert_names, ["Employee One"])
        self.assertEqual(len(result.hits[0].metadata.chat_participants), 1)
        self.assertEqual(
            result.hits[0].metadata.chat_participants[0].member_id,
            UUID(MEMBER_ID),
        )
        self.assertEqual(result.hits[0].metadata.approved_at.year, 2026)
        self.assertEqual(
            result.hits[0].source_thread_id,
            UUID("66666666-6666-4666-8666-666666666666"),
        )
        self.assertEqual(result.hits[0].source_member_ids, [UUID(MEMBER_ID)])

    def test_create_and_get_knowledge_request_use_new_names(self) -> None:
        paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            if request.method == "POST":
                body = json.loads(request.content)
                self.assertEqual(body["project_id"], PROJECT_ID)
                self.assertEqual(body["requesting_application"], "test-agent")
                self.assertEqual(
                    body["hidden_metadata"],
                    {"external_case_id": "CASE-1234"},
                )
                return httpx.Response(
                    200,
                    json={
                        "context_request_id": KNOWLEDGE_REQUEST_ID,
                        "status": "pending",
                        "resource_uri": f"valmar://context-requests/{KNOWLEDGE_REQUEST_ID}",
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
                    "hidden_metadata": {"external_case_id": "CASE-1234"},
                    "status": "completed",
                    "result_summary": "Use the checklist.",
                    "answer": {
                        "status": "resolved",
                        "answer_text": "Use the checklist.",
                        "answer_context_resources": [
                            {
                                "project_id": PROJECT_ID,
                                "module": "unstructured",
                                "resource_id": KNOWLEDGE_ITEM_ID,
                                "uri": (
                                    f"valmar://context/{PROJECT_ID}/unstructured/"
                                    f"{KNOWLEDGE_ITEM_ID}"
                                ),
                            }
                        ],
                        "save_answer_as_unstructured": False,
                        "source_member_ids": [MEMBER_ID],
                    },
                    "created_by_actor_id": "machine:test",
                },
            )

        client = build_client(httpx.MockTransport(handler))
        handle = client.context_requests.create(
            "How do releases work?",
            requesting_application="test-agent",
            hidden_metadata={"external_case_id": "CASE-1234"},
        )
        request = client.context_requests.get(handle.context_request_id)

        self.assertEqual(handle.context_request_id, UUID(KNOWLEDGE_REQUEST_ID))
        self.assertEqual(request.result_summary, "Use the checklist.")
        self.assertEqual(request.hidden_metadata, {"external_case_id": "CASE-1234"})
        self.assertIsNotNone(request.answer)
        assert request.answer is not None
        self.assertEqual(request.answer.source_member_ids, [UUID(MEMBER_ID)])
        self.assertEqual(
            paths,
            [
                "/api/context/requests",
                f"/api/context/requests/{KNOWLEDGE_REQUEST_ID}",
            ],
        )

    def test_list_knowledge_requests_and_import_people(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/context/requests":
                return httpx.Response(
                    200,
                    json=[
                        {
                            "id": KNOWLEDGE_REQUEST_ID,
                            "project_id": PROJECT_ID,
                            "requesting_application": "admin-ui",
                            "question": "Where is the policy?",
                            "hidden_metadata": {"external_case_id": "CASE-1234"},
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

        requests = client.context_requests.list()
        result = client.people.import_bulk(
            [CreatePersonInput(email="ada@example.com", display_name="Ada Lovelace")]
        )

        self.assertEqual(requests[0].question, "Where is the policy?")
        self.assertEqual(
            requests[0].hidden_metadata,
            {"external_case_id": "CASE-1234"},
        )
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
        assignment = client.context_requests.assign(
            KNOWLEDGE_REQUEST_ID,
            member_id=MEMBER_ID,
            reason="Manual assignment.",
        )

        self.assertEqual(
            seen_path,
            f"/api/context/requests/{KNOWLEDGE_REQUEST_ID}/assignments",
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

        self.assertFalse(hasattr(client.context_requests, "synthesize"))
        self.assertFalse(hasattr(client.context_requests, "ignore_synthesis"))
        self.assertFalse(hasattr(client.context_requests, "exclude_assignment_from_synthesis"))


if __name__ == "__main__":
    unittest.main()
