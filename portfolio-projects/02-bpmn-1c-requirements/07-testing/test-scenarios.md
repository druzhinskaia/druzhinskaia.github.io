# Test Scenarios

| ID | Scenario | Steps | Expected Result |
|---|---|---|---|
| TS-01 | Required fields validation | Create request without category and priority | System shows validation error and does not save request |
| TS-02 | SLA calculation | Select high priority | SLA is set to 1 working day |
| TS-03 | Standard request flow | Create request with medium priority and complete all required fields | Request receives status `Новая` and responsible manager is notified |
| TS-04 | Approval flow | Create high-priority request | Request moves to `На согласовании` |
| TS-05 | Overdue notification | Leave request open after SLA deadline | Head of sales receives overdue notification |
| TS-06 | Status history | Change status from `Новая` to `В работе` | History contains date, user and new status |
| TS-07 | Report | Open manager report | Report shows requests by status, overdue requests and responsible users |
