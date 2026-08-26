def fix_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

fix_file('frontend/src/components/MobileComponents/BottomNav.tsx', [
    ('catch (e) { logger.warn("Silent catch block:", e); // Silent fail }', 'catch (e) { logger.warn("Silent catch block:", e); /* Silent fail */ }')
])

fix_file('frontend/src/components/MobileComponents/MobileHeader.tsx', [
    ('catch (e) { logger.warn("Silent catch block:", e); // Silent fail }', 'catch (e) { logger.warn("Silent catch block:", e); /* Silent fail */ }')
])

fix_file('frontend/src/app/customer/cart/page.tsx', [
    ('catch (e) { logger.warn("Silent catch block:", e); // Analytics failure should never block checkout }', 'catch (e) { logger.warn("Silent catch block:", e); /* Analytics failure should never block checkout */ }'),
    ('catch (e) { logger.warn("Silent catch block:", e); // eslint-disable-next-line unused-imports/no-unused-vars }', 'catch (e) { logger.warn("Silent catch block:", e); /* eslint-disable-next-line unused-imports/no-unused-vars */ }')
])

fix_file('frontend/src/components/Header.tsx', [
    ('catch (e) { logger.warn("Silent catch block:", e); // Silent fail }', 'catch (e) { logger.warn("Silent catch block:", e); /* Silent fail */ }')
])

fix_file('frontend/src/components/Analytics/UserEngagementChart.tsx', [
    ('import {\nimport { logger } from \'@/utils/logger\';\n  BarChart', 'import {\n  BarChart'),
    ('import api from \'@/utils/api\';\nimport {', 'import api from \'@/utils/api\';\nimport { logger } from \'@/utils/logger\';\nimport {')
])
