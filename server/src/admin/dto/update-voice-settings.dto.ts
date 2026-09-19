import { IsIn, IsNumber, IsOptional, IsString, Max, Min } from "class-validator";
import { VOICE_PROVIDERS, type VoiceProvider } from "../../shared/voice-settings";

export class UpdateVoiceSettingsDto {
  @IsIn(VOICE_PROVIDERS) provider!: VoiceProvider;
  @IsOptional() @IsString() model?: string;
  @IsOptional() @IsString() voiceId?: string;
  @IsOptional() @IsString() voiceName?: string;
  @IsOptional() @IsString() rate?: string;
  @IsOptional() @IsString() pitch?: string;
  @IsOptional() @IsString() volume?: string;
  @IsOptional() @IsNumber() @Min(0) @Max(1) stability?: number;
  @IsOptional() @IsNumber() @Min(0) @Max(1) similarityBoost?: number;
  @IsOptional() @IsNumber() @Min(0.7) @Max(1.2) speed?: number;
}
