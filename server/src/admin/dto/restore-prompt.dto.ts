import { IsOptional, IsString, Length } from "class-validator";

export class RestorePromptDto {
  @IsOptional()
  @IsString()
  @Length(64, 64)
  expectedSha256?: string;
}
