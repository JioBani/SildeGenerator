import { BadRequestException, ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import { createHash, randomUUID } from "node:crypto";
import { mkdir, readFile, rename, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { config } from "../config/app-config";
import { DatabaseService } from "../database/database.service";
import { PROMPT_CATALOG, type PromptDefinition } from "./prompt-catalog";

type PromptRecord = PromptDefinition & {
  exists: boolean;
  content: string;
  sha256: string | null;
  modifiedAt: string | null;
  version: number | null;
};

const sha256 = (content: string) => createHash("sha256").update(content, "utf8").digest("hex");

@Injectable()
export class PromptsService {
  private readonly root = config.promptsDir;

  constructor(private readonly db: DatabaseService) {}

  private definition(id: string) {
    const definition = PROMPT_CATALOG.find((item) => item.id === id);
    if (!definition) throw new NotFoundException("등록되지 않은 프롬프트입니다.");
    return definition;
  }

  private target(definition: PromptDefinition) {
    const target = path.resolve(this.root, definition.relativePath);
    if (target !== this.root && !target.startsWith(`${this.root}${path.sep}`)) {
      throw new BadRequestException("잘못된 프롬프트 경로입니다.");
    }
    return target;
  }

  private async record(definition: PromptDefinition): Promise<PromptRecord> {
    const target = this.target(definition);
    try {
      const [content, info] = await Promise.all([readFile(target, "utf8"), stat(target)]);
      const digest = sha256(content);
      const version = await this.ensureVersion(definition.relativePath, digest, content);
      return {
        ...definition,
        exists: true,
        content,
        sha256: digest,
        modifiedAt: info.mtime.toISOString(),
        version,
      };
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
      return { ...definition, exists: false, content: "", sha256: null, modifiedAt: null, version: null };
    }
  }

  async list() {
    return Promise.all(PROMPT_CATALOG.map((definition) => this.record(definition)));
  }

  async update(id: string, content: string, expectedSha256?: string) {
    if (!content.trim()) throw new BadRequestException("프롬프트 내용은 비워둘 수 없습니다.");
    const definition = this.definition(id);
    const current = await this.record(definition);
    if (expectedSha256 && current.sha256 !== expectedSha256) {
      throw new ConflictException("다른 사용자가 먼저 수정했습니다. 새로고침 후 다시 시도해 주세요.");
    }
    for (const variable of definition.requiredVariables) {
      if (!content.includes(variable)) {
        throw new BadRequestException(`필수 변수 ${variable}가 필요합니다.`);
      }
    }
    let normalized = content.replace(/\r\n?/g, "\n");
    if (!normalized.endsWith("\n")) normalized += "\n";
    if (current.exists && current.content === normalized) return current;

    const target = this.target(definition);
    await mkdir(path.dirname(target), { recursive: true });
    const temporary = path.join(path.dirname(target), `.${path.basename(target)}.${randomUUID()}.tmp`);
    await writeFile(temporary, normalized, { encoding: "utf8", mode: 0o644 });
    await rename(temporary, target);
    return this.record(definition);
  }

  async versions(id: string) {
    const definition = this.definition(id);
    const current = await this.record(definition);
    const rows = await this.db.query(`SELECT version,sha256,content,created_at AS "createdAt"
      FROM prompt_versions WHERE relative_path=$1 ORDER BY version DESC`, [definition.relativePath]);
    return rows.rows.map((row) => ({ ...row, current: row.sha256 === current.sha256 }));
  }

  async restore(id: string, version: number, expectedSha256?: string) {
    const definition = this.definition(id);
    const found = await this.db.query<{ content: string }>(`SELECT content FROM prompt_versions WHERE relative_path=$1 AND version=$2`, [definition.relativePath, version]);
    if (!found.rows[0]) throw new NotFoundException("해당 프롬프트 버전을 찾을 수 없습니다.");
    return this.update(id, found.rows[0].content, expectedSha256);
  }

  private async ensureVersion(relativePath: string, digest: string, content: string): Promise<number> {
    return this.db.transaction(async (client) => {
      await client.query(`SELECT pg_advisory_xact_lock(hashtext($1))`, [relativePath]);
      const existing = await client.query<{ version: number }>(`SELECT version FROM prompt_versions WHERE relative_path=$1 AND sha256=$2`, [relativePath, digest]);
      if (existing.rows[0]) return existing.rows[0].version;
      const inserted = await client.query<{ version: number }>(`INSERT INTO prompt_versions(relative_path,version,sha256,content)
        SELECT $1,coalesce(max(version),0)+1,$2,$3 FROM prompt_versions WHERE relative_path=$1 RETURNING version`, [relativePath, digest, content]);
      return inserted.rows[0].version;
    });
  }
}
