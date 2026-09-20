import { Transform } from "class-transformer";
import { IsBoolean, IsIn, IsNotEmpty, IsNumber, IsOptional, IsString, Matches, Max, MaxLength, Min } from "class-validator";
import { config } from "../../config/app-config";
import { IMAGE_MODELS, type ImageModel } from "../../shared/image-model";
import { IMAGE_STYLES, type ImageStyle } from "../../shared/image-style";

export class CreateJobDto {
  @Transform(({ value }) => (typeof value === "string" ? value.trim() : value))
  @IsString()
  @IsNotEmpty()
  @MaxLength(config.maxScenarioChars)
  scenario!: string;

  @IsOptional()
  @IsIn(IMAGE_MODELS)
  imageModel?: ImageModel;

  @IsOptional()
  @IsBoolean()
  continuityEnabled?: boolean;

  @IsOptional()
  @IsIn(IMAGE_STYLES)
  imageStyle?: ImageStyle;

  @IsOptional()
  @IsString()
  @Matches(/^[a-z][a-z0-9-]{1,63}$/)
  harnessId?: string;

  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0.75)
  @Max(1.5)
  narrationSpeed?: number;
}
