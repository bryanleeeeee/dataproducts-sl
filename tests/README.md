# Tests

## `golden.json`

The parity fixture, generated from the original TypeScript engine. To
regenerate it from the React source tree:

```bash
# in the React project
rolldown -c rolldown.config.mjs   # bundles golden.ts (see the port notes)
node golden.bundle.mjs            # writes golden.json
```

It contains, for each of the 200 catalogue products: the constructed product
and its benefit inputs, every headline financial, slices of the monthly
cashflow streams, category/class/maturity splits, cost breakdown, confidence
and priority scores with their components, guardrail flags with full wording,
the three scenarios, the sensitivity rows, the recommendations, the realisation
history and the assumption register — plus the portfolio-level insights.

## Running

```bash
python tests/test_parity.py                  # uses GOLDEN, defaults to /tmp/golden.json
GOLDEN=tests/golden.json python tests/test_parity.py

# with the app running on :8501
python tests/smoke.py
python tests/interactions.py
```
