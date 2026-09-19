import { Logger } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";
import { config } from "./config/app-config";
import { WorkerModule } from "./worker/worker.module";

async function bootstrap() {
  const app = await NestFactory.createApplicationContext(WorkerModule);
  app.enableShutdownHooks();
  new Logger("Worker").log(`runner=http url=${config.runnerUrl} concurrency=${config.concurrency} videoJobGlobalConcurrency=${config.videoJobGlobalConcurrency} timeoutMs=${config.jobTimeoutMs}`);
}

void bootstrap();
