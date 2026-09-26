import { BadRequestException } from "@nestjs/common";

export const MUSIC_MAX_BYTES = 10 * 1024 * 1024;

export function audioFormat(buffer: Buffer): { mimeType: string; extension: string } {
  if (buffer.length < 12 || buffer.length > MUSIC_MAX_BYTES) {
    throw new BadRequestException("음악 파일은 10MB 이하의 재생 가능한 파일이어야 합니다.");
  }
  if (buffer.toString("ascii", 0, 4) === "RIFF" && buffer.toString("ascii", 8, 12) === "WAVE") {
    return { mimeType: "audio/wav", extension: ".wav" };
  }
  if (buffer.toString("ascii", 0, 4) === "OggS") return { mimeType: "audio/ogg", extension: ".ogg" };
  if (buffer.toString("ascii", 4, 8) === "ftyp") return { mimeType: "audio/mp4", extension: ".m4a" };
  if (buffer.toString("ascii", 0, 3) === "ID3" || (buffer[0] === 0xff && (buffer[1] & 0xe0) === 0xe0)) {
    return { mimeType: "audio/mpeg", extension: ".mp3" };
  }
  throw new BadRequestException("MP3, WAV, M4A 또는 OGG 음악 파일만 사용할 수 있습니다.");
}
