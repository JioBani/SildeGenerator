import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harnesses/astra-transport-lab/src'))
from astra_transport_lab.scene_program import compile_scene_program
from astra_transport_lab.renderer import _timeline_js, _scene_html


def fixture():
    return SimpleNamespace(id='gpu',duration_seconds=4,scene_function='parallel_processing',
        viewer_takeaway='GPU',narration='Six independent tasks',
        object_states=[{'object_id':'jobA','role':'token','label':'A'}],
        motion=[{'object_id':'jobA','kind':'transport_track','points':[
            {'time':.5,'x':.2,'y':.5},{'time':2,'x':.8,'y':.5}]}])


class Tests(unittest.TestCase):
    def test_size_profile_is_explicit_and_bounded(self):
        scene=fixture();scene.layout={'token_size':'readable'}
        markup=_scene_html(scene,1,compile_scene_program(scene))
        self.assertIn('width:180px',markup)
        self.assertIn('font-size:36px',markup)
        scene.layout={'token_size':'arbitrary-css'}
        with self.assertRaises(ValueError):compile_scene_program(scene)

    def test_columns_are_declared_not_gpu_specific(self):
        scene=fixture();scene.layout={'columns':[{'x':.2,'label':'Queue'},{'x':.8,'label':'Done'}]}
        markup=_scene_html(scene,1,compile_scene_program(scene))
        self.assertIn('Queue',markup)
        self.assertNotIn('병렬 계산',markup)
        scene.layout={'columns':[{'x':2,'label':'bad'}]}
        with self.assertRaises(ValueError):compile_scene_program(scene)

    def test_state_text_cannot_close_script(self):
        scene=fixture()
        scene.object_states[0]['performance_states']=[{'time':1,'state':'complete','label':'</script>'}]
        js=_timeline_js([scene],[compile_scene_program(scene)])
        self.assertNotIn('</script>',js)
        self.assertIn('\\u003c/script\\u003e',js)

    def test_state_times_and_kinds_rejected(self):
        for event in ({'time':5,'state':'complete','label':'6'}, {'time':1,'state':'arbitrary','label':'6'}):
            scene=fixture();scene.object_states[0]['performance_states']=[event]
            with self.assertRaises(ValueError):compile_scene_program(scene)

    def test_compiler_and_renderer_connected(self):
        scene=fixture();program=compile_scene_program(scene)
        self.assertEqual(program['transport_tracks'][0]['id'],'jobA')
        self.assertIn('token-1-jobA',_scene_html(scene,1,program))
        self.assertIn('duration:1.5',_timeline_js([scene],[program]))

    def test_invalid_tracks(self):
        for change in ('missing','duplicate','time','nan','canvas','code'):
            with self.subTest(change=change):
                scene=fixture()
                if change=='missing':scene.object_states=[]
                if change=='duplicate':scene.motion*=2
                if change=='time':scene.motion[0]['points'][1]['time']=.1
                if change=='nan':scene.motion[0]['points'][0]['x']=float('nan')
                if change=='canvas':scene.motion[0]['points'][0]['x']=2
                if change=='code':scene.motion[0]['kind']='eval'
                with self.assertRaises(ValueError):compile_scene_program(scene)


if __name__=='__main__':unittest.main()
