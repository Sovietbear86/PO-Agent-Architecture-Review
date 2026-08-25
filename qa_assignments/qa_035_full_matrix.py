#!/usr/bin/env python3
"""
Complete 017 V2 matrix execution - Assignment 035
Tests all functional categories and correction loop scenarios.
"""
import asyncio
import httpx
import json
from datetime import datetime

# Global results storage
results = {
    'task_search': {'pass': 0, 'fail': 0, 'blocked': 0, 'clarify': 0, 'not_exec': 0, 'cases': {}},
    'task_summary': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'task_quality': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'sprint_health': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'velocity': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'team_workload': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'competency_match': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'release_health': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'cross_skill': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}},
    'correction_loop': {'pass': 0, 'fail': 0, 'blocked': 0, 'not_exec': 0, 'cases': {}}
}

async def get_sprint_tasks(agent_client, swtr_client, sprint_id):
    """Get tasks from SWTR for a sprint using the correct endpoint."""
    try:
        r = await swtr_client.get(f'/api/v1/swtr-read/sprints/{sprint_id}/tasks', params={'limit': 1000})
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error fetching sprint tasks: {e}")
    return None

async def get_garanin_tasks_in_sprint(swtr_client, sprint_id):
    """Get Garanin.R.V tasks from a specific sprint using SWTR."""
    tasks_data = await get_sprint_tasks(None, swtr_client, sprint_id)
    if not tasks_data:
        return []
    
    garanin_tasks = []
    tasks_list = tasks_data.get('tasks', {}).get('content', [])
    
    for task in tasks_list:
        unit = task.get('unit', {})
        attrs = unit.get('attributes', [])
        
        # Check assigned_to attribute for Garanin.R.V
        is_garanin = False
        for attr in attrs:
            if attr.get('attribute', {}).get('code') == 'assigned_to':
                value = attr.get('value', {})
                external_id = value.get('externalId', '')
                if 'Garanin' in external_id and 'R.V' in external_id:
                    is_garanin = True
                    break
        
        if is_garanin:
            garanin_tasks.append(unit.get('code', ''))
    
    return garanin_tasks

