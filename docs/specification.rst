Open Decisions data specification
=================================

Version: 0.1.0. Status: draft.

Scope and terminology
---------------------

Open Decisions defines a vendor-neutral JSON record for a choice among
alternatives. A record describes a decision, not merely an event, prediction,
model response, or executed action. A recommendation awaiting authorization
is not yet a decided outcome. Decisions can select multiple options.

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, and MAY are
interpreted as described in RFC 2119 and RFC 8174 when capitalized.
Requirements apply to producers, consumers, and relays as explicitly stated.
The JSON Schema and this document are both normative: structural validation
alone does not establish conformance. If they disagree, the draft has a defect
that must be resolved, rather than an implementation-specific interpretation.

The format is independent of transports, programming languages, model
providers, and storage systems. It does not prescribe a decision algorithm,
explainability method, authorization model, digital signature, SDK, or OTLP
signal. It provides evidence of reported activity, not proof that a choice
was correct, authorized, fair, or actually executed.

Encoding and common types
-------------------------

* A record MUST be a single UTF-8 JSON object conforming to RFC 8259 and the
  schema in ``schema/0.1.0/decision.schema.json`` (JSON Schema Draft 2020-12).
  JSON member names MUST be unique within each object. Comments, NaN,
  infinity, and trailing commas are forbidden.
* Field names and enum values are case-sensitive. Objects are unordered.
  Array order is retained, but MUST NOT imply ranking, chronology, or
  precedence unless a field explicitly says so.
* Unknown core fields MUST be rejected for this schema version at every
  object level. Vendor data MUST use a defined ``attributes`` map or the
  top-level ``extensions`` map. Unknown extension keys MUST NOT cause a
  core-conformant consumer to reject a record.
* Omit absent optional fields. ``null`` is allowed only inside metadata
  values; it means an explicitly null application value, not an unknown core
  field. Empty arrays mean no entries are reported, not necessarily none
  existed. A zero counter means a measured zero; omit an unknown counter.
* ``text`` is a nonempty Unicode string. Producers SHOULD avoid
  whitespace-only text. Text is untrusted data, not executable markup.
* ``id`` is an ASCII string of 1–256 characters, beginning with an
  alphanumeric character and continuing with alphanumerics or ``._:/@-``.
  IDs are opaque and case-sensitive; consumers MUST NOT normalize them.
  Decision IDs MUST be globally unique; UUID URNs are RECOMMENDED.
  Actor IDs SHOULD be stable pseudonymous identifiers, not email addresses.
* Timestamps MUST be RFC 3339 date-times with an explicit UTC offset.
  Producers SHOULD use UTC with ``Z`` and SHOULD avoid leap-second values
  for portability. Consumers MUST compare instants, not timestamp strings.
  No fixed subsecond precision is required.
* Integers and counters MUST be within the inclusive range
  -9007199254740991 to 9007199254740991; counters are nonnegative.
  All JSON numbers, including nested metadata, MUST be finite and within
  that magnitude. Applications needing larger exact numbers MUST encode
  them as strings in metadata and document their interpretation.
  Binary floating-point round trips are not guaranteed to preserve decimal
  precision; exact financial quantities SHOULD use documented decimal strings.
* An ``attributes`` or ``extensions`` map has namespaced lowercase keys:
  two or more dot-separated segments, each starting with ``a``–``z`` and
  continuing with ``a``–``z``, digits, ``_``, or ``-``; maximum 256 characters.
  Values can recursively contain JSON strings, numbers, booleans, null,
  arrays, and objects. Nested value-object keys are unrestricted.

Record envelope
---------------

The following fields are REQUIRED.

``schema_version``
  Exactly ``0.1.0``. Identifies the complete wire contract, not the producer
  version or the decision revision.
``id``
  Globally unique identity of the logical decision, retained across revisions.
``revision``
  Positive integer snapshot sequence allocated by the decision's owner.
``time``
  Time this revision became true in the source system (event time), not
  transport or export time.
``name``
  Stable, low-cardinality decision category such as ``support.route``.
  MUST remain unchanged across revisions. MUST NOT embed request IDs,
  user identifiers, or free-form questions.
``kind``
  ``human``, ``automated``, ``ai``, or ``hybrid``; see actor classification.
``status``
  ``proposed``, ``decided``, ``deferred``, ``abstained``, or ``failed``.
``resource``
  Source application or service responsible for reporting the decision.
  Required ``service_name`` is its logical service name; optional
  ``service_namespace`` groups services and optional ``service_instance_id``
  identifies an instance. Optional ``attributes`` describe deployment context.
  The resource is not necessarily the decision maker.
``instrumentation_scope``
  Reporting library/adapter identity: required ``name`` and optional
  ``version`` and ``attributes``. This is not the agent or model identity.
