import { BadGatewayException, BadRequestException, Injectable } from "@nestjs/common";
import { config } from "../config/app-config";
import { DEFAULT_HARNESS_ID, type HarnessSnapshot } from "../shared/harness";

@Injectable()
export class HarnessRegistryService {
  async list(): Promise<HarnessSnapshot[]> {
    try {
      const response = await fetch(`${config.runnerUrl}/harnesses`, { signal: AbortSignal.timeout(5000) });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json() as HarnessSnapshot[];
    } catch (error) {
      throw new BadGatewayException(`설치된 Harness 목록을 불러오지 못했습니다: ${error instanceof Error ? error.message : error}`);
    }
  }

  async resolve(id = DEFAULT_HARNESS_ID): Promise<HarnessSnapshot> {
    const harness = (await this.list()).find((item) => item.id === id && item.compatible !== false && item.public !== false);
    if (!harness) throw new BadRequestException(`사용할 수 없는 Harness입니다: ${id}`);
    return harness;
  }
}