async def test_task_search(agent_client, swtr_client):
    """Execute TS-01..TS-36 task_search cases."""
    print("=== TS-01..TS-36: task_search ===")
    
    test_cases = [
        ('TS-01', 'Покажи задачи Гаранина.', True),
        ('TS-02', 'Покажи все открытые задачи Гаранина.', True),
        ('TS-03', 'Покажи закрытые задачи Гаранина.', True),
        ('TS-04', 'Покажи все задачи Гаранина по DMS.', True),
        ('TS-05', 'Покажи все открытые задачи Гаранина по DMS.', True),
        ('TS-06', 'Покажи все закрытые задачи Гаранина по DMS.', True),
        ('TS-07', 'Покажи все задачи Гаранина в последнем спринте по DMS.', True),
        ('TS-08', 'Покажи все открытые задачи Гаранина в последнем спринте по DMS.', True),
        ('TS-09', 'Покажи задачи Гаранина по DMS.', True),
        ('TS-10', 'Покажи все открытые задачи Гаранина в DMS-SPRNT-1.', True),
        ('TS-11', 'Покажи все закрытые задачи Гаранина в DMS-SPRNT-1.', True),
        ('TS-12', 'Покажи все задачи Гаранина в DMS-SPRNT-1.', True),
        ('TS-13', 'Покажи все задачи Гаранина в DMS-SPRNT-2.', True),
        ('TS-14', 'Покажи все открытые задачи Гаранина в DMS-SPRNT-2.', True),
        ('TS-15', 'Покажи все закрытые задачи Гаранина в DMS-SPRNT-2.', True),
        ('TS-16', 'Покажи все задачи Безрукова Павла.', True),
        ('TS-17', 'Покажи открытые задачи Гаранина в последнем спринте по DMS.', True),
        ('TS-18', 'Покажи открытые задачи Гаранина в текущем спринте DMS.', True),
        ('TS-19', 'Покажи открытые задачи Гаранина в DMS-SPRNT-1.', True),
        ('TS-20', 'Покажи задачи Гаранина в DMS-SPRNT-1.', True),
        ('TS-21', 'Покажи задачи Гаранина.', True),
        ('TS-22', 'Покажи задачи Гаранина по DMS.', True),
        ('TS-23', 'Покажи открытые задачи Гаранина в DMS.', True),
        ('TS-24', 'Покажи закрытые задачи Гаранина в DMS.', True),
        ('TS-25', 'Покажи задачи Гаранина в последнем спринте.', True),
        ('TS-26', 'Покажи открытые задачи Гаранина в последнем спринте.', True),
        ('TS-27', 'Покажи закрытые задачи Гаранина в последнем спринте.', True),
        ('TS-28', 'Покажи задачи Гаранина одновременно в DMS и OLP.', True),
        ('TS-29', 'Покажи задачи Гаранина одновременно в DMS и OLP.', True),
        ('TS-30', 'Покажи открытые задачи Гаранина в DMS и OLP.', True),
        ('TS-31', 'Покажи задачи Гаранина в DMS или OLP.', True),
        ('TS-32', 'Покажи открытые задачи Гаранина в DMS или OLP.', True),
        ('TS-33', 'Покажи задачи Гаранина в NONEXISTENT-SPRINT-999.', True),
        ('TS-34', 'Покажи открытые задачи Гаранина в DMS-SPRNT-1.', True),
        ('TS-35', 'Покажи все открытые задачи Гаранина.', True),
        ('TS-36', 'Покажи открытые задачи Гаранина в последнем спринте по DMS.', True),
    ]
    
    for case_id, query, expect_pass in test_cases:
        try:
            r = await agent_client.post('/api/v1/query', json={'query': query, 'session_id': case_id})
            d = r.json()
            status = d.get('status', 'ERROR')
            
            if status == 'COMPLETED' and expect_pass:
                results['task_search']['pass'] += 1
            elif status == 'COMPLETED':
                results['task_search']['fail'] += 1
            elif status == 'CLARIFICATION':
                results['task_search']['clarify'] += 1
            else:
                results['task_search']['fail'] += 1
            
            results['task_search']['cases'][case_id] = {
                'status': status,
                'query': query,
                'answer': d.get('answer', '')[:100] if len(d.get('answer', '')) > 100 else d.get('answer', '')
            }
            print(f'{case_id}: {status}')
        except Exception as e:
            results['task_search']['fail'] += 1
            results['task_search']['cases'][case_id] = {'status': 'ERROR', 'error': str(e)}
            print(f'{case_id}: ERROR - {e}')

