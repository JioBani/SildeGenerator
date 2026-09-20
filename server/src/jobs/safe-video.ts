import { constants } from 'node:fs';
import { open, type FileHandle } from 'node:fs/promises';
import { config } from '../config/app-config';

export const isDownloadableVideo = (info: { isFile(): boolean; size: number }) => info.isFile() && info.size > 0;

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
      // Downloads are streamed from an artifact produced in the shared runner
      // volume, so file size does not increase API memory usage. A fixed size
      // ceiling incorrectly made longer, otherwise valid videos look expired.
      if (!isDownloadableVideo(info)) throw new Error('invalid video');
      return { file, size: info.size };
    } catch (e) { await file.close(); throw e; }
  } finally { await Promise.all(dirs.map(dir => dir.close())); }
}
