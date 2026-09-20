import re

with open(r'c:\Ecommerce app\frontend\src\utils\analytics.ts', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  return {
    os,
    browser,
    campaign,
    device: {
      type: isMobile ? 'mobile' : 'desktop',
      os: os,
      browser: browser
    },
    ...(utmSource && { source: utmSource }),
  };
};
'''

text = re.sub(r'  return \{\n    os,\n    browser,\n    campaign,\n    \.\.\.\(utmSource && \{ source: utmSource \}\),\n  \};\n\};\n', replacement, text)

with open(r'c:\Ecommerce app\frontend\src\utils\analytics.ts', 'w', encoding='utf-8') as f:
    f.write(text)