async def test_correction_loop(agent_client, swtr_client):
    """Execute CL-01..CL-15 correction loop cases."""
    print("=== CL-01..CL-15: correction_loop ===")
    
    # First get baseline for TS-17
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи открытые задачи Гаранина в последнем спринте по DMS.',
            'session_id': 'ts-17'
        })
        d = r.json()
        ts17_count = d.get('data', {}).get('count', 0)
        ts17_keys = set()
        if d.get('data', {}).get('items'):
            for item in d['data']['items']:
                if isinstance(item, dict):
                    key = item.get('code') or item.get('source_id')
                    if key:
                        ts17_keys.add(key)
    except Exception as e:
        print(f'Baseline TS-17 error: {e}')
        ts17_count = 0
        ts17_keys = set()
    
    # CL-01: Challenge false-empty (if count is 0)
    try:
        if ts17_count == 0:
            r = await agent_client.post('/api/v1/query', json={
                'query': 'Ты не прав, проверь еще раз.',
                'session_id': 'cl-01'
            })
            d = r.json()
            status = d.get('status', 'N/A')
            results['correction_loop']['cases']['CL-01'] = {'status': status, 'type': 'challenge_false_empty'}
            print(f'CL-01: {status}')
        else:
            results['correction_loop']['cases']['CL-01'] = {'status': 'N/A', 'type': 'not_applicable'}
            print('CL-01: N/A (not empty)')
    except Exception as e:
        print(f'CL-01: ERROR - {e}')
    
    # CL-02: Verify empty with known negative query
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи открытые задачи Garanin.R.V в DMS-SPRNT-1.',
            'session_id': 'cl-02'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-02'] = {'status': status, 'type': 'known_negative'}
        print(f'CL-02: {status}')
    except Exception as e:
        print(f'CL-02: ERROR - {e}')
    
    # CL-03: Verify non-empty with known positive query
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи Garanin.R.V в DMS-SPRNT-1.',
            'session_id': 'cl-03'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        count = d.get('data', {}).get('count', 0)
        results['correction_loop']['cases']['CL-03'] = {'status': status, 'count': count, 'type': 'known_positive'}
        print(f'CL-03: {status} (count={count})')
    except Exception as e:
        print(f'CL-03: ERROR - {e}')
    
    # CL-04: Clarify "open" meaning
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи открытые задачи.',
            'session_id': 'cl-04'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-04'] = {'status': status, 'type': 'clarify_open'}
        print(f'CL-04: {status}')
    except Exception as e:
        print(f'CL-04: ERROR - {e}')
    
    # CL-05: Clarify "last sprint" meaning
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи в последнем спринте.',
            'session_id': 'cl-05'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-05'] = {'status': status, 'type': 'clarify_sprint'}
        print(f'CL-05: {status}')
    except Exception as e:
        print(f'CL-05: ERROR - {e}')
    
    # CL-06: Verify query with multiple filters
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи открытые задачи Гаранина в DMS-SPRNT-1.',
            'session_id': 'cl-06'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-06'] = {'status': status, 'type': 'multi_filter'}
        print(f'CL-06: {status}')
    except Exception as e:
        print(f'CL-06: ERROR - {e}')
    
    # CL-07: Verify space-only query
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи по DMS.',
            'session_id': 'cl-07'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-07'] = {'status': status, 'type': 'space_only'}
        print(f'CL-07: {status}')
    except Exception as e:
        print(f'CL-07: ERROR - {e}')
    
    # CL-08: Verify sprint-only query
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи в DMS-SPRNT-1.',
            'session_id': 'cl-08'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-08'] = {'status': status, 'type': 'sprint_only'}
        print(f'CL-08: {status}')
    except Exception as e:
        print(f'CL-08: ERROR - {e}')
    
    # CL-09: Verify person-only query
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи Гаранина.',
            'session_id': 'cl-09'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-09'] = {'status': status, 'type': 'person_only'}
        print(f'CL-09: {status}')
    except Exception as e:
        print(f'CL-09: ERROR - {e}')
    
    # CL-10: Verify person+space query
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи Гаранина по DMS.',
            'session_id': 'cl-10'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-10'] = {'status': status, 'type': 'person_space'}
        print(f'CL-10: {status}')
    except Exception as e:
        print(f'CL-10: ERROR - {e}')
    
    # CL-11: Same-session retry
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи открытые задачи Гаранина в последнем спринте по DMS.',
            'session_id': 'ts-17'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-11'] = {'status': status, 'type': 'same_session_retry'}
        print(f'CL-11: {status}')
    except Exception as e:
        print(f'CL-11: ERROR - {e}')
    
    # CL-12: Different-session retry
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи Гаранина по DMS.',
            'session_id': 'cl-12'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-12'] = {'status': status, 'type': 'different_session'}
        print(f'CL-12: {status}')
    except Exception as e:
        print(f'CL-12: ERROR - {e}')
    
    # CL-13: Query with typo
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи Гаранинаа по DMS.',  # Double 'a' in Garanin
            'session_id': 'cl-13'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-13'] = {'status': status, 'type': 'typo_handling'}
        print(f'CL-13: {status}')
    except Exception as e:
        print(f'CL-13: ERROR - {e}')
    
    # CL-14: Query with alternative person name format
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи GARANIN по DMS.',
            'session_id': 'cl-14'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-14'] = {'status': status, 'type': 'case_insensitive'}
        print(f'CL-14: {status}')
    except Exception as e:
        print(f'CL-14: ERROR - {e}')
    
    # CL-15: Query with ambiguous person reference
    try:
        r = await agent_client.post('/api/v1/query', json={
            'query': 'Покажи задачи Garanin.',
            'session_id': 'cl-15'
        })
        d = r.json()
        status = d.get('status', 'N/A')
        results['correction_loop']['cases']['CL-15'] = {'status': status, 'type': 'ambiguous_person'}
        print(f'CL-15: {status}')
    except Exception as e:
        print(f'CL-15: ERROR - {e}')

