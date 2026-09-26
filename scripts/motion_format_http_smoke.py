"""Exercise the isolated, provider-free unified motion-graphics path."""
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:18771/api"
TOKEN = "local-genre-test-only"


def request(path, payload=None):
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    with urlopen(Request(BASE + path, data=data, headers=headers), timeout=30) as response:
        return response.status, json.loads(response.read() or b"{}")


def main():
    try:
        request("/jobs/options/genres")
    except HTTPError as error:
        assert error.code == 404
    else:
        raise AssertionError("The retired genre endpoint is still public")

    _, harnesses = request("/jobs/options/harnesses")
    motion = next(item for item in harnesses if item["id"] == "astra-motion")
    assert motion["public"] is True
    assert motion["display_name"] == "모션그래픽"

    _, created = request("/jobs", {
        "scenario": "하나의 원인이 상태를 바꾸고 결과를 만드는 짧은 설명입니다.",
        "harnessId": "astra-motion",
        "imageStyle": "graphic_explainer",
    })
    job_id = created["id"]
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        _, state = request(f"/jobs/{job_id}")
        if state["status"] in ("completed", "failed"):
            assert state["status"] == "completed", state
            assert state["harnessId"] == "astra-motion"
            print(json.dumps({"job_id": job_id, "status": state["status"], "harness": state["harnessId"]}))
            return
        time.sleep(1)
    raise TimeoutError(f"motion-graphics smoke job did not finish: {job_id}")


if __name__ == "__main__":
    main()