``actors``
  Nonempty collection of participating entities, defined below.
``decision``
  Question, alternatives, and result, defined below.

The following envelope fields are OPTIONAL.

``observed_time``
  Time the source instrumentation first observed this revision. It can differ
  from ``time`` because of clock skew or delayed collection. It is part of
  the immutable snapshot; relays MUST NOT replace it with their receipt time.
``context``
  Optional ``trace_id``, ``span_id``, and ``correlation_id``. Trace IDs are
  exactly 32 lowercase hexadecimal characters, span IDs exactly 16, and
  neither may be all zeros. ``span_id`` requires ``trace_id``.
  ``correlation_id`` is an application-specific opaque ID, not a decision
  reference or a substitute for a trace ID.
``links``
  Decision relationships, defined below.
``ai``
  Model invocation metadata, defined below; REQUIRED for ``kind: ai``.
``governance``
  Optional policy evaluations and approvals, defined below.
``attributes``
  Namespaced supplemental facts about this decision snapshot.
``extensions``
  Namespaced structured payloads with independently documented contracts.

Actors and decision kind
------------------------

Each actor has REQUIRED ``id``, ``type``, and ``roles``; optional ``name``,
``version``, and ``attributes``. ``type`` is one of:

* ``human``: an individual human.
* ``organization``: a collective accountable body, such as a review board.
* ``service``: deterministic or non-agent software automation.
* ``ai_agent``: a software agent using a learned model to contribute to a
  decision. The model itself is not a separate actor.

``roles`` is a nonempty set drawn from ``proposer`` (suggests alternatives or
a recommendation), ``decider`` (selects or is assigned authority to select),
``reviewer`` (assesses), ``executor`` (carries out a choice), and ``observer``
(records or watches). One entity may have multiple roles.

Actor IDs MUST be unique within a snapshot. Every snapshot MUST contain at
least one actor with the ``decider`` role; for pending decisions this is the
assigned decision maker, not a claim that a selection has already occurred.
Multiple deciders indicate shared participation, not voting weights.

Classification considers actors with ``proposer`` or ``decider`` roles:
``human`` means only humans/organizations; ``automated`` means only services;
``ai`` means only AI agents; ``hybrid`` means at least two of those categories.
Observers, reviewers without a proposer/decider role, and executors do not
change this classification. For example, AI recommendations accepted by a
human are ``hybrid``, not ``ai``.

Whenever an AI agent has a proposer/decider role, ``ai`` metadata MUST be
present with at least one invocation referring to that actor. Record an
invocation's completed, failed, or cancelled result before claiming that it
contributed. Work still in progress need not yet list that agent as a
contributor. AI reviewers MAY also have invocation metadata.

Decision payload
----------------

``question`` (REQUIRED)
  The concrete question being answered. Avoid confidential source content.
``options`` (REQUIRED)
  An array of alternatives. Each has REQUIRED ``id`` and ``label`` and
  optional ``description`` and ``attributes``. IDs MUST be unique within the
  snapshot. The same option ID across revisions MUST retain the same meaning.
  Alternatives need not exhaust the real-world possibility space; producers
  SHOULD report all alternatives actually considered when safe.
``selected_option_ids``
  REQUIRED and nonempty for ``decided``; MUST be absent for every other status.
  Each ID MUST match exactly one option in this snapshot; no duplicates.
  Multiple IDs mean a set of selected options, not a ranking. A rejection or
  "do nothing" choice MUST be modeled as an explicit option, not an empty
  selection. ``decided`` requires at least one option.
``reason``
  Optional concise, disclosure-safe explanation of the result or current
  status. It MUST NOT be represented as a private model reasoning trace.
``criteria``
  Optional array of evaluation criteria with REQUIRED unique ``id`` and
  ``description`` and optional ``weight`` and ``attributes``. Weight is a
  relative importance in [0, 1], not a score or probability. Weights need not
  sum to one; omission means unknown/unweighted. Core defines no scoring
  algorithm; document scores in namespaced option attributes.
``evidence``
  Optional array of evidence references with REQUIRED unique ``id`` and
  absolute ``uri`` (RFC 3986), optional ``description``, ``media_type``,
  ``sha256``, and ``attributes``. A digest is 64 lowercase hexadecimal
  characters over the referenced artifact's exact bytes, not a signature.
  Omit it if unavailable. Versioned or content-addressed artifacts are
  RECOMMENDED. Merely referencing evidence does not prove it was read or
  trustworthy. Evidence MUST NOT be fetched automatically during validation.
