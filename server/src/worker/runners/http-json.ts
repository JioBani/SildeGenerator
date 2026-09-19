import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";

const MAX_RESPONSE_BYTES = 50 * 1024 * 1024;

export async function postJson(urlValue: string, body: unknown, signal: AbortSignal, headers: Record<string, string> = {}) {
  const url = new URL(urlValue);
  const payload = Buffer.from(JSON.stringify(body));
  const request = url.protocol === "https:" ? httpsRequest : httpRequest;

  return new Promise<{ status: number; text: string }>((resolve, reject) => {
    const req = request(url, {
      method: "POST",
      signal,
      headers: {
        "Content-Type": "application/json",
        "Content-Length": payload.byteLength,
        ...headers,
      },
    }, (response) => {
      const chunks: Buffer[] = [];
      let size = 0;
      response.on("data", (chunk: Buffer) => {
        size += chunk.length;
        if (size > MAX_RESPONSE_BYTES) {
          response.destroy(new Error("runner response exceeded 50 MiB"));
          return;
        }
        chunks.push(chunk);
      });
      response.on("end", () => resolve({
        status: response.statusCode ?? 0,
        text: Buffer.concat(chunks).toString("utf8"),
      }));
      response.on("error", reject);
    });
    req.on("error", reject);
    req.end(payload);
  });
}
