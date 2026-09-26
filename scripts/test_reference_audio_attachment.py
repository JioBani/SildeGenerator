import unittest
from compile_reference_atlas import attach_audio


class AudioAttachmentTest(unittest.TestCase):
    def fixture(self):
        scene={'source_window':[0,1], 'scene_function':'explain', 'render_authorized':False}
        report={'source_sha256':'source','atlas_sha256':'atlas','scope':'RMS only',
                'partitions':[{'range':[0,1],'scene_function':'explain'}]}
        return [scene], report

    def test_measurement_does_not_approve(self):
        scenes,report=self.fixture()
        attach_audio(scenes,report,'source','atlas',{'file':'report.json'})
        self.assertFalse(scenes[0]['render_authorized'])
        self.assertFalse(scenes[0]['rhythm']['audio_reuse_authorized'])
        self.assertIsNone(scenes[0]['rhythm']['speech_alignment'])

    def test_wrong_source_rejected(self):
        scenes,report=self.fixture()
        with self.assertRaises(ValueError):attach_audio(scenes,report,'other','atlas',{})

    def test_stale_atlas_rejected(self):
        scenes,report=self.fixture()
        with self.assertRaises(ValueError):attach_audio(scenes,report,'source','other',{})

    def test_wrong_interval_rejected(self):
        scenes,report=self.fixture();report['partitions'][0]['range']=[0,2]
        with self.assertRaises(ValueError):attach_audio(scenes,report,'source','atlas',{})


if __name__=='__main__':unittest.main()
