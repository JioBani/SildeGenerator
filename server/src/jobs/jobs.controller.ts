import { Body, Controller, Delete, Get, HttpCode, NotFoundException, Param, ParseIntPipe, ParseUUIDPipe, Post, Query, Req, Sse, StreamableFile, UploadedFile, UseInterceptors } from "@nestjs/common";
import { concatMap, interval, map, startWith, takeWhile } from "rxjs";
import { FileInterceptor } from "@nestjs/platform-express";
import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { Public } from "../auth/public.decorator";
import type { UserRequest } from '../auth/token.guard';
import { CreateJobDto } from "./dto/create-job.dto";
import { EstimateJobDto } from "./dto/estimate-job.dto";
import { ReviewJobDto } from "./dto/review-job.dto";
import { JobsService } from "./jobs.service";
import { config } from "../config/app-config";
import { MUSIC_MAX_BYTES } from "./music-upload";

@Controller("jobs")
export class JobsController {
  constructor(private readonly jobs: JobsService) {}

  @Post()
  @HttpCode(202)
  create(@Body() dto: CreateJobDto, @Req() req: UserRequest) {
    return this.jobs.create(dto.scenario, req.userId, dto.imageModel, dto.continuityEnabled ?? false, dto.imageStyle, dto.harnessId, dto.narrationSpeed, dto.aspectRatio, dto.subtitlesEnabled, undefined, dto.motionStyleId, dto.sceneVisualMode, dto.musicMode, dto.musicUploadId);
  }

  @Public()
  @Get("options/harnesses")
  harnesses() { return this.jobs.harnesses(); }

  @Public()
  @Get("options/production")
  production() { return {
    imageProvider: config.imageProvider,
    imageGenerationPausedUntilUnix: config.imageGenerationPausedUntilUnix,
    supportedImageModels: config.imageProvider === "oauth" ? ["gpt-image-2"] : undefined,
    motionImageProvider: config.motionLocalProduction && config.runnerMode === "live" ? "local_graphic" : config.imageProvider,
    motionProductionAvailable: !config.motionLocalProduction || config.runnerMode === "live",
    slideV05LocalImages: config.slideV05LocalImages,
    voiceProvider: config.voiceProvider,
  }; }

  @Public()
  @Post("estimate")
  estimate(@Body() dto: EstimateJobDto) { return this.jobs.estimate(dto.scenario, dto.narrationSpeed, dto.harnessId); }

  @Get()
  list(@Req() req: UserRequest, @Query('offset') offset?: string) {
    const pageOffset = Number(offset ?? 0);
    return this.jobs.list(req.userId, Number.isInteger(pageOffset) && pageOffset >= 0 ? Math.min(pageOffset, 10000) : 0);
  }

  @Get('notifications')
  notifications(@Req() req: UserRequest) { return this.jobs.notifications(req.userId); }

  @Get('wallet')
  wallet(@Req() req: UserRequest) { return this.jobs.wallet(req.userId); }

  @Post('music')
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: MUSIC_MAX_BYTES } }))
  uploadMusic(@UploadedFile() file: { buffer: Buffer; originalname: string } | undefined, @Req() req: UserRequest) {
    return this.jobs.uploadMusic(req.userId, file);
  }

  @Get('music/:id')
  async music(@Param('id', ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    const upload = await this.jobs.getMusicUpload(req.userId, id);
    const info = await stat(upload.path);
    return new StreamableFile(createReadStream(upload.path), { type: upload.mimeType, length: info.size });
  }

  @Delete('music/:id')
  deleteMusic(@Param('id', ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    return this.jobs.deleteMusicUpload(req.userId, id);
  }

  @Post('notifications/:id/read')
  readNotification(@Param('id', ParseIntPipe) id: number, @Req() req: UserRequest) {
    return this.jobs.readNotification(req.userId, String(id));
  }

  @Get(":id")
  get(@Param("id", ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    return this.jobs.get(id, req.userId);
  }

  @Sse(":id/events")
  async events(@Param("id", ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    if (!config.slideV05LocalImages) throw new NotFoundException();
    const first = await this.jobs.get(id, req.userId);
    return interval(2000).pipe(
      startWith(-1),
      concatMap((tick) => tick === -1 ? Promise.resolve(first) : this.jobs.get(id, req.userId)),
      takeWhile((job) => !["completed", "failed"].includes(job.status), true),
      map((job) => ({ data: job })),
    );
  }

  @Get(":id/video")
  async video(@Param("id", ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    const { file, size } = await this.jobs.getVideo(id, req.userId);
    return new StreamableFile(file.createReadStream(), {
      type: "video/mp4",
      length: size,
      disposition: `attachment; filename="slide-${id}.mp4"`,
    });
  }

  @Post(":id/remake")
  @HttpCode(202)
  remake(@Param("id", ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    return this.jobs.remake(id, req.userId);
  }

  @Get(':id/thumbnail')
  async thumbnail(@Param('id', ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    const { file, size } = await this.jobs.getThumbnail(id, req.userId);
    return new StreamableFile(file.createReadStream(), { type: 'image/png', length: size });
  }

  @Post(":id/review")
  review(@Param("id", ParseUUIDPipe) id: string, @Body() dto: ReviewJobDto, @Req() req: UserRequest) {
    return this.jobs.review(id, req.userId, dto.verdict, dto.note);
  }
}
