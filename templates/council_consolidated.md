# Council Consolidated Deliberation

The following council members will each respond to the user's message in sequence. Each member must respond according to their persona and primary lens, drawing on the provided corpus material.

## User Message

> {{ user_message }}

## Relevant Corpus Material

{{ corpus_chunks }}

## Council Members

{% for member in members %}
**{{ member.name }}** — Primary Lens: {{ member.primary_lens }} | Role: {{ member.role_type }}

Persona: {{ member.persona }}

Escalation Rule: {{ member.escalation_rule }}
{% endfor %}

---

## Instructions

For each council member listed above, produce a response block using the exact delimiter format shown below. Do not skip any member. Each block must end with an `ESCALATION:` line indicating either `NONE` or a brief description of the concern requiring escalation.

Respond in the following format for every member, in order:

{% for member in members %}
=== MEMBER: {{ member.name }} ===
[{{ member.name }} responds here, drawing on their persona ({{ member.persona }}), primary lens ({{ member.primary_lens }}), and the corpus material above. The response should be substantive, specific, and grounded in the provided context.]
ESCALATION: [NONE or brief description of escalation concern based on rule: {{ member.escalation_rule }}]
=== END MEMBER ===
{% endfor %}
