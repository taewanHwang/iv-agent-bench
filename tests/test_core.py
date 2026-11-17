import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from iv_agent_bench.core import (init_run, write_new, read_json, predicate_result, import_hermes,
                                 verify, judge_packet, import_judgment)

BASE = Path(__file__).resolve().parents[1]


class BenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = init_run(BASE / 'tasks/calendar-conflict-proposal.json', self.root / 'runs',
                            'test', 'test', 'default', 'synthetic', True)
        self.db = self.root / 'state.db'
        with sqlite3.connect(self.db) as db:
            db.executescript('''CREATE TABLE sessions(id TEXT, model TEXT, system_prompt TEXT);
            CREATE TABLE messages(id INTEGER,session_id TEXT,role TEXT,content TEXT,timestamp REAL,
            tool_calls TEXT, reasoning TEXT,active INTEGER,compacted INTEGER);
            INSERT INTO sessions VALUES('chosen','model','SECRET_SYSTEM');
            INSERT INTO sessions VALUES('other','model','OTHER_SYSTEM');
            INSERT INTO messages VALUES(1,'chosen','user','request',20,NULL,'SECRET_REASONING',1,0);
            INSERT INTO messages VALUES(2,'other','user','OTHER_PRIVATE',20,NULL,NULL,1,0);
            INSERT INTO messages VALUES(3,'chosen','assistant','proposal',10,NULL,NULL,1,0);
            INSERT INTO messages VALUES(4,'chosen','system','SECRET_SYSTEM',30,NULL,NULL,1,0);
            ''')

    def imported(self):
        import_hermes(self.run, self.db, 'chosen')

    def observed(self, state):
        path = self.root / ('observation-' + str(len(list(self.root.glob('observation-*')))) + '.json')
        write_new(path, {'observer':'tester','observed_at':'2026-11-17T00:00:00Z',
                        'method':'independent service inspection','independent_of_agent':True,'state':state})
        return verify(self.run, path)

    def complete_state(self):
        return {'conflict_exists':True,'calendar_changed':False,'external_messages_sent':False}

    def test_missing_is_unknown_and_any_accepts_alternate_path(self):
        self.assertIsNone(predicate_result({'path':['missing'],'equals':True}, {}))
        pred = {'any':[{'path':['api'],'equals':True},{'path':['browser'],'equals':True}]}
        self.assertTrue(predicate_result(pred, {'browser':True}))
        self.assertIsNone(predicate_result(pred, {'browser':False}))

    def test_boolean_is_not_number(self):
        self.assertFalse(predicate_result({'path':['approved'],'equals':True}, {'approved':1}))

    def test_import_scoped_ordered_and_excludes_sensitive_fields(self):
        before = self.db.read_bytes()
        self.imported()
        self.assertEqual(before, self.db.read_bytes())
        raw = (self.run / 'trajectory.json').read_text()
        self.assertNotIn('SECRET', raw)
        self.assertNotIn('OTHER_PRIVATE', raw)
        self.assertEqual([e['source_message_id'] for e in json.loads(raw)['events']], [1,3])

    def test_import_window_and_no_overwrite(self):
        self.assertEqual(import_hermes(self.run,self.db,'chosen',after_id=1,through_id=3),1)
        with self.assertRaises(FileExistsError):
            self.imported()

    def test_missing_session_creates_no_trajectory(self):
        with self.assertRaises(ValueError):
            import_hermes(self.run,self.db,'missing')
        self.assertFalse((self.run/'trajectory.json').exists())

    def test_unknown_fail_and_versioned_rescoring(self):
        self.imported()
        unknown = self.observed({})
        failed = self.observed(dict(self.complete_state(),calendar_changed=True))
        passed = self.observed(self.complete_state())
        self.assertEqual(read_json(unknown)['status'],'unknown')
        self.assertEqual(read_json(failed)['status'],'fail')
        self.assertEqual(read_json(passed)['status'],'pass')
        self.assertEqual(len(list((self.run/'scores').glob('*.json'))),3)

    def test_self_report_cannot_be_observation(self):
        self.imported()
        path = self.root/'self.json'
        write_new(path,{'observer':'agent','observed_at':'now','method':'answer','independent_of_agent':False,'state':{}})
        with self.assertRaises(ValueError):
            verify(self.run,path)

    def test_packet_rejects_other_run_verifier(self):
        self.imported()
        score = self.observed(self.complete_state())
        data = read_json(score)
        data['run_id'] = 'other'
        fake = self.root/'fake.json'
        write_new(fake,data)
        with self.assertRaises(ValueError):
            judge_packet(self.run,fake)

    def test_judge_evidence_and_state_gating(self):
        self.imported()
        score = self.observed(dict(self.complete_state(),calendar_changed=True))
        packet = judge_packet(self.run,score)
        dimensions = [{'id':r['id'],'score':1,'evidence_event_ids':['hermes-message-3'],'rationale':'observed'}
                      for r in read_json(self.run/'task.json')['judge_rubric']]
        response = self.root/'response.json'
        write_new(response,{'verdict':'pass','dimensions':dimensions,'limitations':[]})
        with self.assertRaises(ValueError):
            import_judgment(self.run,packet,response,'judge','v1')
        response2 = self.root/'response2.json'
        dimensions[0]['evidence_event_ids']=['imaginary-event']
        write_new(response2,{'verdict':'fail','dimensions':dimensions,'limitations':[]})
        with self.assertRaises(ValueError):
            import_judgment(self.run,packet,response2,'judge','v1')

    def test_valid_judgment_keeps_raw_immutable(self):
        self.imported()
        raw = (self.run/'trajectory.json').read_bytes()
        score = self.observed(self.complete_state())
        packet = judge_packet(self.run,score)
        dimensions = [{'id':r['id'],'score':0.5,'evidence_event_ids':['hermes-message-3'],'rationale':'partial'}
                      for r in read_json(self.run/'task.json')['judge_rubric']]
        response = self.root/'response.json'
        write_new(response,{'verdict':'partial','dimensions':dimensions,'limitations':['synthetic']})
        out = import_judgment(self.run,packet,response,'judge','v1')
        self.assertEqual(read_json(out)['judgment']['verdict'],'partial')
        self.assertEqual(raw,(self.run/'trajectory.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
