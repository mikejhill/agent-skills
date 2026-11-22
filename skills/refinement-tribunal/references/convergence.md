# Convergence

Do not evaluate stop conditions until the minimum of two iterations is done.

```text
severity = critical*8 + significant_gaps*4 + weaknesses*2 + minor*1
```

The weights are heuristic; raise weakness weight for safety-critical content. Scores vary between critic runs, so inspect the actual findings before acting on a change in score.

## Stop when any holds

- The iteration cap is reached.
- No critical issues and no significant gaps, and researcher novelty is under 20% (or the researcher was dropped).
- The critic calls the content strong without manufacturing concerns.
- **Degradation:** the score rose versus the previous iteration and the findings confirm it. Revert to the rollback version, log it, stop.
- **Strength erosion:** the advocate flags it and the findings confirm it. Revert, log, stop.
- **Oscillation:** this iteration undid an earlier change. Stop and show the user both versions and the competing views.
- **Stagnation:** the score fell by 10% or less in two consecutive iterations.
- **Dimension regression:** any quality dimension worsened without a documented reason.

## Continue when all hold

Under the cap; at least one critical issue or significant gap, or novelty at 20% or more; score down more than 10%; no unjustified dimension regression; no unresolved erosion flags.

If neither set fully holds (for example, a drop under 10% once), log a soft stagnation signal and continue. A second consecutive signal confirms stagnation and stops the run.

## Edge cases

- **Researcher drop:** if novelty is under 20% in two consecutive iterations, run only the critic and advocate from then on. This mostly matters with a cap of 4 or 5.
- **Already excellent:** still run two iterations.
- **Very long content (over about 60K tokens):** refine each logical section for one iteration, reassemble, then run two holistic iterations for consistency. Calls: `segments*3 + holistic_iterations*3`.
- **Embedded code:** refine the surrounding text; treat code-correctness findings as MEDIUM confidence without specific evidence.
- **Growth:** flag output over 150% of the original size without matching quality gains.
- **Partial rollback:** when specific changes clearly caused degradation, revert only those, and document why.
- **Malformed subagent output:** re-prompt once with tighter format instructions, then continue with the agents that worked and note reduced confidence.
- **Context pressure:** size content in tokens (dense prose is about 30-50 tokens a line). Summarize earlier iterations when your own context gets tight.
