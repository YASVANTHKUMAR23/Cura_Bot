import logging
from typing import Dict, List
import time

from orchestrator import orchestrator
from database.supabase_client import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoScenarios:
    """
    Pre-built demo scenarios for quick testing
    """
    
    SCENARIOS = {
        'heart_attack_critical': {
            'name': 'Heart Attack - Critical Emergency',
            'description': 'Patient with severe heart attack symptoms',
            'patient_phone': '+91-9876543210',
            'messages': [
                'I have severe chest pain',
                'It is crushing pain in the center, spreading to my left arm. I am sweating heavily',
                'Yes, it started suddenly about 30 minutes ago'
            ],
            'expected': {
                'disease': 'Heart Attack',
                'severity': 'CRITICAL',
                'agent3_triggered': True,
                'emergency': True
            }
        },
        
        'dengue_moderate': {
            'name': 'Dengue - Moderate Severity',
            'description': 'Patient with dengue symptoms',
            'patient_phone': '+91-9876543211',
            'messages': [
                'I have high fever for 3 days now',
                'Yes, I have severe headache behind my eyes and red rash on my arms',
                'I traveled to a village last week'
            ],
            'expected': {
                'disease': 'Dengue',
                'severity': 'MODERATE',
                'agent3_triggered': True
            }
        },
        
        'red_flag_emergency': {
            'name': 'Red Flag - Immediate Emergency',
            'description': 'Patient mentions red flag keyword',
            'patient_phone': '+91-9876543214',
            'messages': [
                'I cannot breathe properly',
            ],
            'expected': {
                'emergency_triggered': True,
                'agent': 'emergency',
                'call_108': True
            }
        }
    }
    
    def __init__(self):
        self.orchestrator = orchestrator
        self.results = []
    
    def run_scenario(self, scenario_key: str, delay: float = 2.0) -> Dict:
        """
        Run a single scenario
        
        Args:
            scenario_key: Key from SCENARIOS dict
            delay: Delay between messages (seconds)
        
        Returns:
            Dict with results
        """
        
        if scenario_key not in self.SCENARIOS:
            raise ValueError(f'Scenario {scenario_key} not found')
        
        scenario = self.SCENARIOS[scenario_key]
        
        logger.info(f'\n{"="*60}')
        logger.info(f'DEMO: {scenario["name"]}')
        logger.info(f'{"="*60}')
        logger.info(f'Description: {scenario["description"]}')
        logger.info(f'Patient: {scenario["patient_phone"]}')
        logger.info(f'Messages: {len(scenario["messages"])}\n')
        
        results = []
        session_id = None
        
        for i, message in enumerate(scenario['messages'], 1):
            logger.info(f'\n[Message {i}/{len(scenario["messages"])}]')
            logger.info(f'USER: {message}')
            
            response = self.orchestrator.process_message(
                patient_phone=scenario['patient_phone'],
                message=message,
                session_id=session_id
            )
            
            if not session_id:
                session_id = response['session_id']
            
            logger.info(f'BOT ({response["agent"]}): {response["response"]}')
            
            if response.get('severity'):
                logger.info(f'Severity: {response["severity"]}')
            
            if response.get('disease'):
                logger.info(f'Disease: {response["disease"]} ({response.get("confidence", 0):.0%})')
            
            if response.get('emergency'):
                logger.info(f'EMERGENCY MODE ACTIVATED')
            
            if response.get('appointment_created'):
                logger.info(f'Appointment: {response["appointment_id"]}')
            
            results.append(response)
            
            if i < len(scenario['messages']):
                time.sleep(delay)
        
        logger.info(f'\n{"="*60}')
        logger.info('VALIDATION')
        logger.info(f'{"="*60}')
        
        validation = self._validate_results(results, scenario['expected'])
        
        for check, status in validation.items():
            icon = '✅' if status else '❌'
            logger.info(f'{icon} {check}: {status}')
        
        return {
            'scenario': scenario_key,
            'results': results,
            'validation': validation,
            'passed': all(validation.values())
        }
    
    def _validate_results(self, results: List[Dict], expected: Dict) -> Dict:
        """Validate scenario results"""
        
        validation = {}
        
        if 'disease' in expected:
            detected_disease = None
            for r in results:
                if r.get('disease'):
                    detected_disease = r['disease']
                    break
            
            validation['Disease detected'] = detected_disease == expected['disease']
        
        if 'severity' in expected:
            final_severity = None
            for r in results:
                if r.get('severity'):
                    final_severity = r['severity']
            
            validation['Severity correct'] = final_severity == expected['severity']
        
        if 'agent3_triggered' in expected:
            agent3_used = any(r.get('agent') == 'agent3' for r in results)
            validation['Agent 3 triggered'] = agent3_used == expected['agent3_triggered']
        
        if 'emergency' in expected:
            emergency_triggered = any(r.get('emergency') for r in results)
            validation['Emergency mode'] = emergency_triggered == expected['emergency']
        
        if 'emergency_triggered' in expected:
            emergency_agent = any(r.get('agent') == 'emergency' for r in results)
            validation['Red flag detected'] = emergency_agent
        
        return validation
    
    def run_all_scenarios(self):
        """Run all demo scenarios"""
        
        logger.info(f'\n{"#"*60}')
        logger.info('CURABOT DEMO - ALL SCENARIOS')
        logger.info(f'{"#"*60}\n')
        
        for scenario_key in self.SCENARIOS.keys():
            result = self.run_scenario(scenario_key, delay=1.0)
            self.results.append(result)
            
            time.sleep(2)
        
        logger.info(f'\n{"#"*60}')
        logger.info('DEMO SUMMARY')
        logger.info(f'{"#"*60}\n')
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        logger.info(f'Total scenarios: {total}')
        logger.info(f'Passed: {passed}')
        logger.info(f'Failed: {total - passed}')
        logger.info(f'Success rate: {passed/total*100:.1f}%\n')
        
        for result in self.results:
            icon = '✅' if result['passed'] else '❌'
            logger.info(f'{icon} {result["scenario"]}')


def main():
    """Main demo runner"""
    
    demo = DemoScenarios()
    
    # Run single scenario
    demo.run_scenario('heart_attack_critical')
    
    # Or run all
    # demo.run_all_scenarios()


if __name__ == '__main__':
    main()

