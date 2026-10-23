# Model Decisions — Dallas Stars 2026-27 Forecast

Formulas, definitions, assumptions, and data-convention decisions. Items marked
INSTRUCTOR REVIEW need Business Customer / instructor input before being
presented as agreed.

## Goal definitions (preserved, not conflated)
1. Displayed final score (may include a shootout decision increment).
2. Final hockey goals = regulation + OT goals; shootout decision increment excluded.
3. Regulation goals at 60 minutes.
The Poisson fit uses regulation goals only (definition 3). Shootout increments
are never treated as hockey goals.

## Baseline rates
lambda_GF = mean(regulation GF per game) over verified 2025-26 games.
lambda_GA = mean(regulation GA per game) over verified 2025-26 games.
This differs from the proposal's totals/82 estimate only if regulation totals
differ from displayed final totals; both will be shown side by side and the
discrepancy flagged. (INSTRUCTOR REVIEW: confirm regulation-based fit is
acceptable versus the proposal's season-totals approach.)

## Proposal-claimed 2025-26 values
273 GF, 222 GA, 50-20-12, 112 points are treated as UNVERIFIED. They are not
hard-coded anywhere. If verified values disagree, verified values govern and
the discrepancy is documented in docs/data-report.md.

## OT/SO resolution
Games tied after regulation are resolved with Dallas' empirical OT/SO win
probability estimated from that season's tied games only (not all wins, not
one-goal games). OT vs SO outcomes preserved. If no tied games exist, the run
fails clearly; no unstated 50% fallback.

## Season simulation
X ~ Pois(lambda_GF), Y ~ Poisson(lambda_GA), independent. X>Y win, X<Y
regulation loss, tie -> OT/SO. Points: 2 for any win, 1 for OT/SO loss, 0 for
regulation loss. 82 games per season, >= 10,000 seasons per scenario, fixed
seed. Goal differential = regulation GF - GA (audited); no double-counting of
an OT deciding goal.

## Scenarios
S0 baseline. S1: lambda_GF × (1+s), s in {-15,-10,-5,+5,+10,+15}%, defense
fixed. S2: lambda_GA × (1+d), same d values, offense fixed; negative d =
improved defense. S3: roster math, projected goals =
prior goals/prior games × future games × role factor ÷ 82; incoming minus
outgoing; replacement production included, never a full subtraction without
replacement; goalie scenarios carry an explicit GA assumption. S4: one
combined case, components and order shown, labeled conditional.

## Backtest
Fit on 2024-25 only; simulate 2025-26; load verified 2025-26 actual for
evaluation only. Metrics: mean/median points, abs point error, 80%/95%
interval coverage, predicted vs actual W/REG_L/OTL. No tuning to target.

## Historical translation
Central Division 2021-22..2025-26, completed 82-game seasons, all teams.
"Top-three point-level probability" = fraction of seasons where simulated
Dallas points meet/exceed the historical 3rd-place threshold, averaged over
seasons. Equality: meeting the threshold counts. Not a playoff guarantee, not
exact-rank odds.

## Data conventions
Percentages stored 0-100 with numerator/denominator where available. Goalie
appearances != team games. Traded players: Dallas-only contributions separate
from full-season. No 2026-27 results in fitting.

## Scheduling note
Proposal lists Nov 16 (presentation date) and Nov 30 (schedule introduction).
Recorded as a scheduling clarification; not a coding blocker; no instructor-
confirmed date assumed.

## Known scientific limitations
Constant Poisson rates ignore opponent strength, home/away, injuries, travel,
back-to-backs, empty-net effects; goals for/against not independent; player
production not perfectly additive. Monte Carlo intervals are conditional on
the model, not confidence intervals.