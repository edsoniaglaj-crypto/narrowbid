import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from fetch_tenders import normalize, get_cpv, categories

EXAMPLE={
    'id':'079001-2026','ocid':'ocds-test-12','date':'2026-11-21T12:00:00Z','tag':['tender'],
    'buyer':{'name':'Test UK Council'},
    'tender':{'title':'Website redesign services','description':'Web design and digital content',
    'value':{'amount':42000,'currency':'GBP'},'tenderPeriod':{'endDate':'2027-01-05T16:00:00Z'},
    'items':[{'additionalClassifications':[{'scheme':'CPV','id':'72413000'}]}]}
}

class TestNotice(unittest.TestCase):
    def test_normalized_real_identifier(self):
        d=normalize(EXAMPLE)
        self.assertEqual(d['buyer'],'Test UK Council')
        self.assertTrue(d['url'].endswith('/Notice/079001-2026'))
        self.assertIn('web',d['tags'])
        self.assertEqual(d['value'],42000)
    def test_award_excluded(self):
        d={**EXAMPLE,'tag':['award']}
        self.assertIsNone(normalize(d))
    def test_cancelled_excluded(self):
        d={**EXAMPLE,'tender':{**EXAMPLE['tender'],'status':'cancelled'}}
        self.assertIsNone(normalize(d))
    def test_non_creative_excluded(self):
        d={**EXAMPLE,'tender':{'title':'Supply of gravel','description':'Sand and gravel','value':{},'tenderPeriod':{}}}
        self.assertIsNone(normalize(d))
    def test_no_source_link_excluded(self):
        d={**EXAMPLE,'id':'irrelevant-id','tender':{**EXAMPLE['tender'],'id':'id-bad'}}
        self.assertIsNone(normalize(d))

if __name__=='__main__':unittest.main()
