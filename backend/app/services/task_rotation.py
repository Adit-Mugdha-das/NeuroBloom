"""
Task Selection and Rotation Service
Implements smart rotation to prevent task repetition and boredom
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlmodel import Session, select, and_, desc, col
from app.models.training_session import TrainingSession
from app.models.cognitive_task import CognitiveTask, UserTaskPreference

class TaskRotationService:
    """
    Manages task selection with smart rotation logic.
    Prevents repetition while maintaining clinical validity.
    """
    
    # Task rotation strategies per domain
    ROTATION_CONFIG = {
        'working_memory': {
            'strategy': 'sequential',  # Don't repeat same task twice in a row
            'max_repeats': 1,
            'exclude_last_n': 2  # Don't use same task from last 2 sessions
        },
        'processing_speed': {
            'strategy': 'weighted',  # SDMT more frequent (gold standard)
            'weights': {
                'simple_reaction': 0.25,
                'sdmt': 0.40,  # Prioritize SDMT when implemented
                'trails_a': 0.20,
                'pattern_comparison': 0.15
            },
            'exclude_last_n': 1
        },
        'attention': {
            'strategy': 'random',  # Unpredictable
            'exclude_last_n': 2
        },
        'flexibility': {
            'strategy': 'adaptive',  # Based on user struggle
            'exclude_last_n': 2
        },
        'planning': {
            'strategy': 'balanced',  # Equal exposure
            'exclude_last_n': 1,
            'alternate_types': True  # Alternate visual vs verbal
        },
        'visual_scanning': {
            'strategy': 'difficulty_matched',
            'exclude_last_n': 2
        }
    }
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_available_tasks(self, domain: str, include_baseline: bool = True) -> List[CognitiveTask]:
        """Get all available tasks for a domain"""
        query = select(CognitiveTask).where(CognitiveTask.domain == domain)
        
        if not include_baseline:
            query = query.where(CognitiveTask.is_baseline_task == False)
        
        tasks = self.session.exec(query).all()
        return list(tasks)
    
    def get_recent_tasks(self, user_id: int, domain: str, last_n_sessions: int = 3) -> List[str]:
        """Get task codes used in recent sessions for this domain"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)  # Look back max 30 days
        
        query = select(TrainingSession.task_code).where(
            and_(
                TrainingSession.user_id == user_id,
                TrainingSession.domain == domain,
                TrainingSession.task_code != None,
                TrainingSession.created_at >= cutoff_date
            )
        ).order_by(desc(TrainingSession.created_at)).limit(last_n_sessions)
        
        recent = self.session.exec(query).all()
        return [task_code for task_code in recent if task_code]
    
    def get_user_preferences(self, user_id: int) -> Dict[str, str]:
        """Get user's task preferences"""
        query = select(UserTaskPreference).where(UserTaskPreference.user_id == user_id)
        prefs = self.session.exec(query).all()
        return {pref.task_code: pref.preference for pref in prefs}
    
    def select_task_for_session(
        self, 
        user_id: int, 
        domain: str,
        is_baseline: bool = False
    ) -> Optional[CognitiveTask]:
        """
        Select appropriate task for this session using rotation logic.
        
        Args:
            user_id: User ID
            domain: Cognitive domain (working_memory, attention, etc.)
            is_baseline: If True, always return baseline task for this domain
            
        Returns:
            CognitiveTask object
        """
        
        # For baseline assessment, always use baseline task
        if is_baseline:
            query = select(CognitiveTask).where(
                and_(
                    CognitiveTask.domain == domain,
                    CognitiveTask.is_baseline_task == True
                )
            )
            return self.session.exec(query).first()
        
        # Get available tasks
        available_tasks = self.get_available_tasks(domain, include_baseline=True)
        
        if not available_tasks:
            raise ValueError(f"No tasks available for domain: {domain}")
        
        # Get recent task history
        config = self.ROTATION_CONFIG.get(domain, {'strategy': 'random', 'exclude_last_n': 2})
        recent_tasks = self.get_recent_tasks(user_id, domain, config.get('exclude_last_n', 2))
        
        # Filter out recently used tasks
        candidate_tasks = [
            task for task in available_tasks 
            if task.task_code not in recent_tasks
        ]
        
        # If all tasks were recent, use least recent
        if not candidate_tasks:
            candidate_tasks = available_tasks
        
        # Get user preferences
        preferences = self.get_user_preferences(user_id)
        
        # Apply selection strategy
        strategy = config.get('strategy', 'random')
        
        if strategy == 'sequential':
            # Select next task in sequence, avoiding recent
            return self._select_sequential(candidate_tasks, recent_tasks)
        
        elif strategy == 'weighted':
            # Weighted random selection
            weights = config.get('weights', {})
            return self._select_weighted(candidate_tasks, weights, preferences)
        
        elif strategy == 'random':
            # Pure random from candidates
            return random.choice(candidate_tasks)
        
        elif strategy == 'adaptive':
            # Select based on user's weakest performance
            return self._select_adaptive(user_id, candidate_tasks)
        
        elif strategy == 'balanced':
            # Ensure equal exposure over time
            return self._select_balanced(user_id, candidate_tasks)
        
        else:
            # Default to random
            return random.choice(candidate_tasks)
    
    def _select_sequential(self, candidates: List[CognitiveTask], recent: List[str]) -> CognitiveTask:
        """Select next task in sequence"""
        # Sort by task_code to create consistent ordering
        sorted_tasks = sorted(candidates, key=lambda t: t.task_code)
        
        if recent:
            # Find last used task and select next
            try:
                last_idx = next(i for i, t in enumerate(sorted_tasks) if t.task_code == recent[0])
                next_idx = (last_idx + 1) % len(sorted_tasks)
                return sorted_tasks[next_idx]
            except StopIteration:
                pass
        
        return sorted_tasks[0]
    
    def _select_weighted(
        self, 
        candidates: List[CognitiveTask], 
        weights: Dict[str, float],
        preferences: Dict[str, str]
    ) -> CognitiveTask:
        """Weighted random selection with preference boost"""
        
        task_weights = []
        for task in candidates:
            base_weight = weights.get(task.task_code, 1.0 / len(candidates))
            
            # Boost favorites, reduce dislikes
            pref = preferences.get(task.task_code, 'neutral')
            if pref == 'favorite':
                base_weight *= 1.5
            elif pref == 'dislike':
                base_weight *= 0.5
            
            task_weights.append(base_weight)
        
        # Normalize weights
        total = sum(task_weights)
        if total > 0:
            task_weights = [w / total for w in task_weights]
        
        return random.choices(candidates, weights=task_weights, k=1)[0]
    
    def _select_adaptive(self, user_id: int, candidates: List[CognitiveTask]) -> CognitiveTask:
        """Select task where user performs worst (needs more practice)"""
        
        # Get average performance for each task
        task_performance = {}
        for task in candidates:
            query = select(TrainingSession.score).where(
                and_(
                    TrainingSession.user_id == user_id,
                    TrainingSession.task_code == task.task_code
                )
            ).limit(10)  # Last 10 sessions
            
            scores = self.session.exec(query).all()
            if scores:
                task_performance[task.task_code] = sum(scores) / len(scores)
        
        if not task_performance:
            return random.choice(candidates)
        
        # Select task with lowest average score (needs practice)
        weakest_task_code = min(task_performance.keys(), key=lambda k: task_performance.get(k, 0))
        return next(t for t in candidates if t.task_code == weakest_task_code)
    
    def _select_balanced(self, user_id: int, candidates: List[CognitiveTask]) -> CognitiveTask:
        """Ensure equal exposure to all tasks over time"""
        
        # Count usage of each task
        task_counts = {}
        for task in candidates:
            query = select(TrainingSession).where(
                and_(
                    TrainingSession.user_id == user_id,
                    TrainingSession.task_code == task.task_code
                )
            )
            count = len(self.session.exec(query).all())
            task_counts[task.task_code] = count
        
        if not task_counts:
            return random.choice(candidates)
        
        # Select least-used task
        min_count = min(task_counts.values())
        least_used = [t for t in candidates if task_counts.get(t.task_code, 0) == min_count]
        
        return random.choice(least_used)
    
    def select_session_tasks(
        self, 
        user_id: int,
        domains: Optional[List[str]] = None,
        is_baseline: bool = False
    ) -> Dict[str, CognitiveTask]:
        """
        Select tasks for a complete training session (one task per domain).
        
        Args:
            user_id: User ID
            domains: List of domains to include (default: all 4 core domains)
            is_baseline: If True, select only baseline tasks
            
        Returns:
            Dict mapping domain to selected CognitiveTask
        """
        
        if domains is None:
            # Use 4 core domains for standard session
            domains = ['working_memory', 'processing_speed', 'attention', 'flexibility']
        
        selected_tasks = {}
        for domain in domains:
            task = self.select_task_for_session(user_id, domain, is_baseline)
            selected_tasks[domain] = task
        
        return selected_tasks
