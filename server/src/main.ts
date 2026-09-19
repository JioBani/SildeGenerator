import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { json, type NextFunction, type Request, type Response } from 'express';
import { AppModule } from './app.module';
import { config } from './config/app-config';

// 브라우저는 same-origin 이라도 GET/HEAD 가 아닌 요청에 Origin 을 붙인다.
// 리버스 프록시 뒤 same-origin 배포에서는 실제 호스트가 X-Forwarded-Host 로 전달된다.
function isAllowedOrigin(req: Request) {
  const origin = req.headers.origin;
  if (!origin) return true;
  if (config.corsOrigins.includes(origin)) return true;
  const forwardedHost = req.headers['x-forwarded-host'];
  const host = typeof forwardedHost === 'string' ? forwardedHost : req.headers.host;
  if (!host || host.includes(',')) return false;
  try {
    const parsedOrigin = new URL(origin);
    return ['http:', 'https:'].includes(parsedOrigin.protocol) && parsedOrigin.host === host;
  } catch {
    return false;
  }
}
async function bootstrap() {
  const app = await NestFactory.create(AppModule, { bodyParser: false });
  app.use(json({ limit: '256kb', strict: true }));
  app.use((req: Request, res: Response, next: NextFunction) => {
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    if (!isAllowedOrigin(req)) return res.status(403).end();
    next();
  });
  app.setGlobalPrefix('api');
  if (config.corsOrigins.length) app.enableCors({ origin: config.corsOrigins, methods: ['GET', 'POST', 'PUT'], allowedHeaders: ['Authorization', 'Content-Type'], credentials: false });
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }));
  app.enableShutdownHooks();
  const server = await app.listen(config.port, '0.0.0.0');
  server.maxConnections = 128;
  server.headersTimeout = 10000;
  server.requestTimeout = 15000;
  server.keepAliveTimeout = 5000;
}
void bootstrap();
