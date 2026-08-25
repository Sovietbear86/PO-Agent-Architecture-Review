#!/usr/bin/env python3
"""QA 026 Test Runner v7 - Fixed client management"""

import asyncio
import json
import time

from qa_026_test_runner_v2 import QA026TestRunner

async def run_all_sections():
    print('=' * 70)
    print('QA 026 v2 - Full Run (v7)')
    print('=' * 70)
    
    runner = QA026TestRunner()
    
    # Initialize results
    runner.results = {
        "timestamp": "test",
        "head": "test",
        "section_a": {},
        "section_b": {},
        "section_c": {},
        "section_d": {},
        "section_e": {},
        "section_f": {},
        "section_g": {},
        "section_h": {},
        "section_i": {},
        "section_j": {},
        "summary": {}
    }
    
    start_time = time.perf_counter()
    
    async with runner.client as client:
        # Run each section
        await runner._run_section_a()
        print(f'[1/10] Section A: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_b()
        print(f'[2/10] Section B: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_c()
        print(f'[3/10] Section C: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_d()
        print(f'[4/10] Section D: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_e()
        print(f'[5/10] Section E: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_f()
        print(f'[6/10] Section F: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_g()
        print(f'[7/10] Section G: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_h()
        print(f'[8/10] Section H: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_i()
        print(f'[9/10] Section I: {int((time.perf_counter() - start_time) * 1000)}ms')
        
        await runner._run_section_j()
        print(f'[10/10] Section J: {int((time.perf_counter() - start_time) * 1000)}ms')
    
    # Generate summary
    runner._generate_summary()
    
    elapsed = int((time.perf_counter() - start_time) * 1000)
    print(f'\nFull run completed in {elapsed}ms ({elapsed/60:.1f} min)')
    
    # Summary
    summary = runner.results.get('summary', {})
    metrics = summary.get('summary_metrics', {})
    
    print(f'\n=== SUMMARY ===')
    print(f'  total_passes: {metrics.get("total_passes", 0)}')
    print(f'  total_fails: {metrics.get("total_fails", 0)}')
    print(f'  total_blocked: {metrics.get("total_blocked", 0)}')
    print(f'  total_not_executed: {metrics.get("total_not_executed", 0)}')
    print(f'  total_tests: {metrics.get("total_tests", 0)}')
    print(f'  accounting_valid: {metrics.get("accounting_valid", False)}')
    
    # Save results
    with open('qa_reports/CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026_RESULTS_V8.json', 'w') as f:
        json.dump(runner.results, f, indent=2, ensure_ascii=False)
    print('\nResults saved to qa_reports/CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026_RESULTS_V8.json')

if __name__ == "__main__":
    asyncio.run(run_all_sections())
