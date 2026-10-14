# Open Decisions

An open, vendor-neutral format for reporting **what was decided, by whom, from
which alternatives, and with what supporting context** across applications.
It covers human decisions, deterministic automation, AI agents, and hybrid
workflows.

Like OpenTelemetry standardizes observability data, Open Decisions aims to
standardize decision records. It is an independent project, not an
OpenTelemetry component or an OTLP extension.

## Specification 0.1.0 — draft

- [Normative specification and field reference](docs/specification.rst)
- [JSON Schema (Draft 2020-12)](schema/0.1.0/decision.schema.json)
- [Integration, OpenTelemetry mapping, and conformance](docs/integration.rst)
- [Security, privacy, and deployment guidance](docs/security.rst)

The draft defines a data format, not a hosted service, SDK, collector,
decision engine, or transport protocol. The schema validates structure;
the specification additionally defines semantic validation, ownership,
revision handling, and compatibility.

## Example

```json
{
  "schema_version": "0.1.0",
  "id": "urn:uuid:581d6ebb-255c-4f45-b764-49a6e934ea92",
  "revision": 1,
  "time": "2026-10-14T12:00:00Z",
  "name": "support.route",
  "kind": "human",
  "status": "decided",
  "resource": { "service_name": "support-console" },
  "instrumentation_scope": { "name": "example.support" },
  "actors": [
    { "id": "operator:17", "type": "human", "roles": ["decider"] }
  ],
  "decision": {
    "question": "Which queue should handle this request?",
    "options": [
      { "id": "billing", "label": "Billing" },
      { "id": "technical", "label": "Technical support" }
    ],
    "selected_option_ids": ["technical"]
  }
}
```

Use a globally unique decision ID and start at revision 1. Emit full snapshots,
not patches. Supply an actor with the `decider` role, including for pending
decisions. Unknown optional information is omitted, not guessed.

## Examples

| Record | Demonstrates |
| --- | --- |
| [Minimal](examples/minimal.json) | Required fields and a human selection |
| [Automation](examples/automated.json) | Multiple selections and policy results |
| [AI agent](examples/ai-agent.json) | Model provenance, tool use, token usage, confidence, trace correlation |
| [Hybrid proposal](examples/hybrid-proposed.json) | AI recommendation awaiting human approval |
| [Hybrid decision](examples/hybrid-decided.json) | Full revision-2 snapshot of the same decision |
| [Failure](examples/failed.json) | No selection, structured error, decision link |

Examples are fictional. AI metadata records provenance and a concise
explanation, **not private chain-of-thought, raw prompts, or credentials**.

## Validate and contribute

Python 3.10+ is sufficient for the repository tests. From the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The suite checks the schema, all examples, negative structural cases, URI and
timestamp format checking. It is not a complete semantic validator or SDK.
Implementations must also apply the semantic rules in the specification.

Propose changes with their interoperability rationale, updated documentation,
examples, and positive/negative tests. Before release, the draft may change;
once released, a versioned schema is immutable. Every wire-format change needs
a new schema version. No stability guarantees are made for the 0.x series.

## License

[MIT](LICENSE).
