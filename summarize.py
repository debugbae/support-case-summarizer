"""
Support Case Summarizer — AI-powered structured summaries of support tickets.

Reads a support ticket from a file or stdin and outputs a structured summary
including: issue, severity, affected product, suggested action, and key entities.

Usage:
    python summarize.py ticket.txt
    python summarize.py --format json ticket.txt
    cat ticket.txt | python summarize.py
    python summarize.py --demo

Output formats: text (default) | json | markdown
"""

import sys
import argparse
import requests
import json
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """You are an expert support engineer assistant. Your job is to read raw support tickets and produce structured, actionable summaries for support teams.

Given a support ticket, extract and return ONLY a JSON object with these exact fields:
{
  "one_line_summary": "A single sentence summarizing the core issue",
  "problem_statement": "2-3 sentences describing what the customer is experiencing",
  "severity": "P1 | P2 | P3 | P4",
  "severity_reason": "One sentence explaining why you assigned this severity",
  "affected_product": "The product, feature, or component involved",
  "customer_impact": "What business impact the customer is experiencing",
  "suggested_next_action": "The most important next step for the support engineer",
  "information_needed": ["List", "of", "missing", "info", "that", "would", "help"],
  "key_entities": {
    "customer_name": "extracted or 'Unknown'",
    "environment": "extracted or 'Unknown'",
    "error_codes": ["any", "error", "codes", "mentioned"],
    "version": "software version if mentioned or 'Unknown'"
  }
}

Severity guide:
- P1: System down, data loss, security breach — immediate response required
- P2: Major feature broken, significant customer impact, workaround unavailable
- P3: Feature degraded, workaround available, moderate impact
- P4: Minor issue, cosmetic, low urgency

Return ONLY valid JSON. No explanation, no markdown fences, just the JSON object."""

DEMO_TICKET = """From: john.smith@acmecorp.com
Date: 2024-03-15 09:23 AM
Subject: URGENT - Users locked out of platform after SSO update

Hi Support,

We are experiencing a critical issue following last night's SSO configuration update
in our production environment. As of approximately 7:45 AM PST, roughly 200 of our
users are completely unable to log into the platform. They are receiving the error:
"SAML assertion failed: invalid audience URI (Error code: SAML_4021)".

Our IT team has confirmed the IdP configuration looks correct on our end. We reverted
the change on our side but the issue persists. This is impacting our entire customer
support team and we cannot process any tickets right now.

We are running version 9.4.2 of the platform, Azure AD as our IdP.

This is a revenue-impacting outage. Please escalate immediately.

John Smith
IT Director, Acme Corp
"""


