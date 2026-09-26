import unittest

from app.models import RenderRequest
from app.narration_input import require_narration_only


class NarrationInputTests(unittest.TestCase):
    def test_production_rejects_storyboard_headers(self):
        for header in ("🎬 영상 제목: 반물질", "(00:00~00:08) 도입부 (Hook)",
                       "[03~20초] 본론 1", "**화면:** 붉은 선", "나레이션: 문장", "### 결론"):
            with self.subTest(header=header), self.assertRaisesRegex(ValueError, "음성 대본"):
                RenderRequest(job_id="00000000-0000-0000-0000-000000000001",
                              production_job=True, scenario=header + "\n읽을 문장입니다.")

    def test_parentheses_and_spoken_numbers_remain_valid(self):
        text = "반물질(Antimatter)은 어렵습니다.\n지금 시간은 00:08입니다.\n가격(1g 기준)을 살펴봅니다.\n결론은 아직 모릅니다."
        require_narration_only(text)
        self.assertEqual(RenderRequest(job_id="00000000-0000-0000-0000-000000000001",
                                       production_job=True, scenario=text).scenario, text)

    def test_visual_cues_are_allowed_only_in_the_separate_field(self):
        request = RenderRequest(job_id="00000000-0000-0000-0000-000000000001", production_job=True,
                                scenario="첫 문장입니다.", visual_cues=[{"timeCue": "00~03초", "direction": "화면: 도형", "narration": "첫 문장입니다."}])
        self.assertEqual(request.scenario, "첫 문장입니다.")

    def test_research_requests_keep_their_existing_contract(self):
        request = RenderRequest(job_id="00000000-0000-0000-0000-000000000001",
                                scenario="(00:00~00:08) 시험용 입력")
        self.assertFalse(request.production_job)


if __name__ == "__main__":
    unittest.main()
