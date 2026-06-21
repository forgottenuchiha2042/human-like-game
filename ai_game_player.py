import random
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod


class DifficultyLevel(Enum):
    """AI difficulty levels affecting decision quality and reaction time"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class TouchEvent:
    """Represents a single touch event with realistic variations"""
    x: float
    y: float
    timestamp: float
    duration: float
    pressure: float


@dataclass
class GameState:
    """Represents current game state"""
    board: List[List[int]]
    score: int
    moves_remaining: int
    level: int
    game_active: bool


class HumanTouchSimulator:
    """Simulates realistic human touch behavior"""
    
    def __init__(self, consistency: float = 0.7):
        """
        Args:
            consistency: 0.0-1.0, how consistent the touch pattern is
                        1.0 = perfect/bot-like, 0.0 = very erratic
        """
        self.consistency = consistency
        self.last_touch_time = 0
        self.touch_history = []
    
    def add_touch_jitter(self, x: float, y: float, radius: float = 15) -> Tuple[float, float]:
        """Add realistic positional jitter to touches"""
        jitter_amount = (1 - self.consistency) * radius
        jitter_x = np.random.normal(0, jitter_amount)
        jitter_y = np.random.normal(0, jitter_amount)
        return x + jitter_x, y + jitter_y
    
    def get_touch_duration(self, base_duration: float = 0.1) -> float:
        """Get realistic touch duration with human-like variance"""
        variance = (1 - self.consistency) * 0.15
        duration = np.random.normal(base_duration, variance)
        return max(0.05, duration)  # Minimum 50ms
    
    def get_inter_touch_delay(self, base_delay: float = 0.5) -> float:
        """Get delay between touches with human-like inconsistency"""
        # Humans don't touch at perfectly regular intervals
        variance = (1 - self.consistency) * base_delay * 0.4
        delay = np.random.normal(base_delay, variance)
        # Add occasional hesitation (human deliberation)
        if random.random() < (1 - self.consistency) * 0.15:
            delay += random.uniform(0.3, 1.5)
        return max(0.1, delay)
    
    def get_pressure(self) -> float:
        """Simulate touch pressure (0.0-1.0)"""
        # Human pressure varies slightly
        base_pressure = 0.7
        variance = (1 - self.consistency) * 0.2
        pressure = np.random.normal(base_pressure, variance)
        return max(0.3, min(1.0, pressure))
    
    def simulate_touch(self, target_x: float, target_y: float) -> TouchEvent:
        """Simulate a complete touch event"""
        jittered_x, jittered_y = self.add_touch_jitter(target_x, target_y)
        duration = self.get_touch_duration()
        pressure = self.get_pressure()
        
        current_time = time.time()
        touch = TouchEvent(
            x=jittered_x,
            y=jittered_y,
            timestamp=current_time,
            duration=duration,
            pressure=pressure
        )
        
        self.touch_history.append(touch)
        return touch
    
    def get_reaction_time(self, base_time: float = 0.3) -> float:
        """Get realistic reaction time to game events"""
        # Variance increases with decreased consistency
        variance = (1 - self.consistency) * base_time * 0.5
        reaction = np.random.normal(base_time, variance)
        # Occasional slow reactions (distraction/thinking)
        if random.random() < (1 - self.consistency) * 0.1:
            reaction += random.uniform(0.5, 2.0)
        return max(0.1, reaction)


class GameAI(ABC):
    """Abstract base class for game AI"""
    
    def __init__(self, difficulty: DifficultyLevel, consistency: float = 0.7):
        self.difficulty = difficulty
        self.touch_simulator = HumanTouchSimulator(consistency)
        self.game_state = None
        self.decision_history = []
    
    @abstractmethod
    def analyze_board(self, board: List[List[int]]) -> List[Tuple[int, int, float]]:
        """
        Analyze game board and return list of (x, y, score) tuples
        representing possible moves ranked by desirability
        """
        pass
    
    @abstractmethod
    def select_move(self, possible_moves: List[Tuple[int, int, float]]) -> Tuple[int, int]:
        """Select a move from available options based on difficulty"""
        pass
    
    def should_make_mistake(self) -> bool:
        """Determine if AI should make a deliberate mistake"""
        mistake_rates = {
            DifficultyLevel.BEGINNER: 0.35,
            DifficultyLevel.INTERMEDIATE: 0.15,
            DifficultyLevel.ADVANCED: 0.05,
            DifficultyLevel.EXPERT: 0.01,
        }
        return random.random() < mistake_rates[self.difficulty]
    
    def get_decision_confidence(self) -> float:
        """Get AI's confidence in its decision (affects hesitation)"""
        base_confidence = {
            DifficultyLevel.BEGINNER: 0.4,
            DifficultyLevel.INTERMEDIATE: 0.6,
            DifficultyLevel.ADVANCED: 0.8,
            DifficultyLevel.EXPERT: 0.95,
        }
        # Add some natural variance
        confidence = base_confidence[self.difficulty]
        variance = random.gauss(0, 0.1)
        return max(0.0, min(1.0, confidence + variance))


