import { BullModule } from "@nestjs/bullmq";
import { Module } from "@nestjs/common";
import { APP_GUARD } from "@nestjs/core";
import { TokenGuard } from "./auth/token.guard";
import { redisConnection } from "./config/app-config";
import { JobsModule } from "./jobs/jobs.module";
import { TestController } from "./test/test.controller";
import { AdminModule } from "./admin/admin.module";
import { DatabaseModule } from "./database/database.module";
import { MetricsModule } from "./metrics/metrics.module";
import { HealthController } from "./health/health.controller";
import { SettingsModule } from "./settings/settings.module";

@Module({
  imports: [DatabaseModule, SettingsModule, MetricsModule, BullModule.forRoot({ connection: redisConnection() }), JobsModule, AdminModule],
  controllers: [TestController, HealthController],
  providers: [{ provide: APP_GUARD, useClass: TokenGuard }],
})
export class AppModule {}
