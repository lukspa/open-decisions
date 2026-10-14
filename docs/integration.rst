Integration and conformance guide
=================================

This guide explains use of the draft 0.1.0 contract. Requirements explicitly
marked MUST in the specification remain normative; transport choices below
are recommendations, not a standardized network API.

Producer workflow
-----------------

1. Identify the actual decision boundary, assigned decision maker, alternatives,
   and whether the result is a recommendation or an authoritative choice.
2. Assign a globally unique ID and one logical revision owner. Use a stable
   low-cardinality name and identify the source resource and reporting scope.
3. Emit revision 1 as a complete snapshot. Subsequent revisions include all
   still-relevant fields, not only changed fields. Capture event time at the
   source, not when retrying delivery.
4. Include only disclosed, necessary metadata. Use pseudonymous actors and
   references to controlled evidence rather than copied sensitive inputs.
5. For AI contributions, include the actor, model call purpose, provider/model
   provenance, and known usage. Separate the proposing agent from a human
   approver. Do not assume model output means a decision was authorized.
6. Validate the schema with format assertions, then semantic invariants.
   Publish using a deployment-specific secure transport and retry the exact
   same snapshot after uncertain delivery.

Consumer workflow
-----------------

1. Authenticate the producer and establish tenant/owner boundaries outside
   the record; no field in this format is an authentication credential.
2. Apply byte, depth, member-count, and string limits before expensive parsing.
   Reject duplicate JSON object keys rather than using last-key-wins parsing.
3. Inspect ``schema_version`` and select a locally trusted, supported schema.
   Never fetch schemas or evidence from arbitrary URLs in the incoming record.
4. Validate JSON Schema Draft 2020-12 with ``date-time`` and ``uri`` format
   assertions enabled. Some validators treat ``format`` as annotation only.
5. Perform all local semantic checks listed below.
6. Store by authenticated ownership context plus the (ID, revision)
   coordinate, check duplicate conflicts, and apply available history checks.
   The extra ownership context protects isolation; it does not relax the
   producer requirement that decision IDs be globally unique.
7. Retain out-of-order snapshots and identify gaps. Project latest known
   state using the highest accepted revision, not arrival order.
8. Index known core fields; preserve unknown extension values when relaying.
   Keep rejected records in an access-controlled quarantine with safe errors.

Validation checklist
--------------------

Structural assertions (covered by the repository schema tests):

* Required envelopes, closed core objects, exact schema version and enums.
* Positive bounded revisions, nonnegative bounded counters, bounded confidence.
* Selected choices required only for ``decided``; errors only for ``failed``.
* Nonempty AI invocations required for ``kind: ai``.
* RFC 3339 dates, absolute evidence URIs, trace/span ID shapes.
* Namespaced metadata keys and recursive interoperable JSON values.

Local semantic assertions (implement in an adapter or service; not supplied
as an SDK in this repository):

* Unique actor, option, criterion, evidence, policy, and invocation IDs in
  their documented scopes; unique tool IDs inside each invocation.
* At least one ``decider``; correct kind based on proposers and deciders.
* Every selected ID exists exactly once among options.
* Confidence assessor exists; invocation actor exists and is ``ai_agent``.
* Every contributing AI agent has a recorded invocation, including in hybrid
  workflows. Non-contributing AI reviewers do not force a hybrid kind.
* Policy evidence references exist; approval actors exist with reviewer or
  decider roles; no duplicate approval actors.
* Invocation end is not before start; cached-input and reasoning-output
  subsets do not exceed their corresponding known totals.
* No self-links or repeated target/revision/relationship link tuples.
* No invented ``od``-namespace metadata conventions.

History assertions when prior snapshots are available:

* Revisions are consecutively allocated at the owner; a downstream consumer
  can accept gaps while flagging an incomplete history.
* Same coordinate plus same JSON value is a duplicate; different content is
  a conflict, never a silent overwrite.
* Stable name, logical question meaning, retained option meanings, and
  retained invocation identities.
* Allowed lifecycle transitions and immutable terminal choices.
* New invocations are counted once, not once per repeated full snapshot.

Some semantic checks (such as whether prose describes the same question)
require application knowledge rather than a generic validator.

Conformance test vectors
------------------------

Start with the indicated valid example, make the described change, and
expect the stated result. These vectors are normative illustrations, not
an exhaustive executable semantic validator.

* ``minimal.json`` unchanged: accept.
* ``automated.json`` unchanged: accept the multi-selection as an unordered set.
* ``ai-agent.json`` unchanged: accept with self-reported, uncalibrated confidence.
* ``hybrid-proposed.json`` followed by ``hybrid-decided.json``: accept as
  consecutive snapshots of one decision; count the model call only once.
* ``minimal.json`` with selected ID ``missing-option``: reject semantically,
  even though the JSON Schema accepts it.
* ``minimal.json`` with two different actors sharing ``operator:17``:
  reject semantically.
* ``minimal.json`` with the only actor's role changed to ``observer``:
  reject semantically.
