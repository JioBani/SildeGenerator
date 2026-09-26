"""Schema-only check using the existing developer jsonschema installation."""
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError


class LayoutSchemaTests(unittest.TestCase):
    def test_camera_and_labels(self):
        schema = json.loads((Path(__file__).resolve().parents[1] / 'video-generator/schemas/scene-plan.schema.json').read_text())
        validator = Draft202012Validator(schema['$defs']['scene']['properties']['layout'])
        base = {'mode': 'focus', 'focal_order': ['subject'], 'safe_area': 'caption_bottom',
                'camera': None, 'continuity_group': None, 'visual_labels': []}
        validator.validate(base)
        validator.validate({**base, 'camera': {'mode': 'push', 'focus': [.7, .3], 'strength': .025},
                            'visual_labels': [{'text': 'Result', 'x': .7, 'y': .3}]})
        for camera in [{'mode': 'spin', 'focus': [.5, .5], 'strength': .02},
                       {'mode': 'push', 'focus': [2, .5], 'strength': .02},
                       {'mode': 'push', 'focus': [.5, .5], 'strength': 1}]:
            with self.assertRaises(ValidationError):
                validator.validate({**base, 'camera': camera})
        with self.assertRaises(ValidationError):
            validator.validate({**base, 'visual_labels': [{'text': 'x', 'x': -1, 'y': .5}]})


if __name__ == '__main__':
    unittest.main()
