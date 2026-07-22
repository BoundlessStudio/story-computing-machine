import { readFile, readdir } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { dirname, isAbsolute, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEnvFile } from 'node:process';
import { DatabaseSync } from 'node:sqlite';

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const migrationsDirectory = resolve(projectRoot, 'sql');

try {
  loadEnvFile(resolve(projectRoot, '.env'));
} catch (error) {
  if (!(error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT')) throw error;
}

export function resolveSqlitePath(value = process.env.SQLITE_PATH ?? 'data/story-room.sqlite'): string {
  if (value === ':memory:') return value;
  return isAbsolute(value) ? value : resolve(projectRoot, value);
}

function openDatabase(databasePath: string): DatabaseSync {
  if (databasePath !== ':memory:') mkdirSync(dirname(databasePath), { recursive: true });
  const database = new DatabaseSync(databasePath);
  database.exec('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA busy_timeout = 5000;');
  return database;
}

export async function migrateDatabase(databasePath = resolveSqlitePath()): Promise<string[]> {
  const database = openDatabase(databasePath);
  try {
    database.exec(`
      CREATE TABLE IF NOT EXISTS schema_migrations (
        migration_name TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL
      )
    `);

    const files = (await readdir(migrationsDirectory))
      .filter((file) => /^\d+_.+\.sql$/u.test(file))
      .sort();
    const applied: string[] = [];

    for (const file of files) {
      const existing = database.prepare('SELECT 1 FROM schema_migrations WHERE migration_name = ?').get(file);
      if (existing) continue;
      const source = await readFile(resolve(migrationsDirectory, file), 'utf8');
      database.exec('BEGIN IMMEDIATE');
      try {
        database.exec('PRAGMA defer_foreign_keys = ON');
        database.exec(source);
        database.prepare('INSERT INTO schema_migrations (migration_name, applied_at) VALUES (?, ?)')
          .run(file, new Date().toISOString());
        database.exec('COMMIT');
        applied.push(file);
      } catch (error) {
        database.exec('ROLLBACK');
        throw error;
      }
    }
    return applied;
  } finally {
    database.close();
  }
}

const invokedDirectly = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  const databasePath = resolveSqlitePath();
  const applied = await migrateDatabase(databasePath);
  console.log(applied.length ? `Applied migrations: ${applied.join(', ')}` : 'Database is up to date.');
  console.log(`SQLite database: ${databasePath}`);
}
