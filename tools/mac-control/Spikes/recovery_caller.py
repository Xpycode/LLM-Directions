"""Explicit native activation caller; importable only, with no CLI or launch.

Trusted callers supply the held original marker owner, externally acquired
baseline/seal/history, and separately provisioned witness slots. No defaults
select live state or infer authority from discovered files. This function must
only be invoked for live state after the reviewed initialization/activation
request. Defining it does not authorize that request or a foreground window.
"""
from dataclasses import dataclass
import os

import recovery_activation as activation
import recovery_retention as retention
from recovery_probe import capture_bounded_context
from recovery_snapshot import MarkerLock, require
from supervisor import mac_clock
from runtime_root import trusted_runtime_root


@dataclass(frozen=True)
class WitnessSlot:
    directory: str
    trusted_identity: tuple

    def retain(self, value):
        retention.retain(self.directory, value, trusted_directory_identity=self.trusted_identity)


def activate_retained(owner, seal, baseline, *, history, trusted_history_sha256,
                      transition_slot, acknowledgement_slot, provenance):
    """Acquire native context and retain both original transition and final ack.

    Returns a retained acknowledgement, not a launch request or foreground grant.
    Failure leaves all evidence; there is no retry/reconcile fallback. Ownership
    remains with the caller through return or failure. Native observation uses
    the bounded helper and the supervisor's continuous clock.
    """
    require(type(owner) is MarkerLock, "untrustedMarkerLock")
    trusted_runtime_root(owner.directory)
    owner.recheck()
    slots = (transition_slot, acknowledgement_slot)
    for slot in slots:
        require(type(slot) is WitnessSlot, "untrustedWitnessSlot")
        retention.check_empty(slot.directory, trusted_directory_identity=slot.trusted_identity)
        common = os.path.commonpath([owner.directory, slot.directory])
        require(common not in (owner.directory, slot.directory), "witnessNamespaceNotSeparate")
    require(transition_slot.trusted_identity != acknowledgement_slot.trusted_identity,
            "witnessSlotsNotSeparate")
    common = os.path.commonpath([slot.directory for slot in slots])
    require(common not in tuple(slot.directory for slot in slots), "witnessSlotsNotSeparate")
    clock = mac_clock()
    def observe():
        return capture_bounded_context(clock=clock)
    acknowledgement = activation.activate(owner, seal, baseline, history=history,
        trusted_history_sha256=trusted_history_sha256, observe=observe, clock=clock,
        provenance=provenance, checkpoint_sink=transition_slot.retain)
    acknowledgement_slot.retain(acknowledgement)
    owner.recheck()
    return acknowledgement
