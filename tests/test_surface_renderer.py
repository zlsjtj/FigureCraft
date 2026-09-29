"""Visibility and camera checks for the optional opaque surface backend."""
import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from surface_renderer import render
from probe_runtime import probe

class SurfaceRendererTests(unittest.TestCase):
    def test_probe_availability_is_not_execution(self):
        result=probe()['optional_3d']
        self.assertTrue(result['available'])
        self.assertTrue(Path(result['module_path']).is_file())
        self.assertEqual(result['status'],'NOT_RUN')
        self.assertIn('contact shadows',result['unsupported'])
    def test_visible_face_not_input_order(self):
        def f(z,role):return {'p':np.array([[-1.,-1,z],[1,-1,z],[1,1,z],[-1,1,z]]),'n':np.array([0.,0,1]),'role':role,'color':'#aabbcc'}
        faces=[f(0,'far'),f(1,'near')];args=([1,0,0],[0,1,0],[0,0,1])
        a,mask,_,_,rec=render(faces,*args,px_per_unit=20)
        b,_,_,_,_=render(faces[::-1],*args,px_per_unit=20)
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertTrue(all(s['role_id']==rec['roles']['near'] and abs(s['depth']-1)<1e-9 for s in rec['visibility_samples']))
    def test_bad_camera_and_light(self):
        f={'p':np.array([[0.,0,0],[1,0,0],[0,1,0]]),'n':np.array([0.,0,1]),'role':'demo','color':'#aabbcc'}
        with self.assertRaises(ValueError):render([f],[2,0,0],[0,1,0],[0,0,1])
        with self.assertRaises(ValueError):render([f],[1,0,0],[0,1,0],[0,0,1],light=(0,0,0))
if __name__=='__main__':unittest.main()