* ``ai-agent.json`` with invocation actor ``missing-agent``: reject semantically.
* ``ai-agent.json`` with ``kind`` changed to ``human``: reject semantically.
* ``ai-agent.json`` with 500 cached input tokens and 420 input tokens:
  reject semantically, although both numbers are structurally valid.
* ``ai-agent.json`` with the end time preceding the start time:
  reject semantically.
* ``hybrid-proposed.json`` without ``ai``: reject semantically. The structural
  schema only requires ``ai`` unconditionally when kind itself is ``ai``.
* ``minimal.json`` delivered twice with different whitespace/key ordering:
  accept once and deduplicate the second delivery.
* ``minimal.json`` with changed reason but unchanged ID/revision, after the
  original was stored: quarantine as a conflict.
* ``hybrid-decided.json`` arriving before ``hybrid-proposed.json``: accept
  revision 2 as latest known, flag a history gap, then fill it on revision 1.
* A revision 3 of ``hybrid-decided.json`` selecting ``reject`` instead:
  reject as an invalid terminal-choice mutation. Use a new linked decision.
* ``failed.json`` with a self-link: reject semantically.

Transport and storage
---------------------

Use ``application/json`` for a single record. There is no registered
Open Decisions media type, mandated HTTP endpoint, batch envelope, or
delivery guarantee. For files containing many records, deployments MAY agree
on UTF-8 newline-delimited JSON (one compact record per line; escaped newlines
inside strings). For HTTP batches they MAY agree on JSON arrays.
These are local transport profiles, not additional schema entry points.
Validate each record separately and document partial-failure behavior.

Deployment agreements should define authentication, encryption, tenant
isolation, producer ownership, size limits, retention, batching, retry
backoff, and acknowledgement semantics. An acknowledgement should clearly
distinguish durable acceptance from mere receipt. At-least-once delivery with
coordinate-based deduplication is a useful baseline; the format does not
provide exactly-once delivery.

Store complete snapshots to preserve history, with a separate latest-state
projection if useful. Protect against an unauthorized producer racing to
claim an ID; a self-declared resource or actor is not ownership evidence.
Do not overwrite originals when normalizing timestamps, migrating versions,
redacting for export, or adding collector receipt metadata. Keep derived
views separate and identifiable; a shared coordinate always names the
original snapshot, not a rewritten variant.

OpenTelemetry interoperability
------------------------------

The resource/scope split and trace correlation intentionally resemble
OpenTelemetry. Open Decisions is nevertheless a separate JSON data model,
not a fourth official OpenTelemetry signal. A trace/span association is
optional; not every business decision occurs in an instrumented request.

An adapter can correlate a record with an existing span using ``context``
and can publish a log or span event containing a decision ID, revision,
status, and a controlled record reference. The full record is usually better
stored in a dedicated sink than copied into every span attribute.
Do not use decision IDs or questions as metric dimensions.

The following is an informative mapping, not a declaration of byte-for-byte
OTLP compatibility. Pin the upstream semantic-convention version used by an
adapter because GenAI conventions evolve.

* ``resource.service_name`` maps to resource attribute ``service.name``.
* ``resource.service_namespace`` maps to ``service.namespace``.
* ``resource.service_instance_id`` maps to ``service.instance.id``.
* ``instrumentation_scope.name`` and ``version`` map to InstrumentationScope
  name and version, not resource attributes.
* ``context.trace_id`` and ``span_id`` map to the existing trace/span context;
  preserve their bytes and do not create a fictitious remote parent.
* ``ai.invocations[].provider`` maps to ``gen_ai.provider.name`` when its
  upstream meaning matches; otherwise document a deployment-specific mapping.
* ``model.requested_name`` maps to ``gen_ai.request.model``;
  actual ``model.name`` maps to ``gen_ai.response.model``.
  Do not substitute a requested alias as a known resolved response model.
* ``usage.input_tokens`` and ``output_tokens`` map to
  ``gen_ai.usage.input_tokens`` and ``gen_ai.usage.output_tokens``.
  Cached/reasoning breakdowns, model version, tool records, and decision
  confidence require an explicitly versioned mapping; this draft does not
  assert a universal upstream attribute for them.

Open Decisions metadata permits nested JSON and nulls. These are not
universally representable as OpenTelemetry attributes. Adapters MUST NOT
claim lossless conversion without an encoding contract. Prefer exporting
selected compatible scalar attributes plus a record reference; if JSON is
encoded in a string, document that encoding and its size/truncation limits.
Duplicate semantic fields MUST NOT disagree with authoritative core fields.

References
----------

* JSON: https://www.rfc-editor.org/rfc/rfc8259
* Requirement language: https://www.rfc-editor.org/rfc/rfc2119 and
  https://www.rfc-editor.org/rfc/rfc8174
* Timestamps: https://www.rfc-editor.org/rfc/rfc3339
* URIs: https://www.rfc-editor.org/rfc/rfc3986
* JSON Schema: https://json-schema.org/draft/2020-12
* OpenTelemetry: https://opentelemetry.io/docs/specs/otel/
* GenAI conventions:
  https://opentelemetry.io/docs/specs/semconv/gen-ai/
