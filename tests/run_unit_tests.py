"""Discover actual unit modules and preserve skips/errors separately."""
from pathlib import Path
import argparse,json,unittest,sys
class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.rows=[]
    def addSuccess(self,t):super().addSuccess(t);self.rows.append({'test':t.id(),'status':'PASS'})
    def addSkip(self,t,why):super().addSkip(t,why);self.rows.append({'test':t.id(),'status':'SKIPPED','reason':why})
    def addFailure(self,t,err):super().addFailure(t,err);self.rows.append({'test':t.id(),'status':'FAIL','reason':self._exc_info_to_string(err,t)})
    def addError(self,t,err):
        super().addError(t,err);reason=self._exc_info_to_string(err,t);self.rows.append({'test':t.id(),'status':'MISSING_DEPENDENCY' if 'ModuleNotFoundError' in reason else 'ERROR','reason':reason})
    def addSubTest(self,t,subtest,err):
        super().addSubTest(t,subtest,err)
        if err is not None:self.rows.append({'test':subtest.id(),'status':'FAIL','reason':self._exc_info_to_string(err,t)})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parent
    suite=unittest.defaultTestLoader.discover(str(root),pattern='test_*.py');r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
    status='FAIL' if r.errors or r.failures else 'PARTIAL' if r.skipped or not r.testsRun else 'PASS'
    data={'status':status,'count':r.testsRun,'tests':r.rows,'modules':sorted(x.name for x in root.glob('test_*.py')),'effect_review':'NOT_TESTED'}
    (a.out/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');sys.exit(0 if status=='PASS' else 1)
