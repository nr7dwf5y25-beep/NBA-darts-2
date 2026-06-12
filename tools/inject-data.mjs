// Embeds data/hoopdarts.sql into index.html (between the __HOOPDARTS_SQL__
// markers) so the single-file game ships with its database. Run from the
// repository root after any edit to the .sql file:
//
//   node tools/inject-data.mjs
//
import { readFileSync, writeFileSync } from 'node:fs';

const sql = readFileSync('data/hoopdarts.sql', 'utf8');
if (sql.includes('</script')) {
  throw new Error('SQL must not contain "</script" — it would terminate the embed tag');
}

const html = readFileSync('index.html', 'utf8');
const START = '<!-- __HOOPDARTS_SQL_START__ -->';
const END = '<!-- __HOOPDARTS_SQL_END__ -->';
const s = html.indexOf(START);
const e = html.indexOf(END);
if (s < 0 || e < 0 || e < s) throw new Error('SQL embed markers not found in index.html');

const block =
  START +
  '\n  <script id="hoopdarts-sql" type="text/x-sql">\n' +
  sql +
  '\n  </script>\n  ';
writeFileSync('index.html', html.slice(0, s) + block + html.slice(e));
console.log(`Embedded ${sql.length} bytes of SQL into index.html`);
