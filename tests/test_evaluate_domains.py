from unittest import TestCase

from scripts.evaluate_domains import compare, compare_live, evaluate


class DomainEvaluationTests(TestCase):
    def test_absent_candidate_and_out_of_search_source_are_distinct(self):
        snapshot = {'server_version': 'fixture', 'cases': [
            {'id': 'a', 'kind': 'documents', 'split': 'verify', 'expected': ['resilience'],
             'item': {'id': 'guide:a', 'title': 'Conservation des aliments'}},
            {'id': 'b', 'kind': 'documents', 'split': 'verify', 'expected': ['culture']},
            {'id': 'c', 'kind': 'videos', 'split': 'control', 'expected': ['culture'], 'position': 1,
             'item': {'id': 'video:c', 'title': 'Animation'}},
        ]}
        report = evaluate(snapshot)
        self.assertEqual(report['groups']['all']['measured'], 2)
        self.assertEqual(report['groups']['all']['found_in_search'], 1)
        self.assertEqual(report['groups']['all']['exact'], 2)

    def test_better_exact_score_cannot_hide_lost_expected_membership(self):
        cases = [{'id': source, 'split': 'verify', 'expected': ['resilience'],
                  'predicted': predicted} for source, predicted in [
                      ('a', ['resilience', 'culture']), ('b', ['culture']), ('c', ['culture'])]]
        old = {'cases': cases, 'snapshot_sha256': 'same', 'groups': {'verify': {'measured': 3, 'exact': 0}}}
        new = {**old, 'groups': {'verify': {'measured': 3, 'exact': 2}},
               'cases': [{**case, 'predicted': ['culture'] if case['id'] == 'a' else ['resilience']} for case in cases]}
        result = compare(old, new)
        self.assertFalse(result['passes_verification'])
        self.assertEqual(result['lost_in_verification'], ['a'])
        with self.assertRaisesRegex(ValueError, 'captures différentes'):
            compare(old, {**new, 'snapshot_sha256': 'other'})

    def test_live_comparison_preserves_video_discovery_in_both_spaces(self):
        visible = {'position': 1, 'coverage': 'partial', 'elapsed_ms': 20}
        absent = {**visible, 'position': None}
        case = {'id': 'a', 'kind': 'videos', 'title_prefix': 'Fixture', 'dedicated': True,
                'query': 'fixture', 'expected': ['culture'],
                'live_filters': {domain: visible for domain in ('all', 'culture', 'resilience')}}
        before = {'server_version': 'before', 'cases': [case]}
        after = {'server_version': 'after',
                 'cases': [{**case, 'live_filters': {**case['live_filters'], 'resilience': absent}}]}
        result = compare_live(before, after)
        self.assertFalse(result['passes_verification'])
        self.assertEqual(result['lost_expected'], [{'id': 'a', 'domain': 'resilience'}])
        self.assertEqual(result['before']['expected_visible'], 3)
        self.assertEqual(result['after']['expected_visible'], 2)
        self.assertEqual(result['after']['p95_ms'], 20)
