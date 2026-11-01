from copy import deepcopy
import unittest
from myriadforge.core import Session, DomainError


class CoreTests(unittest.TestCase):
    def test_complete_flow_and_retry(self):
        session = Session(inventory={'guardian_rune': 3, 'shield_fragment': 6})
        session.transition('umbrella')
        with self.assertRaisesRegex(DomainError, 'FORM_LOCKED'):
            session.transition('shield')
        self.assertEqual(session.current, 'umbrella')
        session.craft('guardian', 'request-1')
        before = deepcopy(session)
        session.craft('guardian', 'request-1')
        self.assertEqual(session, before)
        session.transition('shield')
        self.assertEqual(session.current, 'shield')

    def test_insufficient_materials_changes_nothing(self):
        session = Session(inventory={'guardian_rune': 3})
        before = deepcopy(session)
        with self.assertRaisesRegex(DomainError, 'INSUFFICIENT_MATERIALS'):
            session.craft('guardian', 'request-2')
        self.assertEqual(session, before)

    def test_illegal_direct_transition(self):
        session = Session(unlocked={'folded', 'umbrella', 'shield', 'staff'})
        with self.assertRaisesRegex(DomainError, 'TRANSITION_NOT_ALLOWED'):
            session.transition('staff')

    def test_idempotency_key_conflict(self):
        session = Session(inventory={'guardian_rune': 3, 'shield_fragment': 6})
        session.craft('guardian', 'same')
        with self.assertRaisesRegex(DomainError, 'IDEMPOTENCY_CONFLICT'):
            session.craft('arcane', 'same')

    def test_unknown_form(self):
        with self.assertRaisesRegex(DomainError, 'UNKNOWN_FORM'):
            Session().transition('unknown')
