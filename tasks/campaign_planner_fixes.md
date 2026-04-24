# Campaign Planner Fixes — April 24, 2026

## Issues Fixed

### 1. ✅ Weak Brand Enforcement

**Problem**: Campaign planner prompt didn't enforce brand constraints like content generation service does.

**Fix**: Added HARD RULES section to prompt with explicit brand constraints:
- Business name MUST appear in captions
- Tagline MUST be referenced where relevant  
- Tone MUST be strictly followed

**Files Modified**:
- `raamp-backend/application/services/campaign_planner_service.py` (_build_prompt method)

---

### 2. ✅ Showing Prompts Instead of Captions

**Problem**: Calendar showed `caption_prompt` (instructions) instead of actual usable captions.

**User Experience Issue**: Users saw "Write a caption about Valentine's Day promo" but no actual caption they could copy/use.

**Fix**: 
- Changed LLM output schema from `caption_prompt` → `caption` (actual usable text)
- Updated prompt with "CAPTION REQUIREMENTS" section specifying to generate ready-to-use captions
- Captions now include hashtags and are 2-4 lines, brand-aligned

**Files Modified**:
- `raamp-backend/application/services/campaign_planner_service.py` (prompt template)
- `raamp-backend/infrastructure/database/models/campaign_planned_post_model.py` (added caption field)
- `raamp-backend/presentation/schemas/campaign_planner_schemas.py` (PlannedPostItem schema)
- `raamp-frontend/src/services/campaignPlannerService.ts` (TypeScript interface)
- `raamp-frontend/src/components/campaign-planner/PlannedPostDrawer.tsx` (UI display)

---

### 3. ⚠️ Partial Fix: Content Generation After Calendar

**Problem**: After viewing calendar, users could only:
- Convert to Draft (creates empty draft)
- Request Approval (requires manual media)

No automated content generation from prompts.

**Current State**: 
- ✅ Actual captions are now generated and displayed
- ✅ Creative prompts stored for image generation
- ⚠️ Still need "Generate Image" button to call image_generation_service with creative_prompt

**Next Steps**:
1. Add "Generate Image" button in PlannedPostDrawer
2. Call `image_generation_service.generate_image_prompt()` with creative_prompt
3. Display generated image preview
4. Auto-populate media_url field for approval workflow

---

## Testing Recommendations

### Backend Tests
```python
# Test brand enforcement in prompts
def test_brand_constraints_in_prompt():
    service = CampaignPlannerService()
    brand = {
        "business_name": "Bella's Bistro",
        "tagline": "Fresh flavors daily",
        "tone_of_voice": "Warm and inviting"
    }
    brief = {
        "start_date": "2026-05-01",
        "end_date": "2026-05-31",
        "posting_frequency": "3_per_week"
    }
    
    prompt = service._build_prompt(brief=brief, brand=brand)
    
    assert 'Business name MUST appear in caption: "Bella\'s Bistro"' in prompt
    assert 'Tagline MUST be referenced where relevant: "Fresh flavors daily"' in prompt
    assert 'Tone MUST be strictly followed: "Warm and inviting"' in prompt
    assert "ACTUAL USABLE CAPTIONS" in prompt

# Test caption storage (not prompt)
async def test_planned_post_stores_caption():
    # Create test plan
    plan = await create_test_campaign_plan()
    
    # Fetch planned posts
    posts = await CampaignPlannedPostModel.find(
        CampaignPlannedPostModel.campaign_plan_id == str(plan.id)
    ).to_list()
    
    assert len(posts) > 0
    first_post = posts[0]
    
    # Verify caption field exists and is not a prompt
    assert first_post.caption is not None
    assert "Write a caption" not in first_post.caption  # Should not be a prompt
    assert len(first_post.caption) > 0
    
    # Verify creative_prompt is separate
    assert "creative_prompt" in first_post.prompts
```

### Frontend Tests
```typescript
// Test caption display
it("should display actual caption, not caption_prompt", () => {
  const mockItem: PlannedPostItem = {
    id: "123",
    title: "Valentine's Day Special",
    caption: "❤️ Love is in the air at Bella's Bistro! #ValentinesDay #Romance",
    prompts: {
      creative_prompt: "Romantic restaurant table with roses and candles"
    }
  };
  
  render(<PlannedPostDrawer item={mockItem} />);
  
  // Should show actual caption
  expect(screen.getByText(/Love is in the air/)).toBeInTheDocument();
  
  // Should NOT show prompt instruction
  expect(screen.queryByText(/Write a caption/)).not.toBeInTheDocument();
});
```

---

## Migration Notes

**Database Migration**: The `caption` field is optional, so existing planned posts will continue to work. They'll just show "No caption generated" until regenerated with new prompt.

**Backward Compatibility**: 
- Old posts with `caption_prompt` in prompts dict will show as legacy data
- New posts store actual captions in dedicated field
- Frontend gracefully handles both cases

---

## Future Enhancements

1. **Image Generation Integration** (Priority: High)
   - Add "Generate Image" button in PlannedPostDrawer
   - Call image_generation_service with creative_prompt
   - Store generated image URL in planned post

2. **Caption Regeneration** (Priority: Medium)
   - Add "Regenerate Caption" button
   - Call content_generation_service with brand context
   - Allow user to pick from 3 variants

3. **Batch Image Generation** (Priority: Low)
   - Generate images for all planned posts in campaign
   - Background task with progress indicator
   - Notify when complete

---

## Related Files

**Backend**:
- `application/services/campaign_planner_service.py` - Prompt builder & plan creation
- `infrastructure/database/models/campaign_planned_post_model.py` - Data model
- `presentation/schemas/campaign_planner_schemas.py` - API schemas

**Frontend**:
- `components/campaign-planner/PlannedPostDrawer.tsx` - Post detail drawer
- `services/campaignPlannerService.ts` - API client & types
- `pages/CampaignPlannerDetail.tsx` - Calendar view

---

**Report Generated**: April 24, 2026  
**Status**: ✅ Major issues fixed, image generation pending
