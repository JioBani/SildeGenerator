import asyncio
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.background_music import mix_music, verified_upload
from app.engine.process_runner import ProcessRunner


class BackgroundMusicTests(unittest.TestCase):
    def test_upload_scope_and_digest(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            uploads = root / 'music-uploads'
            uploads.mkdir()
            sound = uploads / 'source.wav'
            sound.write_bytes(b'sound')
            selection = {'path': str(sound), 'sha256': hashlib.sha256(b'sound').hexdigest()}
            self.assertEqual(verified_upload(selection, root), sound)
            selection['sha256'] = 'wrong'
            with self.assertRaises(ValueError):
                verified_upload(selection, root)
            selection['sha256'] = hashlib.sha256(b'sound').hexdigest()
            selection['path'] = str(root / 'outside.wav')
            with self.assertRaises(ValueError):
                verified_upload(selection, root)

    def test_auto_music_mixes_with_voice(self):
        async def exercise(root):
            work = root / 'work'
            work.mkdir()
            video = work / 'original.mp4'
            process = ProcessRunner()
            await process.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                               '-f', 'lavfi', '-i', 'color=c=blue:s=320x180:r=24:d=2',
                               '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
                               '-shortest', '-c:v', 'libx264', '-c:a', 'aac', str(video)])
            report = await mix_music(video, {'mode': 'auto', 'preset': 'warm-story'}, root,
                                     work, 2.0, process)
            self.assertTrue(report['applied'])
            self.assertTrue(video.is_file())
            self.assertGreater(video.stat().st_size, 1000)

        with TemporaryDirectory() as directory:
            asyncio.run(exercise(Path(directory)))


if __name__ == '__main__':
    unittest.main()
