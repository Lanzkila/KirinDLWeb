import { cp, mkdir, rm, readdir, copyFile } from 'node:fs/promises';
import { join } from 'node:path';

const output = 'dist';
const staticFiles = [
  'index.html',
  '404.html',
  'robots.txt',
  'sitemap.xml'
];

await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });

for (const file of staticFiles) {
  await copyFile(file, join(output, file));
}

for (const directory of ['public', 'src', 'pages-assets', 'pages']) {
  await cp(directory, join(output, directory), { recursive: true });
}

// The original Jekyll site exposed these pages at the site root through
// front-matter permalinks. Keep those public URLs without requiring Jekyll.
for (const file of await readdir('pages')) {
  if (!file.endsWith('.html')) continue;
  await copyFile(join('pages', file), join(output, file));
}

console.log('KirinDL Web site built in dist/');
