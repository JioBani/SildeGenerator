import { constants } from 'node:fs';
import { open, type FileHandle } from 'node:fs/promises';
import { config } from '../config/app-config';

export async function openThumbnail(id: string) {
  const dirs: FileHandle[] = [];
  try {
    let dir = await open(config.dataDir, constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW);
    dirs.push(dir);
    for (const part of ['jobs', id, 'work', 'images']) {
      dir = await open(`/proc/self/fd/${dir.fd}/${part}`, constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW);
      dirs.push(dir);
    }
    const file = await open(`/proc/self/fd/${dir.fd}/scene-001.png`, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
    try {
      const info = await file.stat();
      if (!info.isFile() || info.size <= 0) throw new Error('invalid thumbnail');
      return { file, size: info.size };
    } catch (error) { await file.close(); throw error; }
  } finally { await Promise.all(dirs.map((dir) => dir.close())); }
}
