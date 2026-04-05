---
description: "Perform a deep-dive autonomous diagnostic of the system, logs, or a specific endpoint. Use when the system has complex failures."
---
# /system-diagnose

## Task
Perform an autonomous, Google-Tier diagnostic of the requested system component: \{{prompt}}\.

## Protocol
1. **Analyze Context**: Scan the workspace for relevant log files, recent terminals, and affected source code.
2. **Determine Root Cause**: Identify the precise execution failure or performance bottleneck.
3. **Formulate Solution**: Architect a highly resilient, enterprise-grade fix (e.g., dynamic typing fallback, concurrency limits, or robust error handling).
4. **Action**: Apply the fix directly or provide the terminal command to implement the diagnostic patch.
5. **Readout**: Summarize the finding in Portuguese in a "Root Cause -> Architectural Fix -> Validation" format.
