# Known Limitations

This build intentionally covers six routes out of the sixty legal
entities in the regulator's seed dataset, in line with the brief's
stated preference for a smaller set of trustworthy results over a
large set of unverifiable ones. Specific gaps:

**Market coverage**
Only one route per channel type is exercised end to end (one direct
writer, one aggregator, one broker, one affinity program, one
residual-market log entry). The remaining direct writers, mutuals,
MGAs, and specialty programs listed in Appendix A are not attempted.
Extending coverage would mean adding registry entries and letting the
same adaptive form-mapping logic run against each new site; the
architecture does not require new code per site, only new registry
records and, likely, tuning of the field-mapping prompt.

**Voice/phone routes**
No voice agent is implemented. Routes that resolve to a phone-only
path (several broker and MGA routes fall into this category) are
logged as `callback_required` with the phone number captured as
evidence, rather than actually placing a call. This is a conscious
scope decision given the one-day build window; a Twilio-based
implementation following the brief's suggested call-opening script
would be the natural next step.

**Premium extraction accuracy**
The regex-based premium detector on final quote pages is a first pass
and has not been validated against every route's actual results-page
wording, since this container could not reach live insurer sites
during development. It should be verified and likely tuned against
each real results page during the event.

**Coverage-benchmark comparability**
The system records whether a premium was found, and defaults to
`quoted_non_comparable` pending human confirmation that the returned
coverage actually matches the demo benchmark (Section 6 of the brief).
Automated matching of every optional benefit and endorsement against
the benchmark is not implemented; this is flagged as a manual
verification step rather than silently assumed.

**Deduplication**
Deduplication currently works by matching `distinct_rate_source_id` as
recorded in the registry ahead of time. It does not yet cross-check
the legal underwriter name actually returned by a broker/aggregator
panel against the registry to catch previously-unknown duplicates
discovered live. That cross-check is listed as a next step.

**Form-field mapping**
The Claude-based field mapper is a best-effort layer, not a guarantee.
It is deliberately conservative (defaults to `null`/no-fill on
uncertain matches) but has not been tested against the six chosen
sites' actual DOM structure, since this development environment has no
outbound access to those sites. Verification and possible prompt
tuning against each real site is expected as the first task at the
event.

**Estimate-only mode default**
By default the system runs in `estimate_only` mode, which avoids
submitting any real identity information. This means the build as
submitted demonstrates market discovery, routing, guardrails, and
evidence capture, but does not by itself demonstrate a completed live
quote with a real applicant profile unless explicitly switched to
`live` mode with consent recorded.
