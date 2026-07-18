const fs = require('fs');
const glob = require('glob');

const files = glob.sync('c:/Ecommerce app/frontend/src/app/admin/**/*.tsx');
let spanMatches = 0;
let labelMatches = 0;
let hMatches = 0;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');

  // Span matches (e.g., table headers)
  const spanRegex =
    /<span className="inline-flex items-baseline gap-1">\s*([^<]+?)\s*\{user\?\.role === 'super_admin' && ([^\s&]+) && \(\s*<InfoButton info=\{([^}]+)\} \/>\s*\)\}\s*<\/span>/g;

  if (content.match(spanRegex)) {
    spanMatches += content.match(spanRegex).length;
    content = content.replace(spanRegex, (full, text, cond1, infoVal) => {
      text = text.trim();
      return `<InfoButton info={user?.role === 'super_admin' && ${cond1} ? ${infoVal} : undefined}>\n  ${text}\n</InfoButton>`;
    });
  }

  // Label matches (e.g., forms)
  const labelRegex =
    /<label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">\s*([^<]+?)\s*\{user\?\.role === 'super_admin' && ([^\s&]+) && \(\s*<InfoButton info=\{([^}]+)\} \/>\s*\)\}\s*<\/label>/g;

  if (content.match(labelRegex)) {
    labelMatches += content.match(labelRegex).length;
    content = content.replace(labelRegex, (full, text, cond1, infoVal) => {
      text = text.trim();
      return `<label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">\n  <InfoButton info={user?.role === 'super_admin' && ${cond1} ? ${infoVal} : undefined}>\n    ${text}\n  </InfoButton>\n</label>`;
    });
  }

  // Header matches (h1, h2)
  const hRegex =
    /<(h[12]) className="([^"]*inline-flex items-baseline[^"]*)">\s*([^<]+?)\s*\{user\?\.role === 'super_admin' && ([^\s&]+) && \(\s*<InfoButton info=\{([^}]+)\} \/>\s*\)\}\s*<\/\1>/g;

  if (content.match(hRegex)) {
    hMatches += content.match(hRegex).length;
    content = content.replace(hRegex, (full, tag, cls, text, cond1, infoVal) => {
      text = text.trim();
      return `<${tag} className="${cls}">\n  <InfoButton info={user?.role === 'super_admin' && ${cond1} ? ${infoVal} : undefined}>\n    ${text}\n  </InfoButton>\n</${tag}>`;
    });
  }

  fs.writeFileSync(file, content, 'utf8');
}

console.log({ spanMatches, labelMatches, hMatches });