``confidence``
  Optional object with REQUIRED ``value`` in [0, 1], nonempty ``method``,
  and ``assessed_by`` referencing an actor in this snapshot. Confidence is a
  reported estimate about the decision, not necessarily a calibrated
  probability. Method SHOULD identify self-reporting versus a calibrated
  estimator and its version. Omit if unknown; consumers MUST NOT infer
  confidence from model token probabilities or treat different methods as
  comparable by default.
``error``
  REQUIRED only for ``failed`` and forbidden otherwise. Has REQUIRED
  stable ``code``, optional safe ``message``, and optional boolean
  ``retryable``. It describes failure to reach a decision, not failure to
  execute an already selected action.

Lifecycle, identity, and revisions
----------------------------------

``proposed``
  Under consideration; no authoritative choice has been made.
``deferred``
  Intentionally postponed, possibly pending more evidence or approval.
``decided``
  One or more alternatives were authoritatively selected.
``abstained``
  Deliberate refusal to choose. This differs from selecting a "reject" option.
``failed``
  The decision process could not complete, with a structured error.

A record is a full immutable snapshot, never a patch. The first emitted
revision MUST be 1. A single logical owner MUST allocate subsequent revisions
as consecutive increasing integers, serializing concurrent writers. Multiple
reporting libraries for one owner MUST coordinate allocation. Independent
systems unable to coordinate MUST use distinct decision IDs and links.

Revisions in ``proposed`` or ``deferred`` MAY move to any status, including the
same status. ``decided``, ``abstained``, and ``failed`` are terminal: later
revisions MAY correct or add descriptive metadata but MUST preserve terminal
status, selected option IDs (as a set), and their meaning. A new choice,
reversal, or retry after terminal failure MUST use a new decision ID, linked
to its predecessor. Execution failure MUST NOT turn a ``decided`` record
into ``failed``. Describe execution outcomes in external telemetry or a
namespaced extension on a new revision.

The question's underlying meaning MUST remain the same across revisions.
Changing the decision problem requires a new ID. Revision 2 of the hybrid
example is a full snapshot of revision 1's decision after human approval;
it is not a second invocation of the agent.

The deduplication coordinate is the pair (``id``, ``revision``).
Re-delivery of an identical JSON value at that coordinate is idempotent;
member ordering and insignificant number formatting do not matter.
Different content at an existing coordinate is a conflict: consumers MUST
flag and quarantine the conflicting input rather than silently overwrite.
Collectors MUST NOT enrich a snapshot in place. Keep collector metadata
outside the record, or ask the owner to emit a new revision.

Consumers MUST tolerate out-of-order delivery, repeated delivery, and missing
revisions. They MUST NOT infer absence of a decision from missing data.
The highest accepted revision is the latest known snapshot, not proof the
history is complete. ``time`` and ``observed_time`` MUST NOT override revision
ordering. Gaps MAY trigger retrieval or an incomplete-history warning.
Concurrent same-coordinate variants are conflicts, not last-writer-wins.

Decision links
--------------

Each link contains REQUIRED ``decision_id`` and ``relationship``, optional
positive ``revision`` and optional ``attributes``. Relationships are directed
from the current decision to the target:

* ``caused_by``: target triggered this decision.
* ``derived_from``: target's outcome informed this decision.
* ``supersedes``: this decision replaces the target.
* ``related_to``: association without stronger semantics.

An explicit revision pins the target snapshot. An omitted revision refers
only to the logical decision, NOT to an implicitly resolved "latest" snapshot.
Consumers MUST NOT pretend such a reference is immutable evidence of a
particular outcome. Producers SHOULD pin revisions for causal or audit links.
Unresolved links are permitted: target delivery or access is not guaranteed.
An identical target/revision/relationship tuple MUST NOT occur twice.
Links to the same logical decision MUST NOT be used to encode revision
history; revision numbers already do that. Thus self-links are forbidden.
Consumers MUST handle cycles between different decisions without unbounded
traversal; cross-record cycle detection is not a core validation requirement.

AI provenance
-------------

``ai.invocations`` is a nonempty array of distinct model calls, not an
ordered transcript. Each invocation has:

* REQUIRED ``id`` unique within the snapshot, ``actor_id`` resolving to an
  ``ai_agent`` actor, and ``purpose``: ``generation``, ``evaluation``,
  ``selection``, ``approval``, or ``other``.
* REQUIRED ``status``: ``completed``, ``failed``, or ``cancelled``. A failed
  invocation can precede a successful decision through fallback or human
  intervention; invocation status is independent of decision status.
* REQUIRED ``provider`` (deployment/provider identity, including local
  inference) and ``model`` with REQUIRED ``name`` and optional ``version``
  and ``requested_name``. Name/version describe the actual model when known;
  requested_name records a request alias. If the provider exposes no resolved
  name, use the reported alias as name and omit the unknown version.
  Producers MUST NOT fabricate provider/model provenance.
