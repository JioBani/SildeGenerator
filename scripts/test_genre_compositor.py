import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harnesses/genre-slide/src'))
from genre_slide.compositor import compile_project

DESIGN={'version':'scene-design-1','rationale':'장면의 핵심 의미와 읽기 순서에 맞춘 시험 설계입니다.',
    'background':'#F6F8FA','foreground':'#172B32','accent':'#D74E42',
    'caption_background':'#102025','caption_foreground':'#FFFFFF',
    'media_box':[.07,.24,.86,.54],'title_box':[.07,.06,.86,.14],'caption_box':[.07,.82,.86,.14],
    'image_fit':'contain','media_treatment':'none','entry_motion':'fade',
    'title_size':54,'caption_size':32,'title_weight':700}


class GenreCompositionTests(unittest.TestCase):
    def test_director_authored_designs_escape_text_and_declare_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);runtime=root/'runtime'
            js=runtime/'node_modules/gsap/dist/gsap.min.js';js.parent.mkdir(parents=True);js.write_text('')
            asset=root/'image.svg';asset.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            composition_ids=[]
            for genre in ('knowledge','history','tutorial','character','cartoon','documentary'):
                scene=SimpleNamespace(id='s1',image_path=asset,duration_seconds=4,
                    viewer_takeaway='<script>bad</script>',narration='원문',layout={'genre_id':genre,'authored_design':DESIGN})
                compile_project([scene],root/genre,SimpleNamespace(width=1920,height=1080,fps=30),runtime)
                html=(root/genre/'index.html').read_text(encoding='utf8')
                self.assertIn('class="scene"',html)
                self.assertIn('<head><meta charset="utf-8"><title>Director Scene</title>',html)
                self.assertIn("@font-face{font-family:'Noto Sans CJK KR'",html)
                self.assertNotIn('<script>bad',html)
                self.assertIn('원문',html)
                metadata=__import__('json').loads((root/genre/'meta.json').read_text(encoding='utf8'))
                composition_ids.append(metadata['name'])
                self.assertIn(f'data-composition-id="{metadata["name"]}"',html)
                self.assertIn(f"window.__timelines['{metadata['name']}']=tl",html)
                if genre in ('history','documentary'):self.assertIn('자료 출처 확인 필요',html)
            self.assertEqual(6,len(set(composition_ids)))
            scene.layout={'genre_id':'tutorial','authored_design':DESIGN,'visual_labels':[{'x':.5,'y':.8,'text':'<b>file</b>'}]}
            compile_project([scene],root/'label',SimpleNamespace(width=1920,height=1080,fps=30),runtime)
            markup=(root/'label/index.html').read_text(encoding='utf8')
            self.assertIn('&lt;b&gt;file&lt;/b&gt;',markup)
            for bad in ({'x':float('nan'),'y':.8,'text':'file'}, {'x':1,'y':.8,'text':'file'}, {'x':.5,'y':.8,'text':''}):
                scene.layout['visual_labels']=[bad]
                with self.assertRaises(ValueError):
                    compile_project([scene],root/'invalid',SimpleNamespace(width=1920,height=1080,fps=30),runtime)

    def test_missing_director_design_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); runtime=root/'runtime'; asset=root/'image.svg'
            js=runtime/'node_modules/gsap/dist/gsap.min.js';js.parent.mkdir(parents=True);js.write_text('')
            asset.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            scene=SimpleNamespace(id='s1',image_path=asset,duration_seconds=4,
                viewer_takeaway='빈 틀 금지',narration='원문',layout={'genre_id':'knowledge'})
            with self.assertRaisesRegex(ValueError,'Scene Design Contract required'):
                compile_project([scene],root/'blocked',SimpleNamespace(width=1920,height=1080,fps=30),runtime)


if __name__=='__main__':unittest.main()
