import { Controller, Get, Req } from "@nestjs/common";
import type { UserRequest } from "../auth/token.guard";

// Connectivity check for issued API keys. Passes the global TokenGuard (auth + rate limit) like every route.
@Controller("test")
export class TestController {
  @Get()
  check(@Req() req: UserRequest) {
    return { status: "ok", message: "slidegen authenticated test response", userId: req.userId };
  }
}
