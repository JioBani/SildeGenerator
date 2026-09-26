import { Transform } from "class-transformer";
import { IsBoolean, IsIn, IsNotEmpty, IsNumber, IsOptional, IsString, IsUUID, Matches, Max, MaxLength, Min } from "class-validator";
import { config } from "../../config/app-config";
import { IMAGE_MODELS, type ImageModel } from "../../shared/image-model";
import { IMAGE_STYLES, type ImageStyle } from "../../shared/image-style";
import { MOTION_STYLE_IDS, type MotionStyleId } from "../../shared/motion-style";

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
  @IsIn(MOTION_STYLE_IDS)
  motionStyleId?: MotionStyleId;

  @IsOptional()
  @IsIn(["local_illustration"])
  sceneVisualMode?: "local_illustration";

  @IsOptional()
  @IsIn(["none", "auto", "upload"])
  musicMode?: "none" | "auto" | "upload";

  @IsOptional()
  @IsUUID()
  musicUploadId?: string;

  @IsOptional()
  @IsString()
  @Matches(/^[a-z][a-z0-9-]{1,63}$/)
  harnessId?: string;

  @IsOptional()
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0.7)
  @Max(1.2)
  narrationSpeed?: number;

  @IsOptional()
  @IsIn(["16:9", "9:16"])
  aspectRatio?: "16:9" | "9:16";

  @IsOptional()
  @IsBoolean()
  subtitlesEnabled?: boolean;
}
