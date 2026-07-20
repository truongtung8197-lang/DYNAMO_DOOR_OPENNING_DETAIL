Here is the optimized, English-translated version of your `AGENTS.MD` file, customized for AI agents and enhanced with a new section specifically tailored for small LLM optimization.

---

# Dynamo Python Tool Rules — Revit 2024

Applied to all Dynamo Python tools in this system. Each tool has its own `progress.md`; this file acts as the immutable global ruleset.

## 0. Small/Fast LLM Optimization (Crucial for lightweight or distilled models, e.g. DeepSeek Flash, Step 3.7 Flash)

* **Limit Output Length:** Each code block must not exceed ~50 lines unless explicitly requested otherwise. Place comments only at critical points: transaction boundaries, unit conversions, or non-obvious side-effects. Do not add comments explaining obvious code.
* **No Multi-tasking:** Focus on solving exactly **one** specific sub-task or node per turn. Do not generate the entire script and deployment plan simultaneously. Exception: merging tiny, directly codependent sub-tasks (e.g., a function and its corresponding unit test) is allowed if separating them makes no sense.
* **Linear Reasoning Before Coding:** Before writing code, break down complex logic into clearly numbered linear steps. This rule applies to the **reasoning process**, not the final code structure—if the problem inherently requires nested logic or recursion (tree traversal, parsers, backtracking, etc.), it is still permitted, provided the rationale was clarified in the preceding breakdown step.
* **No Over-Engineering:** Prefer language built-ins over abstract design patterns unless explicitly requested or truly necessary for the problem (e.g., handling multiple interchangeable algorithms makes the Strategy pattern reasonable). Keep algorithms simple, easy to trace, and avoid premature abstraction.
* **Verify Before Assume:** If uncertain about a function name, signature, or library API, **do not** guess or hallucinate. Ask the user or insert a clear `TODO`/comment marking the exact spot that requires verification.

## 1. Environment & Technical Risks (Read before coding)

* **Stack:** Revit 2024, Dynamo + IronPython3.
* **Revit API Lookup:** If internet access is enabled, search directly at `[https://www.revitapidocs.com/2024/](https://www.revitapidocs.com/2024/)` by class/method name. If information is missing, report to the user instead of guessing signatures.
* **Wrapper:** Always use `UnwrapElement(...)` before calling Revit APIs or checking `isinstance(...)` on objects passed from Dynamo. Never assume raw Revit API objects.
* **Units:** No assumed units. Document input/output units explicitly (`mm`, `feet`, `degree`) and state conversion factors.
```python
mm = feet * 304.8

```


* **Transactions:** Explicitly define transaction boundaries for modifying the model. Prefer `TransactionManager` over manual transactions.
* **Top 4 Failure Modes:** Silent failure, incorrect geometry, missing unwrap, incorrect units, and faulty transaction assumptions.

## 2. Strict Constraints (DO NOT DO)

* **No Silent Fails:** Never use `except: pass`. Errors must be caught and logged.
* **No Deep Nesting:** Do not pack all outputs into a single nested dictionary. Outputs must be directly readable via a Dynamo `Watch` node.
* **No Cosmetic Splitting:** Do not split nodes solely to shorten functions or for purely aesthetic code styling.
* **Batch Support by Default:** Do not write nodes supporting only single elements unless strictly constrained by technical limitations. Support lists and nested lists natively.
* **Fix at Source:** Never patch errors in downstream nodes if the bug originated upstream. Go back and fix the source node.
* **One-Shot Questioning:** Gather all missing details into a single prompt rather than asking piecemeal questions (e.g., Type or Instance? Parameter name? Tolerance? Family category? Batch support needed?).

## 3. Best Practices (SHOULD DO)

* **Strategic Node Splitting:** Split nodes at critical data boundaries where a failure corrupts all subsequent results, AND the output is directly verifiable (e.g., `Point`, `Vector`, `Curve`, `Solid`, `Element`, `Number`, `Boolean`).
* **Tuple Outputs:** Return data and logs as a tuple, not a dictionary:
```python
OUT = data, log

```


* **Explicit I/O Mapping:** Explicitly document inputs and outputs for each node:
```python
IN[0] = SelectModelRevit
IN[1] = OUTPUT NODE ...
OUT[0] = FamilySymbol
OUT[1] = Dynamo Point (Location)
OUT[2] = Log

```


* **Independent Cross-Checking:** Validate outputs using a data source different from the one used to generate them (e.g., if geometry is generated from parameters, validate it against actual spatial geometry, and vice versa).
* **Robust Batch Debugging:** Track and report the count of successes vs. failures. Log specific `Element ID`s and error causes. A failure in one element must not break the entire batch execution.

## 4. Workflow Lifecycle

* **Pre-Code Alignment:** Before coding, list out the processing steps, inputs/outputs, node dependencies, and highest risk factors. Wait for user confirmation.
* **Phase-Based Coding:** Develop one node cluster at a time. The user must test it on a live model and confirm before moving to the next phase. Do not write the entire tool before debugging.

## 5. Context Management (`progress.md` per tool)

* **Session Start:** Read the tool's specific `progress.md`. Do not re-verify locked architectural decisions.
* **Phase Completion:** Update `progress.md` after every validated phase with architectural decisions, new nodes, resolved bugs, lessons learned, and remaining tasks.
* **Minimalist Reference:** Never reiterate established rules. Reference them briefly (e.g., *"Per Phase 2 agreement"*, *"Per current progress.md"*).

## 6. Conflict Resolution Hierarchy

`Correct & Verifiable` > `Easy to debug on live model` > `Maintainable` > `Token efficiency`.

## 7. Known System Anomalies

* `hasattr(obj, "__iter__")` evaluates to `True` incorrectly for `FamilySymbol` and `FamilyInstance`. Use `isinstance(obj, (list, tuple))` instead.
* Dynamo may automatically wrap the output of a preceding node into a `[list, log]` structure; ensure proper unwrapping when received as an input.