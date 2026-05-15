# Support Case Summarizer 🎫

An AI-powered CLI tool that transforms raw support tickets into **structured, actionable summaries** — including severity triage, customer impact, suggested next actions, and missing information gaps.

Runs entirely locally using [Ollama](https://ollama.com). No API keys, no data leaving your machine.

## Demo

```bash
python summarize.py --demo
```

```
============================================================
  SUPPORT CASE SUMMARY
  Generated: 2024-03-15 09:31
============================================================

📌 200 users locked out of production platform due to SAML SSO failure after config update

🔴 Severity: P1  |  Product: SSO / SAML Authentication
   Active outage affecting entire customer support team with direct revenue impact

PROBLEM
----------------------------------------
Following a SSO configuration update, approximately 200 users at Acme Corp are
completely unable to log into the production platform as of 7:45 AM PST. The error
SAML_4021 indicates an audience URI mismatch in the SAML assertion. A revert attempt
on the customer side has not resolved the issue.

CUSTOMER IMPACT
----------------------------------------
Acme Corp's entire customer support team is non-operational, preventing ticket
processing and causing direct revenue impact.

SUGGESTED NEXT ACTION
----------------------------------------
→ Escalate immediately to Tier 2/engineering. Verify SAML audience URI configuration
  on the platform side and check for any backend changes deployed in the last 24 hours.

INFORMATION NEEDED
----------------------------------------
  • Confirm whether the platform received any backend updates overnight
  • Request SAML assertion logs from the customer's IdP
  • Clarify exact timestamp of configuration change vs. onset of errors

KEY ENTITIES
----------------------------------------
  Customer:    Acme Corp (John Smith, IT Director)
  Environment: Production
  Version:     9.4.2
  Error codes: SAML_4021
============================================================
```

## Features

- **Automatic severity triage** (P1–P4) with reasoning
- **Structured output** — one-line summary, problem statement, impact, next action
- **Gap analysis** — flags missing information needed to resolve the case
- **Entity extraction** — customer name, version, environment, error codes
- **3 output formats**: plain text, JSON, Markdown
- **Stdin support** — pipe tickets directly from other tools
- **Fully local** — no data sent to external services

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A pulled model (e.g. `ollama pull llama3.2`)

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/support-case-summarizer.git
cd support-case-summarizer
pip install -r requirements.txt
```

## Usage

```bash
# Run with the built-in demo ticket
python summarize.py --demo

# Summarize a ticket file
python summarize.py ticket.txt

# Output as JSON (for downstream processing / integrations)
python summarize.py --format json ticket.txt

# Output as Markdown (for pasting into Confluence, Jira, etc.)
python summarize.py --format markdown ticket.txt > summary.md

# Pipe from stdin
cat ticket.txt | python summarize.py

# Use a specific Ollama model
python summarize.py --model mistral ticket.txt
```

## Output Fields

| Field | Description |
|-------|-------------|
| `one_line_summary` | Single-sentence TL;DR |
| `problem_statement` | What the customer is experiencing |
| `severity` | P1–P4 with reasoning |
| `affected_product` | Product/feature/component |
| `customer_impact` | Business impact to the customer |
| `suggested_next_action` | Most important next step |
| `information_needed` | Missing details that would help resolution |
| `key_entities` | Customer, environment, version, error codes |

## Integration Ideas

This tool is designed to be a building block. Some ways to extend it:

- **Jira integration**: pipe JSON output into a Jira ticket creation script
- **Slack alerts**: format P1 summaries and post to an on-call channel
- **Batch processing**: loop over a folder of ticket exports for daily triage reports
- **Salesforce**: use the JSON output to auto-populate case fields via API

## Why This Matters

Support engineers spend significant time reading and re-reading tickets before they can act. This tool compresses that to seconds and ensures nothing critical gets missed — severity, impact, and next steps up front, every time.

## License

MIT
