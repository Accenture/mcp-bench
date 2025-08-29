"""
Execution Context for Managing Multi-layered Retry Strategy

Tracks state across multiple retry attempts to ensure idempotent operations.
"""

import time
from dataclasses import dataclass
from typing import Optional
import config.config_loader as config_loader


@dataclass
class ExecutionContext:
    """Tracks execution state to manage retry strategies and prevent duplicate operations."""
    
    # Compression state
    is_compressed: bool = False
    compression_timestamp: Optional[float] = None
    
    # Token reduction tracking
    current_token_reduction: int = 0
    _token_reduction_factors: Optional[list] = None
    
    # Format fix tracking
    current_format_fixes: int = 0
    max_format_fixes: int = 5
    
    # Round tracking
    current_round: int = 1
    max_rounds: int = 3
    
    # Task retry tracking
    current_task_retry: int = 1
    max_task_retries: int = 3
    
    def can_compress(self) -> bool:
        """Check if compression is allowed (only once per execution)."""
        return not self.is_compressed
    
    def mark_compressed(self) -> None:
        """Mark that compression has been performed."""
        self.is_compressed = True
        self.compression_timestamp = time.time()
    
    @property
    def token_reduction_factors(self) -> list:
        """Get token reduction factors from configuration."""
        if self._token_reduction_factors is None:
            self._token_reduction_factors = config_loader.get_token_reduction_factors()
        return self._token_reduction_factors
    
    @property
    def max_token_reductions(self) -> int:
        """Maximum number of token reductions based on configured factors."""
        return len(self.token_reduction_factors)
    
    def can_reduce_tokens(self) -> bool:
        """Check if token reduction is still possible."""
        return self.current_token_reduction < self.max_token_reductions
    
    def apply_token_reduction(self, original_max_tokens: int) -> int:
        """Apply next level of token reduction and return new max_tokens."""
        if not self.can_reduce_tokens():
            return original_max_tokens
        
        self.current_token_reduction += 1
        
        # Use configured reduction factors
        factor_index = self.current_token_reduction - 1
        if factor_index < len(self.token_reduction_factors):
            reduction_factor = self.token_reduction_factors[factor_index]
            return int(original_max_tokens * reduction_factor)
        else:
            return original_max_tokens
    
    def can_fix_format(self) -> bool:
        """Check if format fixing is still possible."""
        return self.current_format_fixes < self.max_format_fixes
    
    def increment_format_fixes(self) -> None:
        """Increment format fix counter."""
        self.current_format_fixes += 1
    
    def can_retry_round(self) -> bool:
        """Check if we can start a new round."""
        return self.current_round < self.max_rounds
    
    def start_new_round(self) -> None:
        """Start a new round, resetting token and format counters."""
        if self.can_retry_round():
            self.current_round += 1
            self.current_token_reduction = 0
            self.current_format_fixes = 0
            # Keep compression state - it persists across rounds
    
    def can_retry_task(self) -> bool:
        """Check if we can retry the entire task."""
        return self.current_task_retry < self.max_task_retries
    
    def start_new_task_retry(self) -> None:
        """Start a new task retry, resetting all counters except task retry."""
        if self.can_retry_task():
            self.current_task_retry += 1
            self.current_round = 1
            self.current_token_reduction = 0
            self.current_format_fixes = 0
            # Reset compression state for new task retry
            self.is_compressed = False
            self.compression_timestamp = None
    
    def get_status_summary(self) -> str:
        """Get a summary of current execution state."""
        return (f"Task {self.current_task_retry}/{self.max_task_retries}, "
                f"Round {self.current_round}/{self.max_rounds}, "
                f"TokenReduction {self.current_token_reduction}/{self.max_token_reductions}, "
                f"FormatFixes {self.current_format_fixes}/{self.max_format_fixes}, "
                f"Compressed: {self.is_compressed}")