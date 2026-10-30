"""Mock payment gateway.

Behaves like a real one in the ways that matter: it is idempotent on the
merchant reference, can time out AFTER taking the money, and resolves later.
"""
import time
from dataclasses import dataclass

clock = time.time  # tests replace this
PENDING_RESOLVE_AFTER_S = 8.0


class GatewayTimeout(Exception):
    pass


@dataclass
class _Txn:
    scenario: str
    created: float


_txns: dict[str, _Txn] = {}


def charge(ref: str, amount: int, scenario: str) -> str:
    """Returns 'success' or 'failed'. Raises GatewayTimeout for the timeout scenario."""
    txn = _txns.setdefault(ref, _Txn(scenario, clock()))
    if txn.scenario == "failure":
        return "failed"
    if txn.scenario == "timeout":
        raise GatewayTimeout(ref)  # money may already be taken
    return "success"


def status(ref: str) -> str:
    """'success' | 'failed' | 'pending' | 'unknown'"""
    txn = _txns.get(ref)
    if txn is None:
        return "unknown"
    if txn.scenario == "failure":
        return "failed"
    if txn.scenario == "timeout":
        return "success" if clock() - txn.created >= PENDING_RESOLVE_AFTER_S else "pending"
    return "success"
