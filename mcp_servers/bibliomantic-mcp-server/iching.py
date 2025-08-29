"""
I Ching Hexagram Database and Interpretation Logic

This module contains a simplified representation of the I Ching's 64 hexagrams
with concise interpretations suitable for integration with Claude responses.
Each hexagram includes its traditional number, name, and interpretive wisdom.
"""

from typing import Dict, Tuple, List
import secrets


class IChing:
    """
    I Ching hexagram database and interpretation system.
    
    Implements the traditional 64 hexagram system with simplified interpretations
    optimized for bibliomantic integration with AI responses.
    """
    
    def __init__(self):
        """Initialize the I Ching database with all 64 hexagrams."""
        self.hexagrams = self._build_hexagram_database()
    
    def _build_hexagram_database(self) -> Dict[int, Dict[str, str]]:
        """
        Build the complete 64-hexagram database.
        
        Returns:
            Dictionary mapping hexagram numbers to their attributes
        """
        return {
            1: {
                "name": "The Creative",
                "binary": "111111",
                "interpretation": "Pure creative force emerges. Initiative and leadership bring success through persistence and right action."
            },
            2: {
                "name": "The Receptive", 
                "binary": "000000",
                "interpretation": "Gentle receptivity and yielding strength. Success comes through supporting others and following the natural flow."
            },
            3: {
                "name": "Difficulty at the Beginning",
                "binary": "010001",
                "interpretation": "Initial struggles give way to breakthrough. Perseverance through early challenges leads to eventual success."
            },
            4: {
                "name": "Youthful Folly",
                "binary": "100010",
                "interpretation": "Learning through inexperience. Humble acceptance of guidance and willingness to learn bring wisdom."
            },
            5: {
                "name": "Waiting",
                "binary": "010111",
                "interpretation": "Patient anticipation of the right moment. Timing is crucial; premature action leads to failure."
            },
            6: {
                "name": "Conflict",
                "binary": "111010",
                "interpretation": "Inner tension requires resolution. Seek compromise and understanding rather than confrontation."
            },
            7: {
                "name": "The Army",
                "binary": "000010",
                "interpretation": "Disciplined organization achieves goals. Leadership with clear purpose unites diverse elements."
            },
            8: {
                "name": "Holding Together",
                "binary": "010000",
                "interpretation": "Unity through mutual support. Relationships flourish when built on trust and shared values."
            },
            9: {
                "name": "Small Accumulation",
                "binary": "110111",
                "interpretation": "Gentle influence creates change. Small, consistent efforts accumulate into significant transformation."
            },
            10: {
                "name": "Treading",
                "binary": "111011",
                "interpretation": "Careful conduct in delicate situations. Respectful behavior toward authority ensures safe passage."
            },
            11: {
                "name": "Peace",
                "binary": "000111",
                "interpretation": "Harmony between heaven and earth. Balance between opposing forces creates lasting prosperity."
            },
            12: {
                "name": "Standstill",
                "binary": "111000",
                "interpretation": "Temporary withdrawal preserves strength. Wait for better conditions rather than forcing progress."
            },
            13: {
                "name": "Fellowship",
                "binary": "111101",
                "interpretation": "Unity with like-minded people. Shared purpose and mutual understanding create powerful alliances."
            },
            14: {
                "name": "Great Possession",
                "binary": "101111",
                "interpretation": "Abundance through wisdom and virtue. Great resources carry great responsibility for others' welfare."
            },
            15: {
                "name": "Modesty",
                "binary": "000100",
                "interpretation": "Humble excellence attracts support. True greatness manifests through unpretentious service."
            },
            16: {
                "name": "Enthusiasm",
                "binary": "001000",
                "interpretation": "Inspiring leadership motivates others. Genuine enthusiasm creates momentum for positive change."
            },
            17: {
                "name": "Following",
                "binary": "011001",
                "interpretation": "Adaptability to changing circumstances. Success comes through flexible response to new conditions."
            },
            18: {
                "name": "Work on the Decayed",
                "binary": "100110",
                "interpretation": "Correcting past mistakes brings renewal. Patient restoration of what has deteriorated yields results."
            },
            19: {
                "name": "Approach",
                "binary": "000011",
                "interpretation": "Gradual progress through gentle persistence. Step-by-step advancement builds solid foundations."
            },
            20: {
                "name": "Contemplation",
                "binary": "110000",
                "interpretation": "Reflective observation reveals truth. Understanding comes through careful consideration of patterns."
            },
            21: {
                "name": "Biting Through",
                "binary": "101001",
                "interpretation": "Decisive action overcomes obstacles. Clear judgment followed by firm resolve breaks through barriers."
            },
            22: {
                "name": "Grace",
                "binary": "100101",
                "interpretation": "Beauty enhances substance. Elegant presentation of worthy content attracts positive attention."
            },
            23: {
                "name": "Splitting Apart",
                "binary": "100000",
                "interpretation": "Deterioration requires patient endurance. Protect what matters most while weathering difficult times."
            },
            24: {
                "name": "Return",
                "binary": "000001",
                "interpretation": "Renewal begins from within. Small positive changes initiate cycles of growth and regeneration."
            },
            25: {
                "name": "Innocence",
                "binary": "111001",
                "interpretation": "Natural spontaneity brings good fortune. Authentic action aligned with inner truth succeeds."
            },
            26: {
                "name": "Great Accumulation",
                "binary": "100111",
                "interpretation": "Stored wisdom becomes power. Accumulated knowledge and experience create opportunities for greatness."
            },
            27: {
                "name": "Nourishment",
                "binary": "100001",
                "interpretation": "Careful attention to what feeds growth. Discriminating selection of influences shapes character."
            },
            28: {
                "name": "Great Excess",
                "binary": "011110",
                "interpretation": "Extraordinary times require extraordinary measures. Bold action in crisis situations can transform everything."
            },
            29: {
                "name": "The Abysmal Water",
                "binary": "010010",
                "interpretation": "Danger requires flowing adaptation. Like water, find the path of least resistance through difficulties."
            },
            30: {
                "name": "The Clinging Fire",
                "binary": "101101",
                "interpretation": "Illuminating clarity dispels confusion. Conscious awareness and clear perception guide right action."
            },
            31: {
                "name": "Influence",
                "binary": "011100",
                "interpretation": "Mutual attraction creates connection. Gentle influence and receptive response build lasting relationships."
            },
            32: {
                "name": "Duration",
                "binary": "001110",
                "interpretation": "Enduring stability through consistent principles. Long-term success requires unwavering commitment to values."
            },
            33: {
                "name": "Retreat",
                "binary": "111100",
                "interpretation": "Strategic withdrawal preserves strength. Knowing when to step back prevents unnecessary losses."
            },
            34: {
                "name": "Great Power",
                "binary": "001111",
                "interpretation": "Strength tempered by wisdom. True power lies in restraint and the measured application of force."
            },
            35: {
                "name": "Progress",
                "binary": "101000",
                "interpretation": "Advancing toward enlightenment. Steady forward movement brings recognition and expanded influence."
            },
            36: {
                "name": "Darkening of the Light",
                "binary": "000101",
                "interpretation": "Inner light persists despite outer darkness. Maintain integrity and wisdom during challenging times."
            },
            37: {
                "name": "The Family",
                "binary": "110101",
                "interpretation": "Harmonious relationships create security. Strong foundations at home support success in the world."
            },
            38: {
                "name": "Opposition",
                "binary": "101011",
                "interpretation": "Differences can become complementary. Understanding opposing viewpoints reveals new possibilities."
            },
            39: {
                "name": "Obstruction",
                "binary": "010100",
                "interpretation": "Obstacles offer opportunities for growth. Patience and persistence eventually overcome all barriers."
            },
            40: {
                "name": "Deliverance",
                "binary": "001010",
                "interpretation": "Liberation from restriction brings relief. Quick action after breakthrough prevents return to difficulty."
            },
            41: {
                "name": "Decrease",
                "binary": "100011",
                "interpretation": "Voluntary simplification increases essentials. Reducing excess reveals what truly matters."
            },
            42: {
                "name": "Increase",
                "binary": "110001",
                "interpretation": "Generous sharing multiplies abundance. Helping others succeed creates mutual prosperity."
            },
            43: {
                "name": "Breakthrough",
                "binary": "011111",
                "interpretation": "Determined resolve overcomes final resistance. Clear decision and bold action achieve breakthrough."
            },
            44: {
                "name": "Coming to Meet",
                "binary": "111110",
                "interpretation": "Unexpected encounters bring opportunity. Remain alert to recognise important meetings and messages."
            },
            45: {
                "name": "Gathering Together",
                "binary": "011000",
                "interpretation": "Collective effort amplifies individual power. Unity of purpose creates strength greater than the sum of parts."
            },
            46: {
                "name": "Pushing Upward",
                "binary": "000110",
                "interpretation": "Gradual ascent through persistent effort. Step-by-step advancement builds sustainable success."
            },
            47: {
                "name": "Oppression",
                "binary": "011010",
                "interpretation": "Constraint tests inner strength. Maintaining dignity and purpose during restriction builds character."
            },
            48: {
                "name": "The Well",
                "binary": "010110",
                "interpretation": "Inexhaustible source of wisdom and nourishment. Deep resources serve many when properly accessed."
            },
            49: {
                "name": "Revolution",
                "binary": "011101",
                "interpretation": "Necessary change transforms outdated systems. Revolution succeeds when timing and methods align properly."
            },
            50: {
                "name": "The Cauldron",
                "binary": "101110",
                "interpretation": "Transformation through refinement. Combining diverse elements creates something greater than their sum."
            },
            51: {
                "name": "Thunder",
                "binary": "001001",
                "interpretation": "Shocking awakening brings clarity. Sudden revelations shatter illusions and reveal truth."
            },
            52: {
                "name": "Mountain",
                "binary": "100100",
                "interpretation": "Stillness cultivates inner strength. Meditation and quiet reflection restore balance and wisdom."
            },
            53: {
                "name": "Gradual Development",
                "binary": "110100",
                "interpretation": "Patient progress ensures lasting results. Slow, steady advancement builds unshakeable foundations."
            },
            54: {
                "name": "The Marrying Maiden",
                "binary": "001011",
                "interpretation": "Subordinate position requires careful conduct. Success comes through understanding one's proper role."
            },
            55: {
                "name": "Abundance",
                "binary": "001101",
                "interpretation": "Peak achievement through integrated effort. Maximum potential realized when all elements work in harmony."
            },
            56: {
                "name": "The Wanderer",
                "binary": "101100",
                "interpretation": "Journey brings experience and wisdom. Adaptability and open-mindedness ensure safe passage through foreign territories."
            },
            57: {
                "name": "The Gentle Wind",
                "binary": "110110",
                "interpretation": "Persistent gentle influence creates lasting change. Subtle consistency succeeds where force fails."
            },
            58: {
                "name": "The Joyous Lake",
                "binary": "011011",
                "interpretation": "Cheerful confidence attracts support. Joy shared with others multiplies and returns in abundance."
            },
            59: {
                "name": "Dispersion",
                "binary": "110010",
                "interpretation": "Breaking down barriers enables reunion. Dissolving rigid boundaries allows natural flow to resume."
            },
            60: {
                "name": "Limitation",
                "binary": "010011",
                "interpretation": "Voluntary boundaries create freedom. Self-imposed discipline prevents external limitation."
            },
            61: {
                "name": "Inner Truth",
                "binary": "110011",
                "interpretation": "Sincere understanding creates connection. Authentic communication bridges differences and builds trust."
            },
            62: {
                "name": "Small Excess",
                "binary": "001100",
                "interpretation": "Careful attention to details ensures success. Small, thorough efforts prevent large problems."
            },
            63: {
                "name": "After Completion",
                "binary": "010101",
                "interpretation": "Success achieved requires continued vigilance. Maintaining accomplishments demands ongoing attention."
            },
            64: {
                "name": "Before Completion",
                "binary": "101010",
                "interpretation": "Final push needed to reach the goal. Careful completion of last steps ensures lasting success."
            }
        }
    
    def generate_hexagram_by_coins(self) -> Tuple[int, str, str]:
        """
        Generate a hexagram using the traditional three-coin method.
        
        Simulates throwing three coins six times to generate six lines,
        building a hexagram from bottom to top as in traditional practice.
        
        Returns:
            Tuple containing (hexagram_number, name, interpretation)
        """
        lines = []
        
        # Generate six lines (bottom to top)
        for _ in range(6):
            # Throw three coins: heads = 3, tails = 2
            coin_sum = sum(3 if secrets.randbelow(2) else 2 for _ in range(3))
            
            # 6 or 9 are changing lines, but for simplicity we use stable lines
            # 6 (three tails) = yin line = 0
            # 9 (three heads) = yang line = 1
            # 7 (two tails, one head) = yang line = 1  
            # 8 (two heads, one tail) = yin line = 0
            if coin_sum in [6, 8]:  # Yin line
                lines.append('0')
            else:  # coin_sum in [7, 9] - Yang line
                lines.append('1')
        
        # Convert binary to hexagram number (1-64)
        binary_string = ''.join(reversed(lines))  # Traditional order: bottom to top
        hexagram_number = self._binary_to_hexagram_number(binary_string)
        
        hexagram_data = self.hexagrams[hexagram_number]
        return hexagram_number, hexagram_data["name"], hexagram_data["interpretation"]
    
    def _binary_to_hexagram_number(self, binary_string: str) -> int:
        """
        Convert binary representation to traditional hexagram number.
        
        Args:
            binary_string: 6-character binary string representing the hexagram
            
        Returns:
            Hexagram number (1-64)
        """
        # Find hexagram by matching binary pattern
        for number, data in self.hexagrams.items():
            if data["binary"] == binary_string:
                return number
        
        # Fallback: convert binary to decimal and map to 1-64 range
        decimal_value = int(binary_string, 2)
        return (decimal_value % 64) + 1
    
    def get_hexagram_by_number(self, number: int) -> Tuple[str, str]:
        """
        Retrieve hexagram by its traditional number.
        
        Args:
            number: Hexagram number (1-64)
            
        Returns:
            Tuple containing (name, interpretation)
        """
        if number in self.hexagrams:
            data = self.hexagrams[number]
            return data["name"], data["interpretation"]
        else:
            return "Unknown", "The path is unclear; seek within for guidance."
    
    def format_divination_text(self, number: int, name: str, interpretation: str) -> str:
        """
        Format hexagram information for integration with queries.
        
        Args:
            number: Hexagram number
            name: Hexagram name
            interpretation: Hexagram interpretation
            
        Returns:
            Formatted string suitable for Claude integration
        """
        return f"I Ching Hexagram {number} - {name}: {interpretation}"


# Module-level convenience function
def divine_hexagram() -> Tuple[int, str, str]:
    """
    Convenience function to generate a random hexagram.
    
    Returns:
        Tuple containing (hexagram_number, name, interpretation)
    """
    iching = IChing()
    return iching.generate_hexagram_by_coins()


if __name__ == "__main__":
    # Demonstration of the I Ching system
    print("I Ching Bibliomantic Divination Demo")
    print("=" * 40)
    
    iching = IChing()
    
    for i in range(3):
        number, name, interpretation = iching.generate_hexagram_by_coins()
        formatted = iching.format_divination_text(number, name, interpretation)
        print(f"\nDivination {i+1}:")
        print(formatted)
