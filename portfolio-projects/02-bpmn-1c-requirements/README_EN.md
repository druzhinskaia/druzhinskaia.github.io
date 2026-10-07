# 1C request processing: analytical specification

[Русский](README.md)

The author's task and source requirements underpin the AS-IS/TO-BE process, functional requirements, UI mock-up, routing rules, SLA, traceability matrix and acceptance scenarios. This repository demonstrates analysis and specification; it does not supply a deployed 1C extension or measured implementation effects.

The canonical rules are in `06-specification/technical-specification.md`, `status-transitions.md` and `sla-and-notifications.md`. High-priority requests or categories requiring approval enter approval on creation; standard requests enter New. Rejection and clarification have explicit routes. Only the manager closes a completed request and closing sets its timestamp. SLA runs during approval and clarification. Working calendar, role checks, notification retries and acceptance cases are explicit.

Python 3.10–3.12, standard library: `python -m unittest discover -s tests -v`. The Python reference model checks calendar and state transitions; it is not 1C implementation. 1C UI, permissions, notification integration and performance scenarios remain pending target-environment execution.

Working hours 09:00–18:00 and SLA of 1/3/5 nine-hour working days are specification decisions to approve before implementation. Previous figures of 200 requests per day and three-day processing are not presented as verified results without a period, source and measurement method. No interview or deployment claim is inferred from documents alone.
