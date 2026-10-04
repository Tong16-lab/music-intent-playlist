# Formal Evaluation Network Failed: Offline Verification Records

This document is a **post-mortem diagnostic note** for the failed run on 2026-10-03, with no model calls, score recalculations, modifications to frozen answers, or overwriting of the original `evaluation.*` and `evaluation_trace.jsonl`. The code version used by the old run is determined by the code hash in `evaluation.json`; the anomaly breakdown below is for future authorized connection inspections only and cannot be used to retroactively deduce past errors.

## What can currently be confirmed about the old run

| Sentence ID | Tried | Safety Error Category | Program Stage | Recorded HTTP Status Code | Can Confirm Reaching Service Provider |
| --- | --- | --- | --- | --- | --- |
| `test_001` | Yes | `network` | API request / response reading stage; did not enter JSON validation | No record | Cannot |
| `test_002` | Yes | `network` | API request / response reading stage; did not enter JSON validation | No record | Cannot |
| `test_003` | Yes | `network` | API request / response reading phase; did not enter JSON validation | No record | Cannot |

All three have no processable API response, no token usage, and no raw model predictions. The program stopped after three consecutive API/structural failures, and `test_004`—`test_030` were not called. The old client separately caught `HTTPError` first, mapping captured 4xx/5xx errors to other error categories; therefore, the old records **show no evidence that Python ever caught a direct `HTTPError`**. However, HTTP errors from the proxy tunnel might be wrapped as `URLError`, and the old logs did not save the status code; it cannot be asserted from this whether the provider received the request, nor can it be asserted that they did not.

The old code lumped `URLError`, `TimeoutError`, and `OSError` all into `network`, with the same `try` block covering both opening the connection and reading the response body. Consequently, the existing records are **unable to trace** which of the following occurred: DNS, TLS, proxy, permissions, connection refused, connection reset, connection/response-waiting timeout, or response-reading timeout; nor can they determine the actual provider, whether the request reached the provider, or whether billing occurred. The logs lack HTTP status codes for each call, underlying exception types, phase breakdowns, or provider request IDs. Do not guess the root cause based on fast command completion or zero tokens.

## This Round of Offline Improvements

Added fixed security categories to the shared exception object and shorthand format request client: DNS, TLS, TLS certificate, open/wait response timeout, response body read timeout, local permissions, connection refused, connection reset, network unreachable, proxy tunnel, and other network errors. Only fixed categories, phases, and available numeric HTTP status codes are logged; raw exception text, hostnames, proxy addresses, request headers, secrets, or response bodies are never logged. Even if an HTTP status code is obtained, it cannot solely prove that the model provider was reached, as the status may originate from a gateway or proxy.

`scripts/check_transport_once.py` is a one-time connection diagnostic entry point reserved for **future separate authorization**: it fixedly uses the tested `compact-dev-v2`, an existing model, and a example sentence not in the development/production test sets; without the `--allow-paid-connection` flag, it will not read local configurations or send requests. It does not create formal evaluation markers, nor does it touch legacy run files. Success or failure only outputs the security category, phase, available status code, tokens, and estimated cost to the terminal; it does not save or print the complete model response.

## Explanation of Old Reports

The old report lists the AI as `0/30` based on the scheduled end-to-end denominator, which means **3 attempts that failed and 27 uncalled**, rather than intent judgment errors by the model across 30 items. The valid intent card count is 0, so neither the valid output accuracy nor the model understanding capability can be evaluated. The keyword baseline score can serve as an independent result for the same batch of examples and cannot be compared for capability superiority or inferiority against the unresponsive AI in this run. The beginning of the old report has already clarified this point.

The SHA-256 checksums for the three frozen record files in `data/test_set_freeze.json` have passed verification again in this round; no re-freezing was performed.

## Next Minimum Verification (Not Executed This Round)

In an environment with explicit user authorization and local network permission, initiate **only one** connection request for this fixed non-test example sentence, without retrying or running the 30 formal sentences. Prioritize checking the desensitization category and phase: if it is still a local permission, DNS, or proxy error, address the environment first; if there is an HTTP status code, handle it according to the authentication/quota/request format category; if a complete response is obtained, separately inspect the structure and local evidence verification. This single attempt may incur charges under standard rates; estimated at approximately USD 0.0009 based on development set average usage, with actual usage or billing unknown. Do not treat a successful connection as an official evaluation score.
