import { CanActivate, ExecutionContext, HttpException, ForbiddenException, Injectable, OnModuleDestroy, UnauthorizedException } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import type { Request } from 'express';
import Redis from 'ioredis';
import { config, redisConnection } from '../config/app-config';
import { hashKey, readKeys } from './key-store';
import { IS_PUBLIC } from './public.decorator';
export type UserRequest = Request & { userId: string };
@Injectable()
export class TokenGuard implements CanActivate, OnModuleDestroy {
  private readonly redis = new Redis(redisConnection());
  constructor(private readonly reflector: Reflector) {}
  onModuleDestroy() { this.redis.disconnect(); }
  async canActivate(context: ExecutionContext) {
    if (this.reflector.getAllAndOverride<boolean>(IS_PUBLIC, [context.getHandler(), context.getClass()])) return true;
    const req = context.switchToHttp().getRequest<UserRequest>();
    const match = /^Bearer (\S{6,256})$/.exec(req.headers.authorization || '');
    let record;
    try { record = match && readKeys()[hashKey(match[1])]; } catch { throw new UnauthorizedException(); }
    if (!record || record.revokedAt) throw new UnauthorizedException();
    if (!['GET', 'POST'].includes(req.method)) throw new ForbiddenException();
    req.userId = record.userId;
    const count = await this.redis.eval(`local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n`, 1, `limits:rate:${record.userId}`);
    if (Number(count) > config.requestsPerMinute) throw new HttpException('request rate exceeded', 429);
    return true;
  }
}
