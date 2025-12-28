# NeuroBloom Development Tools - Quick Reference

## 🚀 Instant Testing Without Completing Tasks

### Method 1: Generate Test Sessions (Recommended)
```bash
# Generate 2 completed sessions (8 tasks total)
python generate_test_data.py 2

# Generate 5 sessions
python generate_test_data.py 5

# Clear all test data
python generate_test_data.py clear
```

### Method 2: Quick Dev Commands
```bash
# Complete current session instantly
python dev_tools.py complete

# Generate 3 sessions
python dev_tools.py generate 3

# Set 7-day streak
python dev_tools.py streak 7

# Clear everything
python dev_tools.py clear
```

### Method 3: Windows Batch (Easiest)
```bash
# Complete current session
test.bat complete

# Generate sessions
test.bat generate 3

# Set streak
test.bat streak 10

# Clear all
test.bat clear
```

## 📋 Common Testing Workflows

### Test Session Summary
```bash
python dev_tools.py complete
# Then visit: http://localhost:5174/session-summary?session=1
```

### Test Progress Page with Data
```bash
python generate_test_data.py 5
# Then visit: http://localhost:5174/progress
```

### Test Streak Tracking
```bash
python dev_tools.py streak 7
# Then visit: http://localhost:5174/progress
# You'll see 7-day streak 🔥
```

### Reset Everything
```bash
python dev_tools.py clear
# Fresh start - all sessions deleted
```

## 🎯 Quick Test Scenarios

### Scenario 1: Test New Feature (e.g., Session Summary)
1. `python dev_tools.py complete` - Instantly complete a session
2. Visit `/session-summary` - See the new feature immediately
3. No need to complete 4 tasks manually!

### Scenario 2: Test with Lots of Data
1. `python generate_test_data.py 10` - Generate 10 sessions
2. Visit `/progress` - See graphs with real data
3. Test performance, trends, etc.

### Scenario 3: Test Streak Features
1. `python dev_tools.py streak 15` - Set 15-day streak
2. Visit `/progress` - See streak card with 🔥 animation
3. Test freeze, longest streak, etc.

## 📝 Notes

- All scripts use User ID: 2, Training Plan ID: 1 (your demo account)
- Test data includes realistic scores (60-95%)
- Sessions are backdated over past days for realistic timeline
- Use `clear` command before important demos to clean up test data

## 💡 Pro Tips

1. **Before Testing New Feature**: Run `python dev_tools.py complete`
2. **Need More Data**: Run `python generate_test_data.py 5`  
3. **Clean Slate**: Run `python dev_tools.py clear`
4. **Quick Streak Test**: Run `python dev_tools.py streak 7`

Now you can build and test features FAST! 🚀
