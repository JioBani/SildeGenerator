import { constants } from 'node:fs';
import { open, type FileHandle } from 'node:fs/promises';
import { config } from '../config/app-config';
// Traverse with pinned directory descriptors; reject symlinks at every component.
// The worker shares /data, so a realpath-then-open check would have a race.
export async function openVideo(id: string) {
  const dirs: FileHandle[] = [];
  try {
    let dir = await open(config.dataDir, constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW);
    dirs.push(dir);
    for (const part of ['jobs', id, 'output']) {
      dir = await open(`/proc/self/fd/${dir.fd}/${part}`, constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW);
      dirs.push(dir);
    }
    const file = await open(`/proc/self/fd/${dir.fd}/video.mp4`, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
    try {
      const info = await file.stat();
      if (!info.isFile() || info.size > 32 * 1024 * 1024) throw new Error('invalid video');
      return { file, size: info.size };
    } catch (e) { await file.close(); throw e; }
  } finally { await Promise.all(dirs.map(dir => dir.close())); }
}
