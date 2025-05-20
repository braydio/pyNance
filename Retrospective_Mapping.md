## 🧪 Process Retrospective: Refactor Exposure Mapping

### Information Needed to Map Successfully

- Full recursive access to file tree under `backend/app/`
- File content previews (e.g., function definitions, import statements)
- Knowledge of sync logic patterns (e.g., Plaid/Teller token flow, account history)
- Locations of schema/model definitions

### Techniques Used

- Iterative directory scanning via `getFileOrFolder` to inspect submodules
- Explicit function extraction and cross-referencing to prior module findings
- Internal state tracking across `routes/`, `helpers/`, `sql/`, and `models` layers
- Verification against Canvas and remote source to avoid duplication or omissions

### What Worked

- Controlled exploration order minimized context switching
- Regular Canvas syncing ensured traceable logic state
- Flagging of indirect imports helped detect latent coupling

### Areas to Improve

- Earlier declaration of critical paths (e.g., model file location)
- Initial high-level map of directory structure to frontload discovery
- Automatically summarizing function headers from each file for rapid classification

### Information That Would Improve the Process

- Defined architectural expectations: what layers exist, and where (e.g., services vs helpers)
- Known naming conventions (e.g., `*_logic.py`, `schemas.py`, `models.py`)
- Upfront sync lifecycle outline (what is called, in what order, by what triggers)

---

## 🧠 GPT Prompt Template for Similar Tasks

You can use the following prompt to elicit this same behavior in ChatGPT for any repo:

```text
You are an autonomous assistant mapping the internal architecture of a backend codebase. Your goal is to identify and index all modules involved in a specified feature (e.g., transaction syncing). Iterate recursively through the file tree, identifying and summarizing:

1. Which files import the core feature logic
2. Which functions are exposed or invoked
3. How the data flows between route, service, helper, and data layers
4. Where models and schemas are defined

Maintain persistent state between steps so you don’t lose track of dependencies. Summarize your progress and logic pathway as you proceed. Write a summary of findings to a central documentation file, and wait for user direction before proceeding to the next execution step.

Assume the user may not know the full file structure — discover it as needed and document as you go.
```
