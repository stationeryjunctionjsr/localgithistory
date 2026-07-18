const fs = require('fs');
const glob = require('glob');
const files = glob.sync('c:/Ecommerce app/frontend/src/app/admin/**/*.tsx');
let hasSelfClosing = false;
let fixedCount = 0;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let newContent = content;

  // Broad replacement for any tag that wraps text and ends with self-closing <InfoButton
  const broadRegex =
    /<(span|label|div|th|td|h[126])[^>]*inline-flex items-baseline[^>]*>([\s\S]*?)<InfoButton info=\{([^}]+)\} \/>\s*\)\}\s*<\/\1>/g;

  if (content.match(broadRegex)) {
    newContent = newContent.replace(broadRegex, (full, tag, innerAndCond, infoVal) => {
      // Find where '{user?.role' starts in innerAndCond
      const condIndex = innerAndCond.lastIndexOf('{user?.role');
      if (condIndex !== -1) {
        const textPart = innerAndCond.substring(0, condIndex).trim();
        const condPart = innerAndCond.substring(condIndex);

        // Extract the condition before infoVal
        const objCondMatch = condPart.match(/&& ([^\s&]+) && \(/);
        if (objCondMatch) {
          const cond1 = objCondMatch[1];
          // Get the opening tag
          const openTag = full.substring(0, full.indexOf('>') + 1);
          return `${openTag}\n  <InfoButton info={user?.role === 'super_admin' && ${cond1} ? ${infoVal} : undefined}>\n    ${textPart}\n  </InfoButton>\n</${tag}>`;
        }
      }
      return full; // fallback
    });
  }

  if (newContent !== content) {
    fs.writeFileSync(file, newContent, 'utf8');
    fixedCount++;
    console.log('Fixed file:', file);
  }
}
console.log('Fixed', fixedCount, 'files with broadly matched nodes.');