* Optional ``started_at`` and ``ended_at`` timestamps; when both are present,
  end MUST NOT precede start. These times concern the model call, not the
  whole decision workflow.
* Optional ``parameters``: namespaced metadata such as
  ``gen_ai.request.temperature``. Use explicit safe generation settings,
  template identifiers, and retrieval configuration, not raw messages.
* Optional ``usage`` with nonnegative integer ``input_tokens``,
  ``output_tokens``, ``cached_input_tokens``, and
  ``reasoning_output_tokens``. Cached tokens are a subset of input tokens;
  reasoning tokens are a subset of output tokens. When both relevant
  counters are present, the subset MUST NOT exceed the total. Omit counters
  if the provider reports incompatible accounting. Tokens are provider
  reported, not comparable units of cost across models.
* Optional ``tools`` array with unique per-invocation ``id``, ``name``,
  ``status`` (``completed``, ``failed``, or ``cancelled``), optional nonnegative
  ``duration_ms``, and ``attributes``. Tool records describe calls associated
  with this invocation, not independent decision approvals. Arguments and
  results are intentionally not core fields.
* Optional ``attributes`` for other namespaced invocation facts.

The same invocation appearing in multiple revisions retains its identity and
meaning; its inclusion is not a new call or new token expenditure.
Consumers aggregating usage across snapshots MUST deduplicate by decision ID
and invocation ID. Calls shared across different decisions SHOULD use an
external stable call identifier in metadata so aggregators can avoid double
counting across decisions as well.

Provenance is not a replay guarantee: stochasticity, provider changes,
unavailable evidence, and unrecorded sensitive inputs may prevent reproduction.

Governance
----------

``governance.policies`` is an optional array of evaluations with REQUIRED
unique ``id`` and ``result`` (``pass``, ``fail``, or ``unknown``), optional
``version``, ``evidence_ids``, and ``attributes``. Evidence IDs MUST resolve
to entries in ``decision.evidence`` and be unique within each evaluation.
One entry per policy identity is permitted per snapshot; represent distinct
evaluations using distinct IDs. A policy result is a report, not enforcement.

``governance.approvals`` is an optional array with REQUIRED ``actor_id``
and ``status`` (``approved``, ``rejected``, or ``pending``), optional ``time``
and ``reason``. Actor IDs MUST resolve to a listed actor with ``reviewer``
or ``decider`` role. Only one entry per actor is permitted per snapshot.
Time, if present, is when this approval status became true. Pending,
rejected, and failed policy checks do not automatically change decision
status: the producer's authority model determines whether a decision can
be made despite them. Consumers MUST NOT interpret ``decided`` alone as
proof all applicable approvals or policies passed.

Extension and version policy
----------------------------

The ``od`` namespace is reserved for future Open Decisions conventions.
Producers MUST NOT invent keys in it. Vendor namespaces SHOULD use a
controlled reverse-DNS prefix, such as ``org.example.routing``.
Well-established external conventions (for example ``gen_ai``) MAY retain
their published names. An extension MUST NOT override the meaning of core
fields or make an otherwise invalid core record valid.

Extensions SHOULD document value types, units, enum vocabularies, privacy
classification, and their own version strategy. Core consumers MAY ignore
extension semantics; lossless relays MUST preserve their JSON values.
If an application requires a specific extension to function, negotiate that
application profile outside the core format.

Every wire-contract change, including optional core fields or enum additions,
requires a new ``schema_version`` and schema path. Released version paths
MUST NOT be repurposed. Editorial corrections that do not alter the accepted
data or semantics MAY update documentation without a new schema.
The current draft may evolve until release. No compatibility across 0.x
versions is promised. For stable 1.x releases, breaking semantic changes
require a major version; additive contracts use a minor version and
non-wire corrections a patch version.

Because the core is closed, consumers MUST validate with the exact supported
version. A consumer MUST NOT silently accept an unknown version using a
different schema or discard unknown core fields to force compatibility.
It MAY reject, quarantine, or relay an opaque unsupported record without
claiming conformance. Migrations MUST be explicit and retain provenance;
they are not an excuse to overwrite an existing immutable snapshot.

Conformance
-----------

A conformant producer MUST emit structurally valid records and satisfy all
record-local and cross-revision MUST requirements above. A conformant
consumer MUST assert ``date-time`` and ``uri`` formats during schema
validation, perform record-local semantic checks, and enforce history rules
when the relevant revisions are available. A relay claiming losslessness
MUST preserve the record JSON value, including extensions.

JSON Schema cannot enforce ID uniqueness by one property, foreign-key
references, kind/actor classification, time ordering, subset token counts,
or cross-revision invariants. Implementations MUST NOT label schema-only
validation as full conformance. See ``integration.rst`` for a validation
checklist and positive/negative semantic test vectors.
