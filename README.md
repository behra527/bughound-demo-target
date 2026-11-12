# BugHound Demo Target

**Repository:** `bughound-demo-target`  
**Purpose:** A deliberately bug-seeded Flask REST API to evaluate BugHound's investigation, root-cause analysis, patch generation, and CI test-verification workflow.

> **Important:** This repository intentionally contains **exactly three application defects**. The initial test failures are expected and must **not** be hidden with `xfail`, skipped tests, or weakened assertions. It is a safe, self-contained test target—not a production task manager.

## Overview

The API provides a minimal in-memory task manager with task creation, listing, lookup by ID, partial updating, deletion, title validation, and a boolean completion flag. Each application instance starts with an empty task store and IDs beginning at `1`. Data is intentionally ephemeral: stopping the process discards tasks. No database, cloud service, API key, or external network call is required at runtime.

**Stack:** Python 3.12+, Flask, pytest, and Python's standard library. Compatible with GitHub Actions runners and BugHound's own CI verification workflow. No GitHub Actions workflow is committed here.

## Architecture

```text
bughound-demo-target/
├── app/
│   ├── __init__.py         # Flask app factory; per-instance task service
│   ├── routes.py           # REST endpoints, JSON request/response and status codes
│   ├── services.py         # In-memory CRUD and completion state
│   └── validators.py       # Payload, title and boolean validation
├── tests/
│   ├── test_tasks.py       # End-to-end HTTP tests using Flask's test client
│   └── test_validation.py  # Validation contract tests
├── run.py                  # Start the Flask development server
├── requirements.txt       # Minimal app and test dependencies
├── README.md
└── .gitignore
```

**Request path:** HTTP request → Flask route → `TaskService` → validators / in-memory dictionary → JSON response. Tests use Flask's built-in test client, so they do not need a running HTTP server or network access.

## Install

From the directory containing this `README.md`, create an isolated environment. Python **3.12 or newer** is required.

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If `py -3.12` is not available, use `python -m venv .venv` with an installed Python 3.12+ interpreter.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the API

```bash
python run.py
```

The API listens on **http://127.0.0.1:5000**. Use `Ctrl+C` to stop it. This is a local demonstration server, not a production deployment configuration.

## Run the tests

From the repository root, with dependencies installed:

```bash
python -m pytest -q
```

**Expected initial outcome:** **3 failed, 44 passed**. The three deliberately failing tests are:

- `tests/test_tasks.py::test_empty_and_whitespace_titles_are_rejected` — BUG-001
- `tests/test_tasks.py::test_get_task_returns_exact_matching_id` — BUG-002
- `tests/test_tasks.py::test_update_completion_to_false_persists` — BUG-003

All other tests should pass. The process exits with status code `1` while bugs remain, which is intentional: BugHound's validation pipeline can use those failures as an objective repair signal. After all three fixes, every test should pass without modifying the tests.

CI runners can execute the same two commands:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

## API reference

All request bodies are JSON objects. Task titles are strings of **1–120 non-whitespace characters after trimming** (intended contract). `completed` must be a JSON boolean, not a string or number. Unknown fields are rejected. IDs are positive integers assigned sequentially. Responses use JSON, except for successful deletion (empty body).

| Method | Endpoint | Purpose | Successful response |
|---|---|---|---|
| `POST` | `/tasks` | Create a task; `title` required, `completed` optional (defaults to `false`) | `201 Created` + task |
| `GET` | `/tasks` | List tasks and count | `200 OK` + collection |
| `GET` | `/tasks/<id>` | Retrieve the task with the exact ID | `200 OK` + task |
| `PATCH` | `/tasks/<id>` | Change `title` and/or `completed` | `200 OK` + updated task |
| `DELETE` | `/tasks/<id>` | Delete a task | `204 No Content` |

Invalid payloads yield `400 Bad Request` with `{"error": "..."}`. Missing tasks yield `404 Not Found` with `{"error": "task not found"}`. Partial updates require at least one permitted field.

### Create

```bash
curl -i -X POST http://127.0.0.1:5000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Write tests"}'
```

`201` response:

