import { IsOptional, IsString, Length, MaxLength } from "class-validator";

export class UpdatePromptDto {
  @IsString()
  @MaxLength(60_000)
  content!: string;

  @IsOptional()
  @IsString()
  @Length(64, 64)
  expectedSha256?: string;
}
