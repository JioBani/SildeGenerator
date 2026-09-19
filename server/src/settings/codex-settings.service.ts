import { BadRequestException, Injectable } from "@nestjs/common";
import { config } from "../config/app-config";
import { DatabaseService } from "../database/database.service";

export const CODEX_EFFORTS = ["low", "medium", "high", "xhigh", "max"] as const;
export type CodexEffort = typeof CODEX_EFFORTS[number];
export type CodexRuntimeSettings = { model: string; effort: CodexEffort; fastMode: boolean };

@Injectable()
export class CodexSettingsService {
  constructor(private readonly db: DatabaseService) {}

  private defaults(): CodexRuntimeSettings {
    const effort = CODEX_EFFORTS.includes(config.codexReasoningEffort as CodexEffort)
      ? config.codexReasoningEffort as CodexEffort
      : "max";
    return { model: config.codexModel, effort, fastMode: config.codexFastMode };
  }

  async get() {
    const result = await this.db.query<{ value: Partial<CodexRuntimeSettings>; updated_at: Date }>(
      `SELECT value,updated_at FROM runtime_settings WHERE key='codex_generation'`,
    );
    const value = { ...this.defaults(), ...(result.rows[0]?.value ?? {}) };
    return {
      ...this.validate(value),
      modelOptions: config.codexModelOptions,
      effortOptions: CODEX_EFFORTS,
      updatedAt: result.rows[0]?.updated_at ?? null,
    };
  }

  async update(value: CodexRuntimeSettings) {
    const validated = this.validate(value);
    const result = await this.db.query<{ updated_at: Date }>(`INSERT INTO runtime_settings(key,value,updated_at)
      VALUES('codex_generation',$1,now())
      ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=now()
      RETURNING updated_at`, [validated]);
    return {
      ...validated,
      modelOptions: config.codexModelOptions,
      effortOptions: CODEX_EFFORTS,
      updatedAt: result.rows[0].updated_at,
    };
  }

  private validate(value: Partial<CodexRuntimeSettings>): CodexRuntimeSettings {
    if (!value.model || !config.codexModelOptions.includes(value.model)) {
      throw new BadRequestException("지원하는 Codex 모델을 선택해 주세요.");
    }
    if (!value.effort || !CODEX_EFFORTS.includes(value.effort as CodexEffort)) {
      throw new BadRequestException("지원하는 reasoning effort를 선택해 주세요.");
    }
    if (typeof value.fastMode !== "boolean") {
      throw new BadRequestException("fast 모드 값이 올바르지 않습니다.");
    }
    return { model: value.model, effort: value.effort as CodexEffort, fastMode: value.fastMode };
  }
}
