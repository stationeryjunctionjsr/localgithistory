import re
import glob

# 1. Fix page.tsx
page_tsx = 'frontend/src/app/page.tsx'
with open(page_tsx, 'r', encoding='utf-8') as f: content = f.read()
old_extract = r"const extractJson = async \(res: Response \| null\) =>\s*res\?\.ok \? res\.json\(\)\.catch\(\(\) => null\) : null;"
new_extract = '''const extractJson = async (res: Response | null, critical: boolean = false) => {
    if (!res || !res.ok) {
      if (critical) throw new Error(`API failed with status ${res?.status}`);
      return null;
    }
    return res.json().catch((e) => {
      if (critical) throw e;
      return null;
    });
  };'''
content = re.sub(old_extract, new_extract, content)
content = content.replace('extractJson(productsRes),', 'extractJson(productsRes, true),')
content = content.replace('extractJson(categoriesRes),', 'extractJson(categoriesRes, true),')
content = content.replace('extractJson(categoryTagsRes),', 'extractJson(categoryTagsRes, true),')
content = content.replace('extractJson(brandsRes),', 'extractJson(brandsRes, true),')
with open(page_tsx, 'w', encoding='utf-8') as f: f.write(content)

# 2. Fix customer & wholesaler
for path in ['frontend/src/app/customer/page.tsx', 'frontend/src/app/wholesaler/page.tsx']:
    with open(path, 'r', encoding='utf-8') as f: content = f.read()
    old_func = r"const extractJson = async \(res: Response \| null, label: string\) => \{[\s\S]*?return res\.json\(\)\.catch\(\(\) => null\);\s*\};"
    new_func = '''const extractJson = async (res: Response | null, label: string, critical: boolean = false) => {
    if (res === null) {
      console.error(`[fetch] network error: ${label}`);
      if (critical) throw new Error(`Network error: ${label}`);
      return null;
    }
    if (!res.ok) {
      console.error(`[fetch] status ${res.status}: ${label}`);
      if (critical) throw new Error(`API failed with status ${res.status}: ${label}`);
      return null;
    }
    return res.json().catch((e) => {
      if (critical) throw e;
      return null;
    });
  };'''
    content = re.sub(old_func, new_func, content)
    content = content.replace("'products/public'),", "'products/public', true),")
    content = content.replace("'categories/public'),", "'categories/public', true),")
    content = content.replace("'category-tags/active'),", "'category-tags/active', true),")
    content = content.replace("'brands/public'),", "'brands/public', true),")
    with open(path, 'w', encoding='utf-8') as f: f.write(content)

print("Fixed extractJson")