def query_ollama(model: str, prompt: str) -> str:
    """Send a prompt to Ollama and return the response text."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Ollama. Make sure it's running: ollama serve", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ Ollama timed out. Try a smaller model.", file=sys.stderr)
        sys.exit(1)


def parse_json_response(raw: str) -> dict:
    """Extract JSON from model response, handling common formatting issues."""
    # Strip markdown fences if model adds them anyway
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(cleaned[start:end])
        raise ValueError(f"Could not parse JSON from model response:\n{raw}")


def format_text(data: dict) -> str:
    """Format summary as readable plain text."""
    severity_icons = {"P1": "🔴", "P2": "🟠", "P3": "🟡", "P4": "🟢"}
    sev = data.get("severity", "?")
    icon = severity_icons.get(sev, "⚪")

    lines = [
        "=" * 60,
        "  SUPPORT CASE SUMMARY",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
        f"📌 {data.get('one_line_summary', 'N/A')}",
        "",
        f"{icon} Severity: {sev}  |  Product: {data.get('affected_product', 'N/A')}",
        f"   {data.get('severity_reason', '')}",
        "",
        "PROBLEM",
        "-" * 40,
        data.get("problem_statement", "N/A"),
        "",
        "CUSTOMER IMPACT",
        "-" * 40,
        data.get("customer_impact", "N/A"),
        "",
        "SUGGESTED NEXT ACTION",
        "-" * 40,
        f"→ {data.get('suggested_next_action', 'N/A')}",
        "",
    ]

    info_needed = data.get("information_needed", [])
    if info_needed:
        lines.append("INFORMATION NEEDED")
        lines.append("-" * 40)
        for item in info_needed:
            lines.append(f"  • {item}")
        lines.append("")

    entities = data.get("key_entities", {})
    lines += [
        "KEY ENTITIES",
        "-" * 40,
        f"  Customer:    {entities.get('customer_name', 'Unknown')}",
        f"  Environment: {entities.get('environment', 'Unknown')}",
        f"  Version:     {entities.get('version', 'Unknown')}",
    ]
    errors = entities.get("error_codes", [])
    if errors:
        lines.append(f"  Error codes: {', '.join(errors)}")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_markdown(data: dict) -> str:
    """Format summary as markdown."""
    severity_icons = {"P1": "🔴", "P2": "🟠", "P3": "🟡", "P4": "🟢"}
    sev = data.get("severity", "?")
    icon = severity_icons.get(sev, "⚪")
    entities = data.get("key_entities", {})

    lines = [
        "## Support Case Summary",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"### {icon} {data.get('one_line_summary', 'N/A')}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| **Severity** | {sev} — {data.get('severity_reason', '')} |",
        f"| **Product** | {data.get('affected_product', 'N/A')} |",
        f"| **Customer** | {entities.get('customer_name', 'Unknown')} |",
        f"| **Version** | {entities.get('version', 'Unknown')} |",
        "",
        "### Problem",
        data.get("problem_statement", "N/A"),
        "",
        "### Customer Impact",
        data.get("customer_impact", "N/A"),
        "",
        "### Suggested Next Action",
        f"> {data.get('suggested_next_action', 'N/A')}",
        "",
    ]

    info_needed = data.get("information_needed", [])
    if info_needed:
        lines.append("### Information Needed")
        for item in info_needed:
            lines.append(f"- {item}")
        lines.append("")

    errors = entities.get("error_codes", [])
    if errors:
        lines.append("### Error Codes")
        for e in errors:
            lines.append(f"- `{e}`")

    return "\n".join(lines)


def get_model() -> str:
    """Auto-detect the first available Ollama model."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = response.json().get("models", [])
        if models:
            return models[0]["name"]
    except Exception:
        pass
    return "llama3.2"


def main():
    parser = argparse.ArgumentParser(
        description="Support Case Summarizer — AI-powered structured ticket summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python summarize.py ticket.txt
  python summarize.py --format json ticket.txt
  python summarize.py --format markdown ticket.txt > summary.md
  cat ticket.txt | python summarize.py
  python summarize.py --demo
        """,
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to ticket file (omit to read from stdin)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Ollama model to use (default: auto-detected)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with a built-in demo ticket",
    )

    args = parser.parse_args()
    model = args.model or get_model()

    # Load ticket content
    if args.demo:
        ticket_text = DEMO_TICKET
        print(f"🎬 Running demo ticket  |  Model: {model}\n", file=sys.stderr)
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                ticket_text = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        ticket_text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(0)

    if not ticket_text.strip():
        print("❌ Ticket content is empty.", file=sys.stderr)
        sys.exit(1)

    print(f"⏳ Analyzing ticket...  |  Model: {model}", file=sys.stderr)

    full_prompt = f"{SYSTEM_PROMPT}\n\nSupport ticket:\n\n{ticket_text}"
    raw_response = query_ollama(model, full_prompt)

    try:
        data = parse_json_response(raw_response)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"❌ Failed to parse model response: {e}", file=sys.stderr)
        print("Raw response:", file=sys.stderr)
        print(raw_response, file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(data, indent=2))
    elif args.format == "markdown":
        print(format_markdown(data))
    else:
        print(format_text(data))


if __name__ == "__main__":
    main()
