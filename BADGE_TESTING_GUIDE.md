# 🏆 Badge Testing Guide

This guide shows you how to test the badge unlocking system using the Dev Panel.

## Quick Test Flow

### 1. **Open Dev Panel**
- Click the purple 🛠️ button in bottom-right corner of any page
- The dev panel will slide open

### 2. **Test Badge Unlocking**

#### Option A: Complete Sessions (Realistic Testing)
```
1. Click "Complete Session" → Completes 4 tasks
2. Click "Check Badges" → Awards any eligible badges
3. See badge notification popup if new badges earned!
```

#### Option B: Generate Multiple Sessions (Fast Testing)
```
1. Click "Generate 3 Sessions" → Creates 12 completed tasks
2. Click "Check Badges" → Awards badges based on progress
3. Watch for badge notifications!
```

#### Option C: Test Streak Badges
```
1. Click "Set 7-Day Streak" → Sets streak to 7 days
2. Click "Check Badges" → Should earn streak badges
3. Try different streak values (3, 14, 30, 100)
```

### 3. **View Your Badges**
- Go to **Progress** page
- Scroll down to see **Achievement Badges** section
- Filter by category (Streaks, Milestones, Performance, etc.)

## Badge Categories & Requirements

### 🎯 Getting Started
- **First Steps** (🎯): Complete 1 session
- **Dedicated Learner** (📚): Complete 5 sessions
- **Consistent Trainer** (💪): Complete 10 sessions
- **Brain Athlete** (🏃): Complete 25 sessions
- **Mental Warrior** (⚔️): Complete 50 sessions
- **Master Trainer** (👑): Complete 100 sessions

### 🔥 Streaks
- **Hot Start** (🔥): 3-day streak
- **Week Warrior** (🌟): 7-day streak
- **Fortnight Champion** (💫): 14-day streak
- **Monthly Master** (🌙): 30-day streak
- **Unstoppable** (🚀): 100-day streak

### 💯 Performance
- **Perfectionist** (💯): Score 100% accuracy + 95% score
- **Sharpshooter** (🎯): Achieve 95% accuracy in session
- **Rising Star** (⭐): Reach difficulty level 5
- **Advanced Learner** (🌟): Reach difficulty level 7
- **Elite Mind** (💎): Reach difficulty level 10

### 🎓 Mastery
- **Well Rounded** (🎨): Complete tasks in all 6 domains
- **Domain Expert** (🎓): Complete 20 tasks in one domain

### ⚡ Speed
- **Speed Demon** (⚡): Complete session in under 10 minutes

### 📈 Improvement
- **Growth Mindset** (📈): Improve score by 20+ points

## Testing Scenarios

### Scenario 1: First-Time User
```
1. Clear All Data (fresh start)
2. Complete Session → Should earn "First Steps" 🎯
3. Check Badges → Confirms badge awarded
4. View Progress page → See badge in showcase
```

### Scenario 2: Session Milestones
```
1. Generate 3 Sessions (total: 3 sessions)
2. Check Badges → No new badges yet
3. Generate 3 Sessions (total: 6 sessions)
4. Check Badges → Should earn "Dedicated Learner" 📚
```

### Scenario 3: Streak Testing
```
1. Set 7-Day Streak
2. Check Badges → Should earn both:
   - "Hot Start" 🔥 (3-day)
   - "Week Warrior" 🌟 (7-day)
3. Set 30-Day Streak
4. Check Badges → Should earn:
   - "Fortnight Champion" 💫 (14-day)
   - "Monthly Master" 🌙 (30-day)
```

### Scenario 4: Multiple Badges at Once
```
1. Clear All Data
2. Generate 3 Sessions (12 tasks total)
3. Set 7-Day Streak
4. Check Badges → Should earn multiple badges:
   - First Steps (1 session)
   - Dedicated Learner (5+ sessions)
   - Hot Start (3-day streak)
   - Week Warrior (7-day streak)
   - Well Rounded (all 4 domains completed)
```

## Expected Behavior

### ✅ When Badge is Earned
1. **Backend**: Badge saved to database
2. **API Response**: Returns badge details
3. **Frontend**: Shows notification popup
4. **Animation**: 
   - Popup slides in from right
   - Badge icon spins/celebrates
   - Auto-dismisses after 4 seconds
5. **Progress Page**: Badge appears in showcase with earned date

### 📊 Badge Progress Tracking
- **Progress Page** shows:
  - Total badges: X/19
  - Progress ring (percentage completed)
  - Category filters
  - Earned badges (gold background)
  - Locked badges (grayscale, lower opacity)

## Dev Panel Features

### 🛠️ Available Commands
1. **✓ Complete Session** - Adds 4 tasks, checks badges automatically
2. **📊 Generate 3 Sessions** - Creates 12 tasks across multiple days
3. **🔥 Set 7-Day Streak** - Instant streak for testing
4. **🏆 Check Badges** - Manually trigger badge checking (NEW!)
5. **🗑️ Clear All Data** - Reset everything

### 💡 Pro Tips
- Use "Generate Sessions" to quickly test milestone badges
- Use "Set Streak" to test streak badges without waiting
- "Check Badges" button shows which badges were just earned
- Badges are checked automatically when completing sessions
- Can't earn the same badge twice (database unique constraint)

## Debugging

### If Badges Don't Appear
1. Check browser console for errors
2. Verify backend is running (port 8000)
3. Check database: `SELECT * FROM user_badges WHERE user_id = 2;`
4. Ensure training plan exists for user
5. Try "Check Badges" button to manually trigger

### To Reset Badge Testing
```
1. Click "Clear All Data" in dev panel
2. Manually delete badges (if needed):
   DELETE FROM user_badges WHERE user_id = 2;
3. Start fresh testing
```

## API Endpoints (for manual testing)

```bash
# Get user's earned badges
GET http://localhost:8000/training/badges/2

# Get all badges (earned + locked)
GET http://localhost:8000/training/badges/available/2

# Check and award badges (DEV)
POST http://localhost:8000/training/dev/check-badges/2

# Get recent badges
GET http://localhost:8000/training/badges/recent/2?limit=5
```

## Success Indicators ✅

You'll know badges are working when:
- [ ] Badge notification popup appears after completing session
- [ ] Badge shows in Progress page showcase
- [ ] Badge has earned date timestamp
- [ ] Can filter badges by category
- [ ] Multiple badges earned simultaneously show sequentially
- [ ] Locked badges appear grayed out
- [ ] Progress ring updates with completion %

Happy badge testing! 🎉
