# ADRminer Improvement & Consistency Plan

This document outlines the plan to address identified deficiencies and implement the "Commands and Tools Consistency Plan" in ADRminer.

## 1. Deficiencies to Address

1.  **Inconsistent File Discovery**: CLI uses shallow glob; Agent uses recursive search with hardcoded exclusions.
2.  **Redundant Service Code**: `CheckingService` contains obsolete manual JSON parsing methods.
3.  **Global State Dependency**: Agent tools rely on a global `_session` variable.
4.  **Hardcoded Exclusions**: Directory exclusions are duplicated across the codebase.

## 2. Implementation Steps

### Step 1: Centralized File Discovery & Configuration
*   **Goal**: Ensure consistent ADR discovery across all interfaces.
*   **Actions**:
    *   Add a `standard_exclusions` list to `src/adrminer/config/settings.py`.
    *   Create `src/adrminer/utils/filesystem.py` with a `discover_adrs(path, recursive=True)` utility.
    *   Update `SessionManager.load_adr_files` and agent tools (`load_adrs`, `list_adr_files`) to use this utility.
    *   Update `AgentContext` to use the same exclusion list.

### Step 2: Cleanup of Core Services
*   **Goal**: Remove obsolete code from services using structured output.
*   **Actions**:
    *   Remove `_parse_adherence_response` and `_parse_section_response` from `src/adrminer/services/checking_service.py`.
    *   Ensure all call sites use the LangChain `adherence_chain` and `section_chain` which return Pydantic models directly.

### Step 3: Refactor Handlers for "Silent Mode" (Consistency Plan Phase 1)
*   **Goal**: Enable handlers to return structured data for agent tools.
*   **Critical Requirement**: **Context Preservation**. When a command is triggered via the interactive CLI (slash command), the handler MUST store its results in the session and sync the agent's context. This allows the agent to refer to the analysis results in subsequent natural language interactions.
*   **Actions**:
    *   Update `BaseHandler.execute` in `src/adrminer/chat/handlers/base.py` to accept a `silent: bool` parameter and return `Optional[Dict[str, Any]]`.
    *   Refactor `TopicsPredictHandler`, `ClassifyPredictHandler`, and `CheckPredictHandler`:
        *   Replace manual loops with batch service calls (e.g., `service.classify_batch`).
        *   Wrap Rich UI output in `if not silent:` blocks.
        *   Ensure `self.session.store_analysis_result` is called.
        *   Ensure `self.session.agent_context.load_from_session(self.session)` is called to sync state.
        *   Calculate and return statistics when `silent=True`.

### Step 4: Refactor Agent Tools (Consistency Plan Phase 2 & Global State)
*   **Goal**: Tools should call handlers and avoid global state if possible.
*   **Actions**:
    *   Refactor `src/adrminer/agents/tools.py` to instantiate handlers and call their `execute(..., silent=True)` method.
    *   Investigate replacing the global `_session` with a thread-local or context-bound session if multiple concurrent sessions are needed in the future. For now, ensure the dependency is explicit and well-documented.

### Step 5: Enhanced Interactive CLI Experience
*   **Goal**: Improve usability and persistence.
*   **Actions**:
    *   Implement persistent command history in `src/adrminer/chat/__init__.py` using `prompt_toolkit.history.FileHistory`.
    *   Add "Mini-dashboards" to handlers using `Rich` panels and tables to show distribution summaries after analysis commands.

### Step 6: Expand ADR Parser Capabilities
*   **Goal**: Support a wider range of ADR templates.
*   **Actions**:
    *   Update `ADRParserService` to support Zimmermann and Nygard patterns in addition to MADR.
    *   Implement template detection logic.

## 3. Timeline & Priority

| Priority | Task | Target Module |
| :--- | :--- | :--- |
| **P0** | Consistency Plan (Phase 1 & 2) | `chat/handlers/`, `agents/tools.py` |
| **P1** | Unified File Discovery | `utils/filesystem.py`, `session.py` |
| **P1** | Service Cleanup | `services/checking_service.py` |
| **P2** | Persistent CLI History | `chat/__init__.py` |
| **P3** | Parser Expansion | `services/adr_parser_service.py` |

## 4. Success Criteria

*   The same analysis results are produced whether triggered via `/classify` or "Please classify...".
*   Duplicate logic for file loading and batch processing is removed.
*   No redundant manual parsing code exists in services.
*   CLI command history persists across restarts.
