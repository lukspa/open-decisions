Security, privacy, and responsible reporting
============================================

Threat model
------------

Decision records can reveal business strategy, personal data, model inputs,
internal tool names, and authorization relationships. Producers, metadata,
evidence, and AI-generated explanations can be malicious or mistaken.
The JSON Schema checks shape, not truth, consent, authority, or policy
compliance. A record marked ``approved`` or ``pass`` is not an access grant.
Model confidence is not a safety guarantee.

Data minimization
-----------------

* Producers SHOULD default to an allowlist of exported fields and metadata.
  They MUST NOT export credentials, access tokens, private keys, or private
  model chain-of-thought as decision telemetry.
* Do not capture raw prompts, full model responses, tool arguments/results,
  retrieval contents, or customer documents by default. Record template
  IDs, versions, safe concise reasons, token counts, and access-controlled
  evidence references instead. Numeric reasoning-token usage is not a
  reasoning transcript.
* If a deployment needs sensitive source artifacts, store them separately
  with explicit authorization, purpose, retention, and consent/legal-basis
  controls; keep only necessary safe references in the decision record.
* Pseudonymize actor IDs. Avoid names, email addresses, raw account numbers,
  and customer text in decision names, questions, labels, IDs, or attributes.
  Pseudonymous data may still be personal data if linkable.
* Sanitize error messages and reasons at the source. They often accidentally
  contain request bodies, stack traces, filesystem paths, or credentials.
* Evidence URLs MUST NOT include credentials or bearer tokens. Signed URLs
  may leak access and expire before an audit; prefer durable opaque artifact
  references resolved by an authorized service.
* Attribute namespaces and free-form extensions are not security boundaries.
  Apply the same redaction policy recursively to every metadata value.
  Exporters SHOULD flag keys suggesting ``prompt``, ``raw_output``,
  ``chain_of_thought``, ``password``, ``secret``, or ``token`` for review.
  This is a heuristic, not a complete detector: documented numeric usage
  counters are legitimate, and innocuous keys can contain sensitive values.

Ingestion and display
--------------------

Authenticate and authorize each producer independently of declared actors,
resource names, and IDs. Bind ownership and tenant identity to a trusted
transport or ingestion configuration. Encrypt transport and storage,
restrict access by purpose, and audit access to records and evidence.

Consumers MUST treat all strings and extensions as untrusted data. Escape
them when rendering HTML, logs, terminals, queries, or exports. Never execute
tool names, URI contents, model explanations, or extension payloads.
AI-assisted consumers MUST treat record contents as data, not instructions;
evidence can carry prompt injection.

Evidence/schema URIs MUST NOT be automatically dereferenced during
validation. An explicitly authorized resolver should allowlist schemes and
destinations, block private network and metadata endpoints as appropriate,
recheck redirects and DNS resolution, bound response sizes/timeouts, and
avoid forwarding ambient credentials. URI syntax validation alone does not
prevent SSRF, phishing, or malicious content.

Use trusted local schemas with remote reference fetching disabled. This
version's schema uses only internal references; its ``$id`` is an identifier,
not a requirement to perform a network request.

Availability and operational controls
------------------------------------

Bound record size, nesting depth, array lengths, string lengths, metadata
member counts, and evidence-resolution work before expensive processing.
The schema deliberately does not prescribe universal deployment quotas.
Both producer and consumer should agree on limits and reject over-limit
records explicitly rather than silently truncate them.

Rate-limit ingestion and quarantine. Avoid high-cardinality indexing of
arbitrary metadata. Quarantine stores and validation errors require the same
privacy protections as accepted data. Do not echo rejected sensitive payloads
into public logs. Never overwrite a same-coordinate conflict automatically.

Immutability, redaction, and retention
-------------------------------------

Immutability describes the data model, not a legal obligation to retain
personal data forever. Define deletion, retention, and correction procedures
for original records, historical snapshots, derived indexes, exports,
quarantines, and backups. A later revision does not erase earlier disclosure.

Redact before assigning and exporting a revision. If records must later be
redacted for a restricted audience, keep those derived views outside the
canonical coordinate namespace and identify their transformation in the
surrounding delivery/storage profile. Never re-ingest a modified view as
the same canonical snapshot. Required core fields must still be present to
claim record conformance; a projection that removes them is not a conformant
full record. Required deletion may remove the canonical record entirely;
consumers must tolerate missing history.

Tamper evidence and accountability
----------------------------------

The format provides no built-in signatures or canonical JSON signing scheme.
SHA-256 evidence digests identify bytes; they do not authenticate a producer,
prove evidence quality, or prevent replacement of the entire record.
Deployments needing tamper-evident audit logs should use independently
specified authenticated append-only storage or signed transport envelopes
with an explicit canonicalization and key-management policy.

Use human review and domain-specific controls for consequential decisions.
Do not infer fairness, legal compliance, calibration, or permission from the
presence of AI provenance, approvals, or policy results alone.
