import re

files_to_patch = [
    "frontend/src/app/brands/page.tsx",
    "frontend/src/app/categories/page.tsx",
    "frontend/src/app/customer/page.tsx",
    "frontend/src/app/wholesaler/page.tsx",
]

for fp in files_to_patch:
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace the extractJson definition
    old_extract = r"const extractJson = async \(res: Response \| null\) =>\s*res\?\.ok \? res\.json\(\)\.catch\(\(\) => null\) : null;"
    new_extract = """const extractJson = async (res: Response | null, critical: boolean = false) => {
    if (!res || !res.ok) {
      if (critical) throw new Error(API failed with status );
      return null;
    }
    return res.json().catch((e) => {
      if (critical) throw e;
      return null;
    });
  };"""
    content = re.sub(old_extract, new_extract, content, flags=re.MULTILINE)

    # In customer and wholesaler pages, the extract logic is slightly different:
    old_extract2 = r"const extract = async \(res: any\) => \{\s*if \(\!res \|\| \!res\.ok\) \{\s*return null;\s*\}\s*return res\.json\(\)\.catch\(\(\) => null\);\s*\};"
    new_extract2 = """const extract = async (res: any, critical: boolean = false) => {
    if (!res || !res.ok) {
      if (critical) throw new Error(API failed with status );
      return null;
    }
    return res.json().catch((e) => {
      if (critical) throw e;
      return null;
    });
  };"""
    content = re.sub(old_extract2, new_extract2, content, flags=re.MULTILINE)

    # 2. Update extractJson / extract calls for critical data
    if "brands/page.tsx" in fp:
        content = content.replace("extractJson(brandsRes)", "extractJson(brandsRes, true)")
        content = content.replace(
            ".catch(() => null)", ".catch((e) => { throw e; })", 2
        )  # First two fetches are critical (brands, categories)

    elif "categories/page.tsx" in fp:
        content = content.replace("extractJson(categoryRes)", "extractJson(categoryRes, true)")
        content = content.replace(
            ".catch(() => null)", ".catch((e) => { throw e; })", 2
        )  # First two fetches (categories, tags)

    elif "customer/page.tsx" in fp or "wholesaler/page.tsx" in fp:
        content = content.replace("extract(productsRes)", "extract(productsRes, true)")
        content = content.replace("extract(categoriesRes)", "extract(categoriesRes, true)")
        content = content.replace("extract(brandsRes)", "extract(brandsRes, true)")

        # Replace the first 3 .catch(() => null) with throw e
        parts = content.split(".catch(() => null)")
        if len(parts) > 3:
            content = (
                ".catch((e) => { throw e; })".join(parts[:4])
                + ".catch(() => null)"
                + ".catch(() => null)".join(parts[4:])
            )

    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched " + fp)
