import { IsIn, IsNotEmpty, IsNumber, IsOptional, IsString, Max, MaxLength, Min } from "class-validator";
import { config } from "../../config/app-config";

export class EstimateJobDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(config.maxScenarioChars)
  scenario!: string;

  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0.7)
  @Max(1.2)
  narrationSpeed!: number;

  @IsOptional()
  @IsIn(["astra-motion", "classic-slide", "cinematic-slide", "narrative-slide", "hybrid-story"])
  harnessId?: string;
}