```json
{"id":1,"title":"Write tests","completed":false}
```

### List

```bash
curl http://127.0.0.1:5000/tasks
```

`200` response, after creating the task above:

```json
{"count":1,"tasks":[{"id":1,"title":"Write tests","completed":false}]}
```

### Retrieve by ID

```bash
curl -i http://127.0.0.1:5000/tasks/1
```

**Expected** `200` response (once BUG-002 is fixed):

```json
{"id":1,"title":"Write tests","completed":false}
```

**Currently**, `GET /tasks/1` returns `404`, despite the task existing. This is an intentional defect.

### Update

```bash
curl -i -X PATCH http://127.0.0.1:5000/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}'
```

`200` response:

```json
{"id":1,"title":"Write tests","completed":true}
```

Try to reopen it:

```bash
curl -i -X PATCH http://127.0.0.1:5000/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"completed":false}'
```

**Expected:** `"completed":false`. **Actual:** `"completed":true` (BUG-003).

To update the title, send `{"title":"Review PR"}` to the same `PATCH` endpoint.

### Delete

```bash
curl -i -X DELETE http://127.0.0.1:5000/tasks/1
```

Successful deletion returns `204` with no body. Deleting that ID again returns `404`.

### Invalid requests

```bash
curl -i -X POST http://127.0.0.1:5000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"   "}'
```

**Expected:** `400` with an error message. **Actual:** `201` with an empty stored title (BUG-001).

Other invalid payloads, such as `{"title":42}`, `{"completed":"yes"}`, a missing title, and malformed JSON, correctly return `400`.

**Windows PowerShell note:** The multi-line `curl` examples above use Bash quoting and continuation. For PowerShell, use `curl.exe` with appropriate escaping, or `Invoke-RestMethod`, for example:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/tasks -Method Post -ContentType 'application/json' -Body '{"title":"Write tests"}'
Invoke-RestMethod -Uri http://127.0.0.1:5000/tasks -Method Get
```

## Intentionally seeded defects

| ID | Existing source file | Expected behavior | Reproducible current behavior |
|---|---|---|---|
| **BUG-001** | `app/validators.py` (`validate_title`) | Empty and whitespace-only titles yield `400` | A blank string is accepted, normalized to `""` and stored with `201` |
| **BUG-002** | `app/services.py` (`get_task`) | GET returns the task whose ID matches the URL | ID handling is off by one; the first task returns `404`, or a later ID can resolve to a different task |
| **BUG-003** | `app/services.py` (`update_task`) | `PATCH` persists explicit `true` **and** `false` | Updating `true` → `false` leaves the task completed |

Each defect is a real, independent implementation problem, not a test fixture or mock behavior. Retrieval uses a different service method than updating and deleting, so BUG-002 does not prevent exercising BUG-003. Use `GET /tasks` to inspect stored values while the by-ID retrieval is faulty.

## BugHound evaluation procedure

1. Push this directory to a **public GitHub repository** named `bughound-demo-target` (do not upload local virtual environments or caches).
2. Connect that repository in BugHound and select the seeded commit/snapshot.
3. Run `python -m pytest -q` before patching to capture the three independent failures.
4. Investigate and patch **only the relevant application source code**, keeping tests unchanged.
5. Let BugHound execute its isolated GitHub Actions CI workflow against the patched commit/branch. This repository does not contain its own workflow.
6. Confirm all tests pass and review the patch before accepting it.

### Expected repair locations

- **BUG-001:** `app/validators.py` — enforce a nonempty normalized title.
- **BUG-002:** `app/services.py` — correct the task-ID lookup.
- **BUG-003:** `app/services.py` — handle explicit `false` as a valid requested update.

Do **not** change or weaken assertions to mask failures. Do **not** treat the initial nonzero pytest exit status as a broken environment: it is the deliberate BugHound test fixture.

## Safety and limitations

This is intentionally a local, unauthenticated, nonpersistent example. It contains no secrets, external integrations, dangerous operations, database connections, or production deployment infrastructure. Its known behavioral defects are confined to the three cases documented above. Do not deploy this repository as a real task management service.
