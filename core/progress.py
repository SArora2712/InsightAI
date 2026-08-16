"""
InsightAI - Sequential step-progress model for the Chat processing indicator.

The backend runs blocking calls (LangGraph invoke/stream), so the UI needs a
small state machine that shows exactly ONE active step at a time, with the
others either done (checkmark, dimmed) or pending (plain gray). Kept pure
(no Streamlit import) so it can be unit-tested and reused.

Call order is the source of truth and is preserved by the model: a step never
becomes active before its predecessor has been reached, no matter in what order
the backend reports per-step completions.
"""

PROCESSING_STEPS = [
    "Run SQL query",
    "Search documents",
    "Synthesize answer",
    "Review answer",
]

STATE_DONE = "done"
STATE_ACTIVE = "active"
STATE_PENDING = "pending"


class StepTracker:
    """Monotonically advancing linear stepper over an ordered step list."""

    def __init__(self, steps=None):
        self._steps = list(steps or PROCESSING_STEPS)
        self._idx = 0

    @property
    def total(self) -> int:
        return len(self._steps)

    @property
    def active(self):
        """Label of the currently active step, or None when complete."""
        return self._steps[self._idx] if self._idx < len(self._steps) else None

    def advance(self, step_label):
        """Mark `step_label` as reached; everything before it becomes done.

        Backwards or repeated completions are ignored so the linear order is
        preserved even when sources complete in a different order.
        """
        if step_label in self._steps:
            target = self._steps.index(step_label)
            if target > self._idx:
                self._idx = target
        return self

    def complete(self):
        """Mark every remaining step done (finished/cancelled)."""
        self._idx = len(self._steps)
        return self

    def snapshot(self):
        """Ordered [(label, state)] pairs for rendering."""
        return [
            (
                label,
                STATE_ACTIVE
                if i == self._idx and i < len(self._steps)
                else (STATE_DONE if i < self._idx else STATE_PENDING),
            )
            for i, label in enumerate(self._steps)
        ]

    def active_count(self) -> int:
        return sum(1 for _, state in self.snapshot() if state == STATE_ACTIVE)


def render_steps_html(tracker) -> str:
    """HTML for the step list shown inside the st.status body.

    - done:     checkmark + dimmed text
    - active:   CSS spinner + highlighted text
    - pending:  plain gray text, no icon
    """
    rows = []
    for label, state in tracker.snapshot():
        if state == STATE_DONE:
            icon = '<span class="ia-step-icon done">&#10003;</span>'
        elif state == STATE_ACTIVE:
            icon = (
                '<span class="ia-step-icon active">'
                '<span class="ia-spinner"></span></span>'
            )
        else:
            icon = '<span class="ia-step-icon"></span>'
        rows.append(
            f'<div class="ia-step {state}">{icon}'
            f'<span class="ia-step-text">{label}</span></div>'
        )
    return '<div class="ia-steps">' + "".join(rows) + "</div>"