/** Refresh the existing author-provided exports, without generation of source records. */
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
process.argv[2]=path.join(root,'portfolio-projects/01-data-quality-excel-reporting');
await import('../portfolio-projects/01-data-quality-excel-reporting/scripts/refresh_report.mjs');
