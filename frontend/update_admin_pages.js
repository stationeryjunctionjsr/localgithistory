const fs = require('fs');
const path = require('path');

const adminPages = [
  'admin/analytics/page.tsx',
  'admin/banners/page.tsx',
  'admin/brands/page.tsx',
  'admin/categories/page.tsx',
  'admin/contacts/page.tsx',
  'admin/coupons/page.tsx',
  'admin/delivery-charges/page.tsx',
  'admin/feature-flags/page.tsx',
  'admin/payments/page.tsx',
  'admin/profile/page.tsx',
  'admin/push-notifications/page.tsx',
  'admin/reports/page.tsx',
];

const srcDir = path.join(__dirname, 'src');

adminPages.forEach((pagePath) => {
  const fullPath = path.join(srcDir, pagePath);

  if (fs.existsSync(fullPath)) {
    let content = fs.readFileSync(fullPath, 'utf8');

    // Add AdminLayout import if not present
    if (!content.includes('import AdminLayout')) {
      // Find the last import statement and add AdminLayout import after it
      const importRegex = /import[^;]+;/g;
      const imports = content.match(importRegex);
      if (imports && imports.length > 0) {
        const lastImport = imports[imports.length - 1];
        const lastImportIndex = content.lastIndexOf(lastImport);
        const importEndIndex = lastImportIndex + lastImport.length;

        content =
          content.slice(0, importEndIndex) +
          "\nimport AdminLayout from '@/components/Admin/AdminLayout'" +
          content.slice(importEndIndex);
      }
    }

    // Wrap return statement with AdminLayout if not already wrapped
    if (content.includes('return (') && !content.includes('<AdminLayout>')) {
      // Find the main return statement
      const returnMatch = content.match(/\s*return\s*\(\s*\n\s*<div[^>]*>/);
      if (returnMatch) {
        const returnIndex = content.indexOf(returnMatch[0]);
        const divStart = returnIndex + returnMatch[0].indexOf('<div');

        // Replace the opening div with AdminLayout wrapper
        content =
          content.slice(0, returnIndex) +
          content.slice(returnIndex).replace(/<div[^>]*>/, '<AdminLayout>\n      <div');

        // Find the closing div and add AdminLayout closing tag
        const lastDivIndex = content.lastIndexOf('</div>');
        if (lastDivIndex !== -1) {
          content =
            content.slice(0, lastDivIndex + 6) +
            '\n    </AdminLayout>' +
            content.slice(lastDivIndex + 6);
        }
      }
    }

    fs.writeFileSync(fullPath, content);
    console.log(`Updated ${pagePath}`);
  } else {
    console.log(`File not found: ${pagePath}`);
  }
});

console.log('Admin pages update complete!');
