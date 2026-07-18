import re
import os

with open('src/components/Admin/DiscountManagement.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add fields to Discount interface
content = re.sub(
    r'applicableItemType\?: \'units\' \| \'cases\'\n\}',
    r'''applicableItemType?: 'units' | 'cases'
  buyXGetYCustomerGetsQuantity?: number | null
  buyXGetYCustomerGetsAppliesToType?: string
  buyXGetYCustomerGetsAppliesToValueIds?: string[]
  buyXGetYCustomerGetsDiscountType?: string
  buyXGetYCustomerGetsDiscountValue?: number | null
}''',
    content
)

# 2. Add fields to formData
content = re.sub(
    r'    applicableItemType: \'units\' as \'units\' \| \'cases\',\n    isActive: true',
    r'''    applicableItemType: 'units' as 'units' | 'cases',
    isActive: true,
    buyXGetYCustomerGetsQuantity: '' as string,
    buyXGetYCustomerGetsAppliesToType: 'all' as string,
    buyXGetYCustomerGetsAppliesToValueIds: [] as string[],
    buyXGetYCustomerGetsDiscountType: 'percentage' as string,
    buyXGetYCustomerGetsDiscountValue: '' as string''',
    content
)

# 3. Add handleGets fields, and renderAppliesToSelector helper
helper_str = r'''
  const handleGetsAppliesToTypeChange = (value: string) => {
    setFormData({ ...formData, buyXGetYCustomerGetsAppliesToType: value, buyXGetYCustomerGetsAppliesToValueIds: [] })
  }

  const toggleGetsAppliesToValue = (idOrName: string) => {
    const current = formData.buyXGetYCustomerGetsAppliesToValueIds || []
    const next = current.includes(idOrName) ? current.filter(x => x !== idOrName) : [...current, idOrName]
    setFormData({ ...formData, buyXGetYCustomerGetsAppliesToValueIds: next })
  }

  const renderAppliesToSelector = (
    appliesToType: string,
    appliesToValueIds: string[],
    onTypeChange: (value: string) => void,
    onValueToggle: (id: string) => void,
    labelTitle: string = 'Applies to'
  ) => {
    return (
      <div className="pt-2">
        <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
          {labelTitle}
        </label>
        <select value={appliesToType} onChange={e => onTypeChange(e.target.value)} className="w-full border rounded px-3 py-2">
          {APPLIES_TO_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {appliesToType !== 'all' && (
          <div className="mt-3">
            <label className="block text-sm font-medium mb-1">Select {appliesToType === 'categories' ? 'categories' : appliesToType === 'subCategories' ? 'sub-categories' : appliesToType === 'brands' ? 'brands' : 'collections'} *</label>
            <div className="border rounded p-3 max-h-48 overflow-y-auto space-y-2">
              {appliesToType === 'categories' && categories.map(c => (
                <label key={c._id} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={appliesToValueIds?.includes(c._id)} onChange={() => onValueToggle(c._id)} className="rounded" />
                  <span>{c.name}</span>
                </label>
              ))}
              {appliesToType === 'subCategories' && subCategoryOptions.map(s => (
                <label key={s} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={appliesToValueIds?.includes(s)} onChange={() => onValueToggle(s)} className="rounded" />
                  <span>{s}</span>
                </label>
              ))}
              {appliesToType === 'brands' && brands.map(b => (
                <label key={b._id} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={appliesToValueIds?.includes(b._id)} onChange={() => onValueToggle(b._id)} className="rounded" />
                  <span>{b.name}</span>
                </label>
              ))}
              {appliesToType === 'collections' && collections.map(c => (
                <label key={c._id} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={appliesToValueIds?.includes(c._id)} onChange={() => onValueToggle(c._id)} className="rounded" />
                  <span>{c.name}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const showUserBehaviour = true'''

content = content.replace('  const showUserBehaviour = true', helper_str)

# 4. Add to submitData
submit_data_replace = r'''        applicableItemType: discountCategory === 'business' ? formData.applicableItemType : undefined,
        isActive: formData.isActive,
        buyXGetYCustomerGetsQuantity: formData.buyXGetYCustomerGetsQuantity ? parseInt(formData.buyXGetYCustomerGetsQuantity, 10) : null,
        buyXGetYCustomerGetsAppliesToType: formData.buyXGetYCustomerGetsAppliesToType,
        buyXGetYCustomerGetsAppliesToValueIds: formData.buyXGetYCustomerGetsAppliesToValueIds,
        buyXGetYCustomerGetsDiscountType: formData.buyXGetYCustomerGetsDiscountType,
        buyXGetYCustomerGetsDiscountValue: formData.buyXGetYCustomerGetsDiscountValue ? parseFloat(formData.buyXGetYCustomerGetsDiscountValue) : null
      }'''
content = re.sub(r'        applicableItemType: discountCategory === \'business\' \? formData\.applicableItemType : undefined,\n        isActive: formData\.isActive\n      \}', submit_data_replace, content)

# 5. Add to resetForm
reset_form_replace = r'''      userBehavior: 'none',
      applicableItemType: 'units',
      isActive: true,
      buyXGetYCustomerGetsQuantity: '',
      buyXGetYCustomerGetsAppliesToType: 'all',
      buyXGetYCustomerGetsAppliesToValueIds: [],
      buyXGetYCustomerGetsDiscountType: 'percentage',
      buyXGetYCustomerGetsDiscountValue: ''
    })'''
content = re.sub(r'      userBehavior: \'none\',\n      applicableItemType: \'units\',\n      isActive: true\n    \}\)', reset_form_replace, content)

# 6. Add to handleEdit
edit_form_replace = r'''      userBehavior: behavior,
      applicableItemType: d.applicableItemType || 'units',
      isActive: d.isActive !== false,
      buyXGetYCustomerGetsQuantity: d.buyXGetYCustomerGetsQuantity?.toString() || '',
      buyXGetYCustomerGetsAppliesToType: d.buyXGetYCustomerGetsAppliesToType || 'all',
      buyXGetYCustomerGetsAppliesToValueIds: d.buyXGetYCustomerGetsAppliesToValueIds || [],
      buyXGetYCustomerGetsDiscountType: d.buyXGetYCustomerGetsDiscountType || 'percentage',
      buyXGetYCustomerGetsDiscountValue: d.buyXGetYCustomerGetsDiscountValue?.toString() || ''
    })'''
content = re.sub(r'      userBehavior: behavior,\n      applicableItemType: d\.applicableItemType \|\| \'units\',\n      isActive: d\.isActive !== false\n    \}\)', edit_form_replace, content)

# 7. Form UI adjustments
# Move generic "applicableItemType" right below "typeOfDiscount" for business
# Remove "No requirement" if buy_x_get_y
# Show Applies To in Customer Buys if buy_x_get_y
# Show Customer Gets if buy_x_get_y

def replace_form(s):
    form_start = s.find('{/* Type of discount - first field */}')
    form_end = s.find('{/* Maximum discount uses */}')
    
    new_form_content = '''{/* Type of discount - first field */}
              <div>
                <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
                  Type of discount *
                </label>
                <select name="typeOfDiscount" value={formData.typeOfDiscount} onChange={handleChange} className="w-full border rounded px-3 py-2">
                  {TYPE_OF_DISCOUNT_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              {discountCategory === 'business' && (
                <div>
                  <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
                    Apply discount to
                  </label>
                  <select name="applicableItemType" value={formData.applicableItemType} onChange={handleChange} className="w-full border rounded px-3 py-2">
                    <option value="units">Units</option>
                    <option value="cases">Cases</option>
                  </select>
                </div>
              )}
              {/* Method */}
              <div>
                <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
                  Method *
                </label>
                <select name="method" value={formData.method} onChange={handleChange} className="w-full border rounded px-3 py-2">
                  <option value="discount_code">Discount code</option>
                  <option value="automatic">Automatic discount</option>
                </select>
                <small className="text-gray-500 text-xs block">Automatic discount is applied for the selected segment, behaviour and products.</small>
              </div>
              {formData.method === 'discount_code' && (
                <div>
                  <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
                    Discount Code *
                  </label>
                  <input type="text" name="code" value={formData.code} onChange={handleChange} required={formData.method === 'discount_code'} style={{ textTransform: 'uppercase' }} className="w-full border rounded px-3 py-2" />
                </div>
              )}

              {/* Eligibility */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Eligibility</h4>
                <div className="space-y-3">
                  {showUserBehaviour && (
                    <div>
                      <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
                        User behaviour
                      </label>
                      <select name="userBehavior" value={formData.userBehavior} onChange={handleChange} className="w-full border rounded px-3 py-2">
                        {USER_BEHAVIOUR_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                        {discountCategory === 'retail' ? (
                          <option value="selective_retail">Selective Retail Customers</option>
                        ) : (
                          <option value="selective_business">Selective Business Customers</option>
                        )}
                      </select>
                    </div>
                  )}
                  {showSelectiveUsers && (
                    <div>
                      <label className="block text-sm font-medium mb-1">Select {discountCategory === 'retail' ? 'retail' : 'business'} customers *</label>
                      <div className="border rounded p-3 max-h-48 overflow-y-auto space-y-2">
                        {selectiveUserList.map(u => (
                          <label key={u._id} className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={formData.applicableUserIds?.includes(u._id)} onChange={() => toggleApplicableUser(u._id)} className="rounded" />
                            <span>{u.name || u.phone || u.email || u._id}</span>
                          </label>
                        ))}
                        {selectiveUserList.length === 0 && <p className="text-gray-500 text-sm">No users found.</p>}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Minimum purchase requirements */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">
                  {formData.typeOfDiscount === 'buy_x_get_y' ? 'Customer buys (Minimum purchase requirements)' : 'Minimum purchase requirements'}
                </h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
                      Requirement type
                    </label>
                    <select name="minRequirementType" value={formData.minRequirementType} onChange={handleChange} className="w-full border rounded px-3 py-2">
                      {(formData.typeOfDiscount === 'buy_x_get_y' ? MIN_REQUIREMENT_OPTIONS.filter(o => o.value !== 'none') : MIN_REQUIREMENT_OPTIONS).map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  {formData.minRequirementType === 'min_amount' && (
                    <div>
                      <label className="block text-sm font-medium mb-1">Minimum purchase amount (₹) — on eligible items</label>
                      <input type="number" name="minPurchaseAmount" value={formData.minPurchaseAmount} onChange={handleChange} step="0.01" min="0" placeholder="0" className="w-full border rounded px-3 py-2" />
                    </div>
                  )}
                  {formData.minRequirementType === 'min_quantity' && (
                    <div>
                      <label className="block text-sm font-medium mb-1">Minimum quantity of eligible items</label>
                      <input type="number" name="minQuantityOfEligibleItems" value={formData.minQuantityOfEligibleItems} onChange={handleChange} min="1" placeholder="e.g. 2" className="w-full border rounded px-3 py-2" />
                      <small className="text-gray-500 text-xs block">User must have this many quantity of products eligible for the discount in cart.</small>
                    </div>
                  )}
                  {formData.typeOfDiscount === 'buy_x_get_y' && formData.minRequirementType !== 'none' && (
                    <div className="mt-2 text-gray-700 bg-gray-50 p-4 border rounded">
                      {renderAppliesToSelector(formData.appliesToType, formData.appliesToValueIds, handleAppliesToTypeChange, toggleAppliesToValue, 'Any items from')}
                    </div>
                  )}
                </div>
              </div>

              {/* Discount value / Customer gets */}
              {formData.typeOfDiscount === 'buy_x_get_y' ? (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Customer gets</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Quantity</label>
                      <input type="number" name="buyXGetYCustomerGetsQuantity" value={formData.buyXGetYCustomerGetsQuantity} onChange={handleChange} min="1" required className="w-full border rounded px-3 py-2" />
                      <small className="text-gray-500 text-xs block">Customers must add the quantity of items specified above to their cart.</small>
                    </div>
                    
                    <div className="text-gray-700 bg-gray-50 p-4 border rounded">
                      {renderAppliesToSelector(formData.buyXGetYCustomerGetsAppliesToType, formData.buyXGetYCustomerGetsAppliesToValueIds, handleGetsAppliesToTypeChange, toggleGetsAppliesToValue, 'Any items from')}
                    </div>
                    
                    <div className="pt-3">
                      <label className="block text-sm font-medium mb-3 font-semibold text-gray-700">At a discounted value</label>
                      <div className="space-y-4">
                        <label className="flex items-start gap-2 cursor-pointer">
                          <input type="radio" name="buyXGetYCustomerGetsDiscountType" value="percentage" checked={formData.buyXGetYCustomerGetsDiscountType === 'percentage'} onChange={handleChange} className="mt-1" />
                          <div className="flex-1">
                            <span className="block text-sm font-medium">Percentage</span>
                            {formData.buyXGetYCustomerGetsDiscountType === 'percentage' && (
                              <input type="number" name="buyXGetYCustomerGetsDiscountValue" value={formData.buyXGetYCustomerGetsDiscountValue} onChange={handleChange} placeholder="%" step="0.01" min="0" required className="mt-2 w-full border rounded px-3 py-2" />
                            )}
                          </div>
                        </label>
                        <label className="flex items-start gap-2 cursor-pointer">
                          <input type="radio" name="buyXGetYCustomerGetsDiscountType" value="amount_off" checked={formData.buyXGetYCustomerGetsDiscountType === 'amount_off'} onChange={handleChange} className="mt-1" />
                          <div className="flex-1">
                            <span className="block text-sm font-medium">Amount off each</span>
                            {formData.buyXGetYCustomerGetsDiscountType === 'amount_off' && (
                              <input type="number" name="buyXGetYCustomerGetsDiscountValue" value={formData.buyXGetYCustomerGetsDiscountValue} onChange={handleChange} placeholder="₹" step="0.01" min="0" required className="mt-2 w-full border rounded px-3 py-2" />
                            )}
                          </div>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input type="radio" name="buyXGetYCustomerGetsDiscountType" value="free" checked={formData.buyXGetYCustomerGetsDiscountType === 'free'} onChange={handleChange} />
                          <span className="text-sm font-medium">Free</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Discount value</h4>
                  <div className="space-y-3">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-1 inline-flex items-baseline gap-1">
                          Discount type *
                        </label>
                        <select name="discountType" value={formData.discountType} onChange={handleChange} required className="w-full border rounded px-3 py-2">
                          <option value="percentage">Percentage (%)</option>
                          <option value="fixed">Fixed amount (₹)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Discount value *</label>
                        <input type="number" name="discountValue" value={formData.discountValue} onChange={handleChange} step="0.01" min="0" required className="w-full border rounded px-3 py-2" />
                      </div>
                    </div>
                    <div className="text-gray-700 bg-gray-50 p-4 border rounded">
                      {renderAppliesToSelector(formData.appliesToType, formData.appliesToValueIds, handleAppliesToTypeChange, toggleAppliesToValue, 'Applies to')}
                    </div>
                  </div>
                </div>
              )}

              '''
    
    return s[:form_start] + new_form_content + s[form_end:]

content = replace_form(content)

with open('src/components/Admin/DiscountManagement.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

