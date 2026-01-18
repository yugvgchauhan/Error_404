"""Analyze skill gaps between user and market requirements."""
from typing import Dict, List, Tuple


class GapAnalyzer:
    """Compare user skills against market requirements."""
    
    def analyze_gaps(
        self,
        user_skills: Dict[str, Dict],  # {skill: {proficiency, confidence}}
        market_requirements: Dict[str, Dict]  # {skill: {frequency, requirement_level, avg_proficiency_needed}}
    ) -> Dict:

        critical_gaps = []
        important_gaps = []
        emerging_gaps = []
        strengths = []
        
        for skill, market_data in market_requirements.items():
            user_prof = user_skills.get(skill, {}).get('proficiency', 0.0)
            market_need = market_data['avg_proficiency_needed']
            gap_size = market_need - user_prof
            
            gap_info = {
                'skill': skill,
                'user_proficiency': round(user_prof, 2),
                'market_requirement': round(market_need, 2),
                'gap': round(gap_size, 2),
                'market_frequency': market_data['frequency'],
                'requirement_level': market_data['requirement_level']
            }
            
            # Categorize gaps
            if gap_size > 0.5 and market_data['requirement_level'] == 'critical':
                gap_info['priority'] = 'CRITICAL'
                gap_info['impact'] = f"Blocking {int(market_data['frequency']*100)}% of jobs"
                critical_gaps.append(gap_info)
            
            elif gap_size > 0.3 and market_data['requirement_level'] in ['critical', 'important']:
                gap_info['priority'] = 'IMPORTANT'
                gap_info['impact'] = f"Reduces competitiveness in {int(market_data['frequency']*100)}% of jobs"
                important_gaps.append(gap_info)
            
            elif market_data['requirement_level'] == 'emerging' and gap_size > 0:
                gap_info['priority'] = 'EMERGING'
                gap_info['impact'] = f"Future-proofing skill (appearing in {int(market_data['frequency']*100)}% of jobs)"
                emerging_gaps.append(gap_info)
            
            elif gap_size <= 0:
                gap_info['priority'] = 'STRENGTH'
                gap_info['advantage'] = f"Exceeds market requirement by {abs(gap_size):.2f}"
                strengths.append(gap_info)
        
        # Sort by gap size
        critical_gaps.sort(key=lambda x: x['gap'], reverse=True)
        important_gaps.sort(key=lambda x: x['gap'], reverse=True)
        emerging_gaps.sort(key=lambda x: x['gap'], reverse=True)
        
        # Calculate overall readiness
        readiness = self._calculate_readiness(user_skills, market_requirements)
        
        # Generate summary
        summary = {
            'total_gaps': len(critical_gaps) + len(important_gaps) + len(emerging_gaps),
            'critical_gap_count': len(critical_gaps),
            'important_gap_count': len(important_gaps),
            'emerging_gap_count': len(emerging_gaps),
            'strength_count': len(strengths),
            'overall_readiness_pct': readiness,
            'interpretation': self._interpret_readiness(readiness),
            'top_3_priorities': [g['skill'] for g in critical_gaps[:3]]
        }
        
        return {
            'critical_gaps': critical_gaps,
            'important_gaps': important_gaps,
            'emerging_gaps': emerging_gaps,
            'strengths': strengths,
            'overall_readiness': readiness,
            'summary': summary
        }
    
    def _calculate_readiness(
        self,
        user_skills: Dict[str, Dict],
        market_requirements: Dict[str, Dict]
    ) -> float:
        """Calculate overall job readiness percentage."""
        if not market_requirements:
            return 0.0
        
        total_weight = 0
        achieved_weight = 0
        
        for skill, market_data in market_requirements.items():
            # Weight by frequency and criticality
            weight = market_data['frequency']
            
            if market_data['requirement_level'] == 'critical':
                weight *= 2.0
            elif market_data['requirement_level'] == 'important':
                weight *= 1.5
            elif market_data['requirement_level'] == 'emerging':
                weight *= 1.2
            
            total_weight += weight
            
            user_prof = user_skills.get(skill, {}).get('proficiency', 0.0)
            market_need = market_data['avg_proficiency_needed']
            
            # Achievement ratio (capped at 1.0)
            achievement = min(user_prof / market_need, 1.0) if market_need > 0 else 1.0
            
            achieved_weight += weight * achievement
        
        readiness = (achieved_weight / total_weight) * 100 if total_weight > 0 else 0
        
        return round(readiness, 1)
    
    def _interpret_readiness(self, readiness: float) -> str:
        """Provide interpretation of readiness score."""
        if readiness >= 90:
            return "Excellent - Ready to apply immediately!"
        elif readiness >= 75:
            return "Good - Strong candidate with minor gaps"
        elif readiness >= 60:
            return "Fair - Nearly ready, 1-2 key gaps to address"
        elif readiness >= 45:
            return "Developing - Several important skills needed (3-4 months)"
        else:
            return "Early stage - Significant skill development needed (6+ months)"
    
    def get_missing_skills(
        self,
        user_skills: Dict[str, Dict],
        market_requirements: Dict[str, Dict],
        min_frequency: float = 0.3
    ) -> List[str]:
        """
        Get list of skills user completely lacks that appear frequently in jobs.
        
        Args:
            min_frequency: Minimum frequency in market (0-1) to include skill
        
        Returns:
            List of skill names
        """
        missing = []
        
        for skill, market_data in market_requirements.items():
            if market_data['frequency'] >= min_frequency:
                if skill not in user_skills or user_skills[skill]['proficiency'] < 0.1:
                    missing.append(skill)
        
        return missing