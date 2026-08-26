import re
with open('frontend/src/app/valet/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"(?s)(\s*\{ret\.deliverySlot && \(\s*<div className=\"mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1\.5 rounded-lg border border-purple-200 font-medium inline-block\">\s*?? Scheduled Pickup Slot: \{ret\.deliverySlot\.startTime\} - \{ret\.deliverySlot\.endTime\} \(\{ret\.deliverySlot\.date\}\)\s*</div>\s*\)\}){2,}"

match = re.search(pattern, content)
if match:
    single_block = """
                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            ?? Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}"""
    content = re.sub(pattern, single_block, content)
    with open('frontend/src/app/valet/page.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced multiple blocks with one.")
else:
    print("Pattern not found!")
