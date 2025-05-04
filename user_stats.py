import time
from collections import Counter

class UserStats:
    """Tracks and analyzes user behavior during the simulation"""
    
    def __init__(self):
        self.start_time = time.time()
        self.commands_used = []
        self.wrong_answers = 0
        self.hints_requested = 0
        self.close_attempts = 0
        self.time_per_stage = {}
        self.current_stage_start = time.time()
        self.total_thinking_time = 0
        self.last_command_time = time.time()
        self.help_used = 0
        self.story_viewed = 0
        self.unique_commands = set()
        self.emotions = []
        
    def log_command(self, command):
        """Log a command used by the user"""
        current_time = time.time()
        thinking_time = current_time - self.last_command_time
        self.last_command_time = current_time
        
        if 0 < thinking_time < 300:
            self.total_thinking_time += thinking_time
            
        self.commands_used.append({
            'command': command,
            'timestamp': current_time,
            'thinking_time': thinking_time
        })
        self.unique_commands.add(command.upper())
        
        if command.upper() == "HELP":
            self.help_used += 1
        elif command.upper() == "HINT":
            self.hints_requested += 1
        elif command.upper() == "STORY":
            self.story_viewed += 1
    
    def log_wrong_answer(self):
        """Log a wrong answer"""
        self.wrong_answers += 1
    
    def log_close_attempt(self):
        """Log an attempt to close the terminal"""
        self.close_attempts += 1
    
    def log_stage_complete(self, stage):
        """Log completion of a story stage"""
        current_time = time.time()
        stage_time = current_time - self.current_stage_start
        self.time_per_stage[stage] = stage_time
        self.current_stage_start = current_time
    
    def log_emotion(self, emotion):
        """Log detected facial emotion"""
        self.emotions.append({
            'emotion': emotion,
            'timestamp': time.time()
        })
    
    def get_elapsed_time(self):
        """Get total elapsed time in seconds"""
        return int(time.time() - self.start_time)
    
    def get_average_thinking_time(self):
        """Get average thinking time between commands in seconds"""
        if len(self.commands_used) <= 1:
            return 0
        return self.total_thinking_time / (len(self.commands_used) - 1)
    
    def get_accuracy(self):
        """Calculate user accuracy percentage"""
        total_answers = self.wrong_answers + len(self.time_per_stage)
        if total_answers == 0:
            return 100
        return int(100 * len(self.time_per_stage) / total_answers)
    
    def get_persistence_score(self):
        """Calculate persistence score (1-10)"""
        base_score = min(10, max(1, len(self.commands_used) / 5))
        hint_penalty = min(5, self.hints_requested) * 0.5
        return min(10, max(1, base_score - hint_penalty))
    
    def get_efficiency_score(self):
        """Calculate efficiency score (1-10)"""
        if not self.time_per_stage:
            return 5
        avg_stage_time = sum(self.time_per_stage.values()) / len(self.time_per_stage)
        time_score = 10 - min(5, avg_stage_time / 60)
        wrong_answer_penalty = min(5, self.wrong_answers * 0.5)
        return min(10, max(1, time_score - wrong_answer_penalty))
    
    def get_curiosity_score(self):
        """Calculate curiosity score (1-10)"""
        unique_cmd_score = min(5, len(self.unique_commands) / 2)
        story_score = min(3, self.story_viewed)
        return min(10, max(1, unique_cmd_score + story_score))
    
    def get_adaptability_score(self):
        """Calculate adaptability score (1-10)"""
        base_score = 8
        hint_penalty = min(4, self.hints_requested * 0.8)
        help_penalty = min(3, self.help_used * 0.6)
        return min(10, max(1, base_score - hint_penalty - help_penalty))
    
    def get_emotion_summary(self):
        """Generate a summary of detected emotions"""
        if not self.emotions:
            return "No emotions detected.\n"
        
        emotion_counts = Counter(emotion['emotion'] for emotion in self.emotions)
        total = sum(emotion_counts.values())
        summary = "Emotion Analysis:\n"
        for emotion, count in emotion_counts.items():
            percentage = (count / total) * 100
            summary += f"{emotion.capitalize()}: {count} times ({percentage:.1f}%)\n"
        return summary
    
    def get_stats_report(self):
        """Generate a comprehensive stats report"""
        elapsed_time = self.get_elapsed_time()
        minutes, seconds = divmod(elapsed_time, 60)
        
        persistence = self.get_persistence_score()
        efficiency = self.get_efficiency_score()
        curiosity = self.get_curiosity_score()
        adaptability = self.get_adaptability_score()
        
        overall_score = (persistence + efficiency + curiosity + adaptability) / 4
        percentile = min(99, max(1, int(overall_score * 10)))
        
        report = f"""
Simulation Results:
-------------------
Time elapsed: {minutes} minutes {seconds} seconds
Commands used: {len(self.commands_used)}
Unique commands: {len(self.unique_commands)}
Riddle accuracy: {self.get_accuracy()}%
Close attempts: {self.close_attempts}
Hints requested: {self.hints_requested}

Performance Metrics:
-------------------
Persistence: {persistence:.1f}/10
Efficiency: {efficiency:.1f}/10
Curiosity: {curiosity:.1f}/10
Adaptability: {adaptability:.1f}/10

{self.get_emotion_summary()}

You rank in the top {percentile}% of participants.
"""
        if self.time_per_stage:
            report += "\nStage Completion Times:\n"
            for stage, time_taken in self.time_per_stage.items():
                minutes, seconds = divmod(int(time_taken), 60)
                report += f"Stage {stage}: {minutes}m {seconds}s\n"
        
        return report
    
    def log_event(self, event_type, details=None):
        """Log a general user event with timestamp"""
        if details is None:
            details = {}
        
        print(f"Event logged: {event_type}")
        
        if not hasattr(self, 'events'):
            self.events = []
        
        self.events.append({
            'type': event_type,
            'timestamp': time.time(),
            'details': details
        })