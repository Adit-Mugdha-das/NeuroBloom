# Tower of London - Minimum Moves Calculation

## Overview

Algorithm for calculating the minimum number of moves to solve Tower of London puzzles in NeuroBloom.

**Algorithm:** Breadth-First Search (BFS)  
**Date:** March 2, 2026

## Problem Description

**Tower of London** is a cognitive puzzle with:
- 3 pegs of different heights (capacities: 3, 2, 1 discs)
- Colored discs that must be rearranged from start to goal configuration
- One disc moved at a time
- Each peg has limited capacity

## Why BFS?

BFS is optimal for this problem because:

1. **Guarantees shortest path** - First solution found is the minimum
2. **Unweighted moves** - Each move costs 1 (BFS excels here)
3. **Complete** - Always finds a solution if one exists
4. **Simple** - Straightforward implementation and maintenance

## Algorithm Design

**State Representation:**
```python
state = [[disc1, disc2], [disc3], []]  # 3 pegs with discs (bottom to top)
```

**Core Components:**
- **Queue (FIFO)** - Explores states breadth-first
- **Visited Set** - Prevents cycles
- **Move Generator** - Creates valid next states
- **Goal Checker** - Detects solution

## How It Works

```
1. Initialize: queue = [(start_state, 0)], visited = {start_state}

2. While queue not empty:
   - Dequeue (current_state, moves)
   - If current_state == goal_state: return moves ✓
   - For each valid move:
     * Generate next_state
     * If not visited:
       - Add to visited
       - Enqueue (next_state, moves + 1)

3. If queue empty: return -1 (no solution)
```

**Valid moves:** Source peg has discs AND destination has capacity

## Implementation

```python
from collections import deque

def calculate_minimum_moves(start_state, goal_state, peg_capacities):
    """Calculate minimum moves using BFS."""
    queue = deque([(start_state, 0)])
    visited = {tuple(tuple(peg) for peg in start_state)}
    
    while queue:
        current_state, moves = queue.popleft()
        
        if current_state == goal_state:
            return moves
        
        # Try all valid moves
        for from_peg in range(len(current_state)):
            if not current_state[from_peg]:
                continue
            
            for to_peg in range(len(current_state)):
                if from_peg == to_peg:
                    continue
                if len(current_state[to_peg]) >= peg_capacities[to_peg]:
                    continue
                
                # Apply move
                new_state = [peg[:] for peg in current_state]
                new_state[to_peg].append(new_state[from_peg].pop())
                
                state_tuple = tuple(tuple(peg) for peg in new_state)
                if state_tuple not in visited:
                    visited.add(state_tuple)
                    queue.append((new_state, moves + 1))
    
    return -1  # No solution
```

## Complexity

**Time:** O(b^d) where b=branching factor, d=depth (minimum moves)  
**Space:** O(s) where s=unique states visited  
**Typical:** 3-4 discs < 1ms, 5-6 discs < 10ms

## Alternatives Considered

| Algorithm | Pros | Cons | Verdict |
|-----------|------|------|---------|
| **DFS** | Lower space, simple | ❌ No minimum guarantee | ✗ Not suitable |
| **A\*** | Optimal, potentially faster | ❌ Needs heuristic, complex | ✗ Overkill |
| **Greedy** | Fast, low memory | ❌ No optimality, unreliable | ✗ Unreliable |
| **DP** | Handles subproblems | ❌ Complex, large state space | ✗ Poor fit |

## Optimizations

1. **Early termination** - Stop when goal found
2. **Efficient hashing** - Use tuples for O(1) visited lookup
3. **Bidirectional search** - Search from both ends (reduces O(b^d) to O(b^(d/2)))
4. **Move pruning** - Skip redundant moves (immediate undo, symmetric states)
5. **State caching** - Pre-compute common configurations

## Testing

**Test Cases:**
- Trivial: start == goal → 0 moves
- Simple: 1-3 moves required
- Complex: 5+ moves, multiple paths
- Edge cases: impossible configs, capacity limits

**Example:**
```python
assert calculate_minimum_moves([[1, 2], [], []], [[1, 2], [], []], [3, 2, 1]) == 0
assert calculate_minimum_moves([[1], [2], []], [[1, 2], [], []], [3, 2, 1]) == 1
```

## Integration with NeuroBloom

**Game Flow:**
1. Generate start/goal configurations → calculate minimum moves
2. Track user's moves → compare to optimal
3. Calculate performance score

**Scoring:**
```python
efficiency = (minimum_moves / user_moves) * 100
time_bonus = max(0, 100 - time_taken_seconds)
final_score = (efficiency + time_bonus) / 2
```

## Displaying Solutions

**Visual Playback:** Show optimal solution step-by-step after completion

**Implementation:** Track path in BFS:
```python
def calculate_with_path(start_state, goal_state, peg_capacities):
    queue = deque([(start_state, 0, [])])
    visited = {tuple(tuple(peg) for peg in start_state)}
    
    while queue:
        current_state, moves, path = queue.popleft()
        
        if current_state == goal_state:
            return moves, path
        
        # ... generate moves and add (next_state, moves+1, path+[(from,to)])
    
    return -1, []
```

## Common Pitfalls

1. **Infinite loops** - Use visited set to prevent cycles
2. **State hashing** - Convert mutable lists to immutable tuples
3. **Shallow copying** - Use deep copy `[peg[:] for peg in state]`
4. **Capacity checks** - Validate destination capacity before moves

## References

- **BFS:** Classic graph traversal for shortest paths
- **Tower of London:** Shallice (1982) - Cognitive planning assessment
- **State-Space Search:** Russell & Norvig - AI: A Modern Approach

---

**Last Updated:** March 2, 2026
