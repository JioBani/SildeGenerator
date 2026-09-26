import { IsIn, IsOptional, IsString, MaxLength } from "class-validator";

export class ReviewJobDto {
  @IsIn(["APPROVED", "REVISION_REQUIRED"])
  verdict!: "APPROVED" | "REVISION_REQUIRED";

  @IsOptional()
  @IsString()
  @MaxLength(1000)
  note?: string;
}
