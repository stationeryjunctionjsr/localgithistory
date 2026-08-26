import re

for fp in ['frontend/src/app/brands/page.tsx', 'frontend/src/app/categories/page.tsx']:
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    old_extract = r'const extractJson = async \(res: Response \| null\) =>\s*res\?\.ok \? res\.json\(\)\.catch\(\(\) => null\) : null;'
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
    content = re.sub(old_extract, new_extract, content, flags=re.MULTILINE)

    if 'brands/page.tsx' in fp:
        content = content.replace('extractJson(brandsRes)', 'extractJson(brandsRes, true)')
        content = content.replace('.catch(() => null)', '.catch((e) => { throw e; })', 2)
    elif 'categories/page.tsx' in fp:
        content = content.replace('extractJson(categoryRes)', 'extractJson(categoryRes, true)')
        content = content.replace('.catch(() => null)', '.catch((e) => { throw e; })', 2)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
