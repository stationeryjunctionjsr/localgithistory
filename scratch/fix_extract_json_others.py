import re
import glob

files = glob.glob('frontend/src/app/*/*page.tsx', recursive=True) + glob.glob('frontend/src/app/*/*/*page.tsx', recursive=True)
for path in files:
    if 'customer' in path or 'wholesaler' in path or 'page.tsx' not in path:
        continue
    with open(path, 'r', encoding='utf-8') as f: content = f.read()
    
    old_extract = r"const extractJson = async \(res: Response \| null\) =>\s*res\?\.ok \? res\.json\(\)\.catch\(\(\) => null\) : null;"
    if re.search(old_extract, content):
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
        content = content.replace('extractJson(brandsRes)', 'extractJson(brandsRes, true)')
        content = content.replace('extractJson(categoriesRes)', 'extractJson(categoriesRes, true)')
        content = content.replace('extractJson(categoryRes)', 'extractJson(categoryRes, true)')
        content = content.replace('extractJson(colsRes)', 'extractJson(colsRes, true)')
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        print(f"Fixed {path}")
