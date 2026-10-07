/** Documentation is maintained as source files, not regenerated from a fictional case. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','portfolio-projects/02-bpmn-1c-requirements');
for (const file of ['README.md','06-specification/technical-specification.md','03-bpmn/to-be.drawio']) await fs.access(path.join(root,file));
console.log('Existing author-provided requirements and diagrams are preserved.');
