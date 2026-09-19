import { Body, Controller, Get, HttpCode, Param, ParseUUIDPipe, Post, Req, StreamableFile } from "@nestjs/common";
import { Public } from "../auth/public.decorator";
import type { UserRequest } from '../auth/token.guard';
import { CreateJobDto } from "./dto/create-job.dto";
import { JobsService } from "./jobs.service";

@Controller("jobs")
export class JobsController {
  constructor(private readonly jobs: JobsService) {}

  @Post()
  @HttpCode(202)
  create(@Body() dto: CreateJobDto, @Req() req: UserRequest) {
    return this.jobs.create(dto.scenario, req.userId, dto.imageModel, dto.continuityEnabled ?? false, dto.imageStyle, dto.harnessId);
  }

  @Public()
  @Get("options/harnesses")
  harnesses() { return this.jobs.harnesses(); }

  @Get(":id")
  get(@Param("id", ParseUUIDPipe) id: string, @Req() req: UserRequest) {
    return this.jobs.get(id, req.userId);
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
}
