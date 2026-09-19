import { Global, Module } from "@nestjs/common";
import { CodexSettingsService } from "./codex-settings.service";
import { VoiceSettingsService } from "./voice-settings.service";

@Global()
@Module({ providers: [CodexSettingsService, VoiceSettingsService], exports: [CodexSettingsService, VoiceSettingsService] })
export class SettingsModule {}