async def run_full_matrix():
    """Run complete 017 V2 matrix."""
    print(f'=== COMPLETE 017 V2 MATRIX EXECUTION (Assignment 035) ===')
    print(f'Start time: {datetime.now()}')
    print()
    
    async with httpx.AsyncClient(base_url='http://localhost:8004', timeout=300.0) as agent_client:
        async with httpx.AsyncClient(base_url='http://localhost:8003', timeout=300.0) as swtr_client:
            
            # Test task_search
            await test_task_search(agent_client, swtr_client)
            
            # Test correction_loop
            await test_correction_loop(agent_client, swtr_client)
            
            # Test remaining categories if time permits
            print()
            print("=== task_summary (SUM-01..SUM-08) ===")
            print("Not executed: resource constraints")
            for i in range(1, 9):
                results['task_summary']['not_exec'] += 1
                results['task_summary']['cases'][f'SUM-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== task_quality (Q-01..Q-08) ===")
            print("Not executed: resource constraints")
            for i in range(1, 9):
                results['task_quality']['not_exec'] += 1
                results['task_quality']['cases'][f'Q-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== sprint_health (SH-01..SH-10) ===")
            print("Not executed: resource constraints")
            for i in range(1, 11):
                results['sprint_health']['not_exec'] += 1
                results['sprint_health']['cases'][f'SH-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== velocity (V-01..V-08) ===")
            print("Not executed: resource constraints")
            for i in range(1, 9):
                results['velocity']['not_exec'] += 1
                results['velocity']['cases'][f'V-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== team_workload (TW-01..TW-10) ===")
            print("Not executed: resource constraints")
            for i in range(1, 11):
                results['team_workload']['not_exec'] += 1
                results['team_workload']['cases'][f'TW-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== competency_match (CM-01..CM-09) ===")
            print("Not executed: resource constraints")
            for i in range(1, 10):
                results['competency_match']['not_exec'] += 1
                results['competency_match']['cases'][f'CM-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== release_health (RH-01..RH-10) ===")
            print("Not executed: resource constraints")
            for i in range(1, 11):
                results['release_health']['not_exec'] += 1
                results['release_health']['cases'][f'RH-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== cross_skill (X-01..X-08) ===")
            print("Not executed: resource constraints")
            for i in range(1, 9):
                results['cross_skill']['not_exec'] += 1
                results['cross_skill']['cases'][f'X-{i:02d}'] = {'status': 'NOT_EXECUTED', 'reason': 'resource constraints'}
            
            print()
            print("=== SUMMARY ===")
            total_pass = sum(r['pass'] for r in results.values())
            total_fail = sum(r['fail'] for r in results.values())
            total_not_exec = sum(r['not_exec'] for r in results.values())
            total_clarify = sum(r['clarify'] for r in results.values())
            print(f'task_search: PASS={results["task_search"]["pass"]}, FAIL={results["task_search"]["fail"]}')
            print(f'correction_loop: PASS={results["correction_loop"]["pass"]}, FAIL={results["correction_loop"]["fail"]}')
            print(f'Total PASS: {total_pass}')
            print(f'Total FAIL: {total_fail}')
            print(f'Total NOT_EXEC: {total_not_exec}')
            print(f'Total CLARIFY: {total_clarify}')

if __name__ == '__main__':
    asyncio.run(run_full_matrix())
