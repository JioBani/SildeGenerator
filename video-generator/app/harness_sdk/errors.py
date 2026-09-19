class HarnessError(RuntimeError):
    pass


class ManifestValidationError(HarnessError):
    pass


class GraphValidationError(HarnessError):
    pass


class HarnessTaskError(HarnessError):
    def __init__(self, harness_id: str, version: str, task_id: str, cause: Exception):
        super().__init__(f"harness {harness_id}@{version} task {task_id} failed: {cause}")
        self.task_id = task_id
