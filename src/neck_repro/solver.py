"""The supplied LP: maximize beta, B alpha = (J.T Uw) beta, 0<=alpha<=1."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import linprog


@dataclass
class Solution:
    status: int
    message: str
    activation: np.ndarray | None = None
    beta: float | None = None
    residual: float | None = None
    scaled_residual: float | None = None
    upper_marginal: np.ndarray | None = None
    iterations: int = 0


def solve_direction(B, q, *, method="highs", tolerance=1e-9):
    B, q = np.asarray(B, dtype=float), np.asarray(q, dtype=float)
    if B.ndim != 2 or q.shape != (B.shape[0],) or not np.isfinite(B).all() or not np.isfinite(q).all():
        raise ValueError("Incompatible or nonfinite torque maps")
    ng = B.shape[1]
    aeq = np.column_stack((B, -q))
    r = linprog(np.r_[np.zeros(ng), -1], A_eq=aeq, b_eq=np.zeros(len(q)),
                bounds=[(0, 1)] * ng + [(0, None)], method=method,
                options={"primal_feasibility_tolerance": tolerance,
                         "dual_feasibility_tolerance": tolerance})
    if not r.success:
        # Unbounded/failed tasks remain failures, never manufactured zero forces.
        return Solution(r.status, r.message, iterations=r.nit)
    alpha, beta = r.x[:-1], float(r.x[-1])
    residuals = B @ alpha - q * beta
    scale = np.maximum(1, abs(B) @ abs(alpha) + abs(q * beta))
    return Solution(r.status, r.message, alpha, beta, float(abs(residuals).max()),
                    float((abs(residuals) / scale).max()), r.upper.marginals[:-1], r.nit)


def validate_solution(solution, tolerance=1e-7):
    if solution.status != 0:
        raise RuntimeError(f"LP failed ({solution.status}): {solution.message}")
    values = np.r_[solution.activation, solution.beta, solution.scaled_residual]
    if not np.isfinite(values).all():
        raise RuntimeError("Nonfinite solution")
    if min(solution.activation) < -tolerance or max(solution.activation) > 1 + tolerance or solution.beta < -tolerance:
        raise RuntimeError("Bounds violated")
    if solution.scaled_residual > tolerance:
        raise RuntimeError("Equilibrium residual exceeded tolerance")
