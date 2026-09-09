"""Strict native spike wire adapter, not a report/log importer.

Used only by the sole reader of retained owned stdout pipes. Launch identity and
tag base come from the controlling caller before input. Native timestamps use
mach_continuous_time; every surrounding observer/probe/verifier clock must match.
No process launch, signalling, marker access or admission authority.
"""
import copy

import recovery_record as model


class NativeFrames:
    def __init__(self, identity, tag_base):
        model.check_identity(identity)
        model.number(tag_base, 1)
        model.require(tag_base <= (1 << 63) - 257)
        self.identity = copy.deepcopy(identity)
        self.base = tag_base
        self.down_count = 0

    def normalize(self, role, row):
        model.require(type(row) is dict and row.get('source') == role)
        ns = row.get('ns')
        model.require(type(ns) is str and ns.isascii() and ns.isdecimal()
                      and len(ns) <= 20 and str(int(ns)) == ns)
        ns = int(ns)
        model.require(0 < ns < 1 << 64)
        event = row.get('event')
        schemas = {
            ('worker', 'posted'): 'tag down',
            ('worker', 'checkpoint'): 'run sequence tag heldKeysEmpty',
            ('target', 'keyDown'): 'tag sourcePID count matchesSamplePrefix',
            ('target', 'keyUp'): 'tag sourcePID',
            ('target', 'observationComplete'): 'pid isActive frontmostPID',
            ('worker', 'preflight'): 'accessibility inputMonitoring eventPosting',
            ('worker', 'ready'): 'pid', ('target', 'ready'): 'pid',
            ('worker', 'bound'): '', ('worker', 'heartbeat'): '',
            ('worker', 'ownedObserved'): 'tag type',
            ('worker', 'stopping'): 'reason focusCheck',
            ('worker', 'stopped'): 'heldKeysEmpty clipboard',
            ('target', 'changed'): 'count',
            ('target', 'becameActive'): '', ('target', 'resignedActive'): '',
            ('target', 'closed'): '', ('target', 'stopClicked'): '',
        }
        model.require((role, event) in schemas)
        model.keys(row, 'source event ns ' + schemas[role, event])
        for field in ('down', 'heldKeysEmpty', 'matchesSamplePrefix', 'isActive',
                      'accessibility', 'inputMonitoring', 'eventPosting'):
            if field in row:
                model.require(type(row[field]) is bool)
        if 'pid' in row:
            model.require(type(row['pid']) is int and row['pid'] == self.identity[role]['pid'])
        for field in ('count', 'type', 'frontmostPID'):
            if field in row:
                model.number(row[field], 0)
        for field in ('reason', 'focusCheck', 'clipboard'):
            if field in row:
                model.require(type(row[field]) is str and len(row[field]) <= 128)
        out = dict(event=event, run=self.identity['run'], ns=ns)
        if event in ('posted', 'keyDown', 'keyUp', 'checkpoint'):
            model.number(row['tag'], 1)
            sequence = row['tag'] - self.base
            model.require(1 <= sequence <= 256)
            out.update(sequence=sequence, tag=row['tag'])
            if event == 'checkpoint':
                model.require(row['run'] == self.identity['run']
                              and type(row['sequence']) is int and row['sequence'] == sequence
                              and row['heldKeysEmpty'] is True)
                out['held'] = []
            elif event == 'posted':
                out['kind'] = 'down' if row['down'] else 'up'
            else:
                out.update(event='receipt', kind='down' if event == 'keyDown' else 'up',
                           origin_pid=row['sourcePID'])
                model.number(row['sourcePID'], 1)
                if event == 'keyDown':
                    # Empty or unchanged text can still match a sample prefix.
                    # Require actual insertion progress, as the supervisor does.
                    model.require(row['matchesSamplePrefix'] is True
                                  and row['count'] == self.down_count + 1)
                    self.down_count += 1
            return out
        if event == 'observationComplete':
            return out
        # Only enumerated diagnostics can be omitted, never input evidence or
        # an unknown lifecycle message. Owned waits and EOF supply exit proof.
        return None
