with open('frontend/src/app/valet/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

single_block = """                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            ?? Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}
"""
double_block = single_block + "\n" + single_block

while double_block in content:
    content = content.replace(double_block, single_block)

with open('frontend/src/app/valet/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
