import re

with open('src/components/Admin/DiscountManagement.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    (
        'className="w-full border rounded px-3 py-2"',
        'className="w-full border-2 border-gray-400 rounded px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"'
    ),
    (
        'className="w-full border rounded px-3 py-2 bg-white"',
        'className="w-full border-2 border-gray-400 rounded px-3 py-2 bg-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"'
    ),
    (
        'className="w-full border rounded px-3 py-2 mb-2 text-sm focus:ring-1 focus:ring-blue-500 focus:outline-none"',
        'className="w-full border-2 border-gray-400 rounded px-3 py-2 mb-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"'
    ),
    (
        'className="border rounded p-3 max-h-48 overflow-y-auto space-y-2"',
        'className="border-2 border-gray-400 rounded p-3 max-h-48 overflow-y-auto space-y-2"'
    ),
    (
        'className="mt-2 w-full max-w-[200px] border rounded px-3 py-2"',
        'className="mt-2 w-full max-w-[200px] border-2 border-gray-400 rounded px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"'
    ),
    (
        'className="mt-2 w-full border rounded px-3 py-2"',
        'className="mt-2 w-full border-2 border-gray-400 rounded px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"'
    ),
    (
        'className="text-gray-700 bg-gray-50 p-4 border rounded"',
        'className="text-gray-700 bg-gray-50 p-4 border-2 border-gray-400 rounded"'
    ),
    (
        'className="border border-gray-100 rounded bg-gray-50 p-2 h-48 overflow-y-auto space-y-1"',
        'className="border-2 border-gray-400 rounded bg-gray-50 p-2 h-48 overflow-y-auto space-y-1"'
    ),
    (
        'className="mt-3 bg-white p-3 border rounded shadow-sm"',
        'className="mt-3 bg-white p-3 border-2 border-gray-400 rounded shadow-sm"'
    )
]

for old_str, new_str in replacements:
    content = content.replace(old_str, new_str)

# Double check standard border replacement for any leftover
# content = re.sub(r'className="([^"]*)border rounded([^"]*)"', r'className="\1border-2 border-gray-400 rounded focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500\2"', content)

with open('src/components/Admin/DiscountManagement.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

