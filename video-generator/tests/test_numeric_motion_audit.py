import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from audit_numeric_motion import geometry, observe


class NumericOutputAuditTests(unittest.TestCase):
    def fixture(self,grammar='cumulative_change',factor=1,same_color=False):
        diagram=dict(grammar=grammar,comparison_scale_max=45,nodes=[
            dict(id=f'n{i}',quantity=value,color=color,change_at=at)
            for i,(value,color,at) in enumerate(zip([10,20,15],['#00FF00','#FF0000','#00FF00'],[.1,.4,.7]))])
        if same_color:
            for node in diagram['nodes']: node['color']='#00FF00'
        frames=np.zeros((240,360,640,3),dtype=np.uint8)
        for node,(x,y,w,h) in zip(diagram['nodes'],geometry(diagram)):
            color=[int(node['color'][i:i+2],16) for i in (1,3,5)]
            left=round(20+x*.6); right=round(left+w*.6*factor)
            frames[round(node['change_at']*240):,round(y*.6):round((y+h)*.6),left:right]=color
        return diagram,frames

    def test_arbitrary_values_and_repeated_nonadjacent_accents(self):
        for grammar in ('cumulative_change','quantitative_comparison'):
            diagram,frames=self.fixture(grammar)
            self.assertEqual([],observe(frames,diagram,10)['findings'])

    def test_frozen_reverse_and_overwide_are_rejected(self):
        diagram,frames=self.fixture('quantitative_comparison')
        for invalid in (frames[::-1],np.repeat(frames[:1],240,axis=0),np.repeat(frames[-1:],240,axis=0)):
            self.assertTrue(observe(invalid,diagram,10)['findings'])
        diagram,frames=self.fixture('quantitative_comparison',factor=1.2)
        self.assertTrue(any('wrong_final_quantity' in f for f in observe(frames,diagram,10)['findings']))

    def test_same_adjacent_color_measures_cumulative_checkpoints(self):
        diagram,frames=self.fixture(same_color=True)
        result=observe(frames,diagram,10)
        self.assertEqual([],result['findings'])
        self.assertEqual('cumulative_checkpoints_not_individual_layer_edges',result['measurement_kind'])
        self.assertEqual(3,len(result['cumulative_width_px']))
        for invalid in (frames[::-1],np.repeat(frames[:1],240,axis=0),np.repeat(frames[-1:],240,axis=0)):
            self.assertTrue(observe(invalid,diagram,10)['findings'])

    def test_correct_final_total_does_not_hide_wrong_intermediate_amount(self):
        diagram,frames=self.fixture(same_color=True)
        frames[24:96,:,84+64:]=0
        result=observe(frames,diagram,10)
        self.assertTrue(any('wrong_cumulative_quantity' in f for f in result['findings']))
        self.assertAlmostEqual(result['expected_cumulative_width_px'][-1],result['final_total_width_px'],delta=1)

    def test_snapshot_tracks_zero_extreme_and_wrong_geometry(self):
        for layout in ('rows','dot_tracks'):
            for quantities in ((0,100),(80,35),(45,45)):
                pair=dict(color='#00FF00',scale_max=100,before=dict(value=quantities[0],show_at=.1),after=dict(value=quantities[1],show_at=.5))
                diagram=dict(grammar='before_after',snapshot_pair=pair)
                frames=np.zeros((120,360,640,3),dtype=np.uint8)
                yy,xx=np.ogrid[:360,:640]
                for j,state in enumerate((pair['before'],pair['after'])):
                    y=(250+j*140)*.6; start=20+220*.6; end=start+560*.6*state['value']/100
                    if layout=='rows': mask=(xx>=start)&(xx<end)&(abs(yy-y)<8)
                    else: mask=(xx-end)**2+(yy-y)**2<7.2**2
                    frames[round(state['show_at']*120):,mask]=[0,255,0]
                self.assertEqual([],observe(frames,diagram,5,snapshot_layout=layout)['findings'])
                shifted=np.roll(frames,18,axis=2)
                self.assertTrue(observe(shifted,diagram,5,snapshot_layout=layout)['findings'])
                reversed_frames=frames[::-1]
                self.assertTrue(observe(reversed_frames,diagram,5,snapshot_layout=layout)['findings'])
