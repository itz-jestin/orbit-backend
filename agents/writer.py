from utils.logger import logger
from state import ResearchState
from tools.llm import llm


def writer(state: ResearchState):

    logger.info("Writer started")

    research = state["research_results"]
    critique = state.get("critique") or {}
    is_revision = bool(state.get("final_report")) and critique.get("approved") is True

    if is_revision:
        logger.info("Writer running in revision mode")

        prompt = f"""
You are a professional research report writer revising your own report
based on reviewer feedback.

Here is your previous report:

{state["final_report"]}

Here is the reviewer's feedback on what to improve:

{critique.get("feedback", "")}

Specific issues by question:
{critique.get("question_issues", [])}

Research (for reference, in case you need more detail to address the
feedback):

{research}

STRICT GROUNDING RULES (do not violate these while adding depth):
- Use ONLY facts, figures, and statements present in the Research above.
- NEVER invent direct quotations. Do not use quotation marks around any
  text unless that exact text appears verbatim in the Research.
- NEVER invent publication years, dates, or in-text citations like
  "(Company, 2022)". The Research does not include dates — do not add any.
- If you cite a source, refer to it only by name/domain as it appears in
  the Research's "sources" list — no fabricated attribution.
- If the feedback asks for "more depth" or "more examples" and the
  Research doesn't contain enough detail to provide it, say so explicitly
  in the report rather than inventing detail.

Rewrite the FULL report addressing the feedback. Keep the same overall
structure (# Introduction, # Main Findings, # Conclusion). Return only
the revised report.
"""
        state["revised"] = True
    else:
        prompt = f"""
You are a professional research report writer.

Using the research below, write a detailed report.

Research:

{research}

STRICT GROUNDING RULES:
- Use ONLY facts and statements present in the Research above.
- NEVER invent direct quotations, publication years, or dates.
- If citing a source, refer to it only by name/domain as given — no
  fabricated attribution format like "(Company, 2022)".
- Do NOT write "According to [Source]" or similar attribution phrases
  unless that exact claim appears in the Research above. Do not add
  outside knowledge you may know about the topic, even if true — only
  synthesize what is present in the Research.

The report should contain:

# Introduction

# Main Findings

# Conclusion

Return only the report.
"""

    logger.info("Sending report generation request to LLM")

    try:
        response = llm.invoke(prompt)
    except Exception as e:
        logger.error(f"LLM call failed in writer: {e}")
        raise

    logger.info("Report generated successfully")

    state["final_report"] = response.content

    logger.info("Writer completed")

    return state