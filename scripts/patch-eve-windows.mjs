import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

if (process.platform === 'win32') {
  const target = path.resolve('node_modules/eve/dist/src/internal/application/output-publication-artifacts.js');
  const source = await readFile(target, 'utf8');
  const importNeedle = 'import{mkdir,rename,rm,stat}from"node:fs/promises";';
  const patchedImport = 'import{mkdir,rm,stat}from"node:fs/promises";import{renameWithTransientBusyRetry}from"#shared/rename-with-retry.js";';

  if (source.includes(patchedImport)) {
    process.stdout.write('Eve Windows publication retry patch already applied.\n');
  } else {
    if (!source.includes(importNeedle)) {
      throw new Error('Unsupported Eve output publication implementation; review the Windows retry patch before upgrading Eve.');
    }
    const patched = source
      .replace(importNeedle, patchedImport)
      .replaceAll('await rename(', 'await renameWithTransientBusyRetry(');
    await writeFile(target, patched, 'utf8');
    process.stdout.write('Applied Eve Windows publication retry patch.\n');
  }
}