class ToonBlastAI(GameAI):
    """AI specifically designed for Toon Blast-like games"""
    
    def analyze_board(self, board: List[List[int]]) -> List[Tuple[int, int, float]]:
        """
        Analyze board for matches (3+ same tiles)
        Returns moves scored by:
        - Immediate points
        - Cascading potential
        - Special piece creation
        """
        moves = []
        
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] == 0:  # Empty
                    continue
                
                score = self._evaluate_position(board, row, col)
                if score > 0:
                    moves.append((row, col, score))
        
        # Sort by score descending
        return sorted(moves, key=lambda x: x[2], reverse=True)
    
    def _evaluate_position(self, board: List[List[int]], row: int, col: int) -> float:
        """Evaluate score for a specific position"""
        tile_type = board[row][col]
        if tile_type == 0:
            return 0
        
        score = 0
        
        # Horizontal matches
        left_count = self._count_adjacent(board, row, col, 0, -1, tile_type)
        right_count = self._count_adjacent(board, row, col, 0, 1, tile_type)
        horizontal_matches = left_count + right_count + 1
        
        # Vertical matches
        up_count = self._count_adjacent(board, row, col, -1, 0, tile_type)
        down_count = self._count_adjacent(board, row, col, 1, 0, tile_type)
        vertical_matches = up_count + down_count + 1
        
        # Score calculation (simplified)
        if horizontal_matches >= 3:
            score += horizontal_matches * 10
            if horizontal_matches >= 4:
                score += 50  # Bonus for 4+ match
        
        if vertical_matches >= 3:
            score += vertical_matches * 10
            if vertical_matches >= 4:
                score += 50  # Bonus for 4+ match
        
        # Cascade potential (rough estimate)
        if horizontal_matches >= 3 or vertical_matches >= 3:
            score += random.randint(5, 20)
        
        return score
    
    def _count_adjacent(self, board: List[List[int]], row: int, col: int, 
                       dr: int, dc: int, tile_type: int) -> int:
        """Count adjacent tiles of same type in given direction"""
        count = 0
        r, c = row + dr, col + dc
        
        while 0 <= r < len(board) and 0 <= c < len(board[0]):
            if board[r][c] == tile_type:
                count += 1
                r += dr
                c += dc
            else:
                break
        
        return count
    
    def select_move(self, possible_moves: List[Tuple[int, int, float]]) -> Tuple[int, int]:
        """Select move based on difficulty with human-like inconsistency"""
        if not possible_moves:
            return None
        
        # Random mistake
        if self.should_make_mistake():
            selected = random.choice(possible_moves)
        else:
            # Difficulty affects how consistently we pick the best move
            selection_quality = {
                DifficultyLevel.BEGINNER: 0.5,
                DifficultyLevel.INTERMEDIATE: 0.7,
                DifficultyLevel.ADVANCED: 0.85,
                DifficultyLevel.EXPERT: 0.95,
            }
            
            quality = selection_quality[self.difficulty]
            if random.random() < quality:
                selected = possible_moves[0]  # Best move
            else:
                # Pick from top moves with weighted randomness
                top_count = max(1, int(len(possible_moves) * 0.3))
                selected = random.choice(possible_moves[:top_count])
        
        self.decision_history.append({
            'move': selected,
            'considered': len(possible_moves),
            'confidence': self.get_decision_confidence()
        })
        
        return (selected[0], selected[1])


