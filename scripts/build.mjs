import { cp, mkdir, rm, readdir, copyFile } from 'node:fs/promises';
import { join } from 'node:path';

const output = 'dist';
const staticFiles = ['index.html', 'preview.html', '404.html', 'robots.txt', 'sitemap.xml'];

await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });

for (const file of staticFiles) {
  await copyFile(file, join(output, file));
}

for (const directory of ['public', 'src', 'pages-assets', 'pages']) {
  await cp(directory, join(output, directory), { recursive: true });
}

// Keep migrated Jekyll permalink URLs available from the site root.
for (const file of await readdir('pages')) {
  if (!file.endsWith('.html')) continue;
  await copyFile(join('pages', file), join(output, file));
}

console.log('KirinDL Web site built in dist/');
