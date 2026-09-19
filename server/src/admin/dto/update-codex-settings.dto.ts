import { IsBoolean, IsIn, IsString } from "class-validator";
import { config } from "../../config/app-config";
import { CODEX_EFFORTS } from "../../settings/codex-settings.service";

export class UpdateCodexSettingsDto {
  @IsString()
  @IsIn(config.codexModelOptions)
  model!: string;

  @IsString()
  @IsIn(CODEX_EFFORTS)
  effort!: "low" | "medium" | "high" | "xhigh" | "max";

  @IsBoolean()
  fastMode!: boolean;
}
