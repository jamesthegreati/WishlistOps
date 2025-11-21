"""
Content quality filter to prevent AI-generated slop.

This filter detects and flags generic AI language, corporate buzzwords,
and other quality issues in generated content.

Architecture: See 05_WishlistOps_Revised_Architecture.md Fix #5
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

from .models import VoiceConfig


logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Result of content filtering."""
    passed: bool
    issues: list[str]
    score: float  # 0.0 (terrible) to 1.0 (perfect)


class ContentFilter:
    """
    Filter AI-generated content for quality issues.
    
    Detects:
    - AI slop buzzwords
    - Corporate marketing speak
    - Off-brand language
    - Length issues
    - Repetition problems
    
    Attributes:
        voice_config: Voice configuration with avoid_phrases
        slop_words: Built-in list of AI buzzwords
    """
    
    # Built-in AI slop detector patterns
    SLOP_WORDS = [
        # Classic AI buzzwords
        r'\bdelve\b', r'\btapestry\b', r'\bleverage\b', r'\bsynergy\b',
        r'\brobust\b', r'\bholistic\b', r'\bseamless\b',
        
        # Marketing buzzwords
        r'\bcutting[- ]edge\b', r'\brevolutionary\b', r'\bgame[- ]changing\b',
        r'\bindustry[- ]leading\b', r'\bworld[- ]class\b',
        
        # Corporate speak
        r'\belevate\b', r'\btransform\b', r'\bunlock\b.*\bpotential\b',
        r'\btake.*\bto the next level\b', r'\bpivot\b',
        
        # Generic phrases
        r'\bat the end of the day\b', r'\bthink outside the box\b',
        r'\bwin[- ]win\b', r'\blow[- ]hanging fruit\b',
        
        # Over-used AI transitions
        r'\bthat said\b', r'\bmeanwhile\b', r'\bnevertheless\b',
        r'\bhowever, it\'s important to note\b',
        
        # Overly formal
        r'\butilize\b', r'\bfacilitate\b', r'\bimplement\b',
        r'\boptimize\b.*\bexperience\b',
        
        # AI safety additions
        r'\bas an AI\b', r'\bI cannot\b', r'\bI apologize\b',
    ]
    
    # Suspicious phrase patterns (marketing speak)
    MARKETING_PATTERNS = [
        r'\bimmersive experience\b',
        r'\bunparalleled.*experience\b',
        r'\bnext[- ]generation\b',
        r'\binnovative solution\b',
        r'\bgroundbreaking\b',
        r'\bbest[- ]in[- ]class\b',
    ]
    
    # Good indie dev phrases (increase score)
    POSITIVE_PATTERNS = [
        r'\bwe fixed\b', r'\bwe added\b', r'\bwe improved\b',
        r'\bbug fix\b', r'\bnew feature\b', r'\bupdate\b',
        r'\bthanks for\b', r'\byour feedback\b',
    ]
    
    def __init__(self, voice_config: Optional[VoiceConfig] = None) -> None:
        """
        Initialize content filter.
        
        Args:
            voice_config: Voice configuration with custom avoid phrases
        """
        self.voice_config = voice_config or VoiceConfig()
        
        # Combine built-in and user-defined avoid phrases
        self.avoid_phrases = [
            phrase.lower() 
            for phrase in self.voice_config.avoid_phrases
        ]
        
        logger.info("Content filter initialized", extra={
            "custom_avoid_phrases": len(self.avoid_phrases)
        })
    
    def check(self, text: str) -> FilterResult:
        """
        Check text for quality issues.
        
        Args:
            text: Text to check (announcement body)
            
        Returns:
            FilterResult with pass/fail and detected issues
        """
        issues = []
        score = 1.0  # Start with perfect score
        
        text_lower = text.lower()
        
        # Check 1: AI slop words
        for pattern in self.SLOP_WORDS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                issues.append(f"AI slop detected: '{matches[0]}'")
                score -= 0.15
        
        # Check 2: Marketing patterns
        for pattern in self.MARKETING_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append(f"Marketing speak detected: pattern '{pattern}'")
                score -= 0.10
        
        # Check 3: User-defined avoid phrases
        for phrase in self.avoid_phrases:
            if phrase in text_lower:
                issues.append(f"Avoided phrase found: '{phrase}'")
                score -= 0.10
        
        # Check 4: Length validation
        word_count = len(text.split())
        if word_count < 50:
            issues.append(f"Too short: {word_count} words (min 50)")
            score -= 0.20
        elif word_count > 500:
            issues.append(f"Too long: {word_count} words (max 500)")
            score -= 0.10
        
        # Check 5: Repetition detection
        repetition_issues = self._check_repetition(text)
        issues.extend(repetition_issues)
        score -= len(repetition_issues) * 0.05
        
        # Check 6: Overly formal tone
        if self._is_too_formal(text):
            issues.append("Tone too formal (sounds like corporate announcement)")
            score -= 0.15
        
        # Bonus: Good indie dev language
        for pattern in self.POSITIVE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 0.05
        
        # Clamp score to 0-1 range
        score = max(0.0, min(1.0, score))
        
        # Pass threshold: 0.6
        passed = score >= 0.6 and len(issues) == 0
        
        if not passed:
            logger.warning("Content failed quality filter", extra={
                "score": f"{score:.2f}",
                "issues_count": len(issues),
                "issues": issues[:3]  # Log first 3 issues
            })
        else:
            logger.info("Content passed quality filter", extra={
                "score": f"{score:.2f}"
            })
        
        return FilterResult(
            passed=passed,
            issues=issues,
            score=score
        )
    
    def _check_repetition(self, text: str) -> list[str]:
        """
        Check for repeated words or phrases.
        
        Args:
            text: Text to check
            
        Returns:
            List of repetition issues found
        """
        issues = []
        words = text.lower().split()
        
        # Check for repeated words (same word 3+ times)
        word_counts = {}
        for word in words:
            if len(word) > 4:  # Only check meaningful words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        for word, count in word_counts.items():
            if count >= 4:  # Word appears 4+ times
                issues.append(f"Word '{word}' repeated {count} times")
        
        # Common phrases to ignore (too common to flag)
        ignore_phrases = {
            'in the', 'to the', 'of the', 'on the', 'at the',
            'we are', 'we have', 'this is', 'that is', 'it is',
            'and the', 'for the', 'with the', 'from the'
        }
        
        # Positive phrases (good to use, don't flag even if repeated)
        positive_phrases = {
            'we fixed', 'we added', 'we improved', 'we updated',
            'bug fix', 'new feature', 'thanks for'
        }
        
        # Check for repeated phrases (2-3 word phrases)
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+2])
            # Skip common phrases and positive phrases
            if phrase in ignore_phrases or phrase in positive_phrases:
                continue
            rest_of_text = ' '.join(words[i+2:])
            if phrase in rest_of_text:
                issues.append(f"Phrase '{phrase}' repeated")
                break  # Only report first repetition
        
        return issues
    
    def _is_too_formal(self, text: str) -> bool:
        """
        Check if tone is too formal/corporate.
        
        Args:
            text: Text to check
            
        Returns:
            True if too formal
        """
        formal_indicators = [
            r'\bpursuant to\b', r'\btherefore\b', r'\bfurthermore\b',
            r'\bsubsequently\b', r'\bhenceforth\b', r'\bwherein\b',
            r'\bis pleased to announce\b', r'\bare excited to introduce\b',
        ]
        
        text_lower = text.lower()
        formal_count = sum(
            1 for pattern in formal_indicators 
            if re.search(pattern, text_lower)
        )
        
        # If 2+ formal indicators, consider it too formal
        return formal_count >= 2
    
    def suggest_improvements(self, text: str, issues: list[str]) -> str:
        """
        Generate suggestions for improving flagged content.
        
        Args:
            text: Original text
            issues: Issues detected by filter
            
        Returns:
            String with improvement suggestions
        """
        suggestions = []
        
        if any("AI slop" in issue for issue in issues):
            suggestions.append(
                "Replace buzzwords with specific, concrete language. "
                "Example: Instead of 'robust system', say 'bug-free combat'."
            )
        
        if any("Marketing speak" in issue for issue in issues):
            suggestions.append(
                "Remove marketing jargon. Write like you're talking to a friend "
                "about your game, not pitching to investors."
            )
        
        if any("Too short" in issue for issue in issues):
            suggestions.append(
                "Add more details about the changes. What exactly is new? "
                "How does it improve gameplay?"
            )
        
        if any("repeated" in issue for issue in issues):
            suggestions.append(
                "Use more varied vocabulary. Find synonyms or rephrase "
                "to avoid repetition."
            )
        
        if any("too formal" in issue for issue in issues):
            suggestions.append(
                "Use casual, conversational tone. Write 'we fixed' not "
                "'we are pleased to announce the resolution of'."
            )
        
        return "\n".join(f"- {s}" for s in suggestions)
    
    def generate_regeneration_prompt(self, original_text: str, issues: list[str]) -> str:
        """
        Generate prompt for AI to regenerate content avoiding issues.
        
        Args:
            original_text: Original generated text
            issues: Issues that were detected
            
        Returns:
            Prompt for regeneration
        """
        forbidden_words = [
            issue.split("'")[1] 
            for issue in issues 
            if "'" in issue
        ]
        
        prompt = (
            f"Rewrite this announcement to fix these issues:\n"
            f"{chr(10).join(f'- {issue}' for issue in issues)}\n\n"
            f"Original text:\n{original_text}\n\n"
            f"Requirements:\n"
            f"- Do NOT use these words: {', '.join(forbidden_words)}\n"
            f"- Write in casual, authentic indie dev voice\n"
            f"- Be specific and concrete, not vague\n"
            f"- Sound like a human, not a corporate announcement\n"
            f"- Keep it between 50-300 words\n"
        )
        
        return prompt


# Convenience function
def check_content(text: str, voice_config: Optional[VoiceConfig] = None) -> FilterResult:
    """Quick content check (convenience function)."""
    filter = ContentFilter(voice_config)
    return filter.check(text)