class GardenscapesAI(GameAI):
    """AI specifically designed for Gardenscapes-like games"""
    
    def analyze_board(self, board: List[List[int]]) -> List[Tuple[int, int, float]]:
        """
        Analyze board for puzzle solution
        Prioritizes:
        - Clearing specific tile types
        - Creating and using power-ups
        - Path finding
        """
        moves = []
        
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] <= 0:
                    continue
                
                score = self._evaluate_puzzle_position(board, row, col)
                if score > 0:
                    moves.append((row, col, score))
        
        return sorted(moves, key=lambda x: x[2], reverse=True)
    
    def _evaluate_puzzle_position(self, board: List[List[int]], row: int, col: int) -> float:
        """Evaluate position for puzzle-solving"""
        tile_type = board[row][col]
        score = 0
        
        # Check for match
        if self._has_adjacent_match(board, row, col, tile_type):
            score += 20
        
        # Check for power-up potential
        if board[row][col] > 3:  # Special tiles
            score += 30
        
        # Check position importance (center is often more valuable)
        center_x = len(board) / 2
        center_y = len(board[0]) / 2
        distance = abs(row - center_x) + abs(col - center_y)
        score += max(0, 20 - distance)
        
        return score
    
    def _has_adjacent_match(self, board: List[List[int]], row: int, col: int, tile_type: int) -> bool:
        """Check if position can form a match"""
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < len(board) and 0 <= nc < len(board[0]):
                if board[nr][nc] == tile_type:
                    return True
        return False
    
    def select_move(self, possible_moves: List[Tuple[int, int, float]]) -> Tuple[int, int]:
        """Select move with puzzle-solving approach"""
        if not possible_moves:
            return None
        
        if self.should_make_mistake():
            selected = random.choice(possible_moves)
        else:
            # Puzzle games often benefit from deliberate play
            planning_quality = {
                DifficultyLevel.BEGINNER: 0.4,
                DifficultyLevel.INTERMEDIATE: 0.65,
                DifficultyLevel.ADVANCED: 0.82,
                DifficultyLevel.EXPERT: 0.93,
            }
            
            if random.random() < planning_quality[self.difficulty]:
                selected = possible_moves[0]
            else:
                top_count = max(2, int(len(possible_moves) * 0.4))
                selected = random.choice(possible_moves[:top_count])
        
        return (selected[0], selected[1])


class GameSession:
    """Manages a complete game session with touch simulation"""
    
    def __init__(self, ai: GameAI, initial_board: List[List[int]]):
        self.ai = ai
        self.board = [row[:] for row in initial_board]  # Deep copy
        self.session_start = time.time()
        self.moves_made = []
        self.touch_events = []
    
    def play_turn(self) -> Optional[TouchEvent]:
        """Execute one AI turn with realistic touch simulation"""
        # AI analyzes board
        possible_moves = self.ai.analyze_board(self.board)
        
        if not possible_moves:
            return None
        
        # Get reaction time
        reaction_time = self.ai.touch_simulator.get_reaction_time()
        time.sleep(reaction_time)
        
        # Select move
        selected_row, selected_col = self.ai.select_move(possible_moves)
        
        # Simulate touch with human-like behavior
        touch = self.ai.touch_simulator.simulate_touch(
            float(selected_col), 
            float(selected_row)
        )
        
        self.touch_events.append(touch)
        self.moves_made.append((selected_row, selected_col))
        
        # Simulate board update (simplified)
        self._update_board(selected_row, selected_col)
        
        return touch
    
    def _update_board(self, row: int, col: int):
        """Update board state after move (simplified)"""
        if self.board[row][col] > 0:
            self.board[row][col] = 0  # Remove tile
    
    def get_session_stats(self) -> dict:
        """Get statistics about the game session"""
        if not self.touch_events:
            return {}
        
        touch_times = [
            self.touch_events[i+1].timestamp - self.touch_events[i].timestamp
            for i in range(len(self.touch_events) - 1)
        ]
        
        return {
            'total_moves': len(self.moves_made),
            'session_duration': time.time() - self.session_start,
            'avg_inter_touch_time': np.mean(touch_times) if touch_times else 0,
            'touch_time_variance': np.std(touch_times) if touch_times else 0,
            'avg_touch_pressure': np.mean([t.pressure for t in self.touch_events]),
            'decision_confidence_avg': np.mean([
                d['confidence'] for d in self.ai.decision_history
            ]) if self.ai.decision_history else 0,
        }


# Example usage
if __name__ == "__main__":
    # Create a sample board
    sample_board = [
        [1, 2, 3, 1, 2],
        [3, 1, 2, 3, 1],
        [2, 3, 1, 2, 3],
        [1, 2, 3, 1, 2],
        [3, 1, 2, 3, 1],
    ]
    
    # Create AI and play
    ai = ToonBlastAI(DifficultyLevel.INTERMEDIATE, consistency=0.6)
    session = GameSession(ai, sample_board)
    
    # Play 5 turns
    for i in range(5):
        touch = session.play_turn()
        if touch:
            print(f"Turn {i+1}: Touched ({touch.x:.1f}, {touch.y:.1f}) "
                  f"with pressure {touch.pressure:.2f}")
    
    # Print statistics
    stats = session.get_session_stats()
    print("\nSession Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.3f}")
