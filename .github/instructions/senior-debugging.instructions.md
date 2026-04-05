---
description: "Use when: analyzing logs, debugging complex issues, handling exceptions, or writing diagnostic telemetry"
applyTo: "**/*.py"
---
# Senior Diagnostics & Deep Debugging Protocol

When debugging Python modules or configuring logging/endpoints, adhere rigidly to these Google-tier observability principles:

1. **Never Swallow Exceptions:** Never use a bare \	ry: ... except: pass\. Always log the stack trace and contextual variables that led to the fault.
2. **Context-Heavy Logs:** Use structured logging injected with execution context. If debugging a DataFrame, log shapes, memory footprints, and unique column schemas before/after transformations.
3. **Fail Fast, Recover Gracefully:** Validate inputs immediately at boundaries (e.g., endpoint ingestion or file loading). Do not let poisoned data propagate deep into the processing engine.
4. **Traceability:** When fixing a bug, leave a comment tracing why the architectural fix was chosen (e.g., \# Fix: Coalesce duplicate columns to prevent AttributeError during lateral DataFrame concat.\).
5. **Read Before Writing:** Always trace the upstream data provider before assuming the downstream consumer is broken.
