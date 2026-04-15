#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class FakeNewsAPITester:
    def __init__(self, base_url="https://fakehunter-neo4j.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:300]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        if success:
            if "neo4j" in response and response.get("status") == "healthy":
                print("   ✅ Neo4j connection confirmed")
                return True
            else:
                print("   ⚠️  Health check passed but Neo4j status unclear")
        return success

    def test_seed_database(self):
        """Test database seeding"""
        success, response = self.run_test(
            "Seed Database",
            "POST",
            "seed",
            200,
            timeout=60  # Seeding might take longer
        )
        if success and "count" in response:
            count = response.get("count", 0)
            print(f"   ✅ Seeded {count} articles")
            return count > 0
        return success

    def test_analyze_fake_article(self):
        """Test analyzing a fake news article"""
        fake_article = {
            "text": "BREAKING: Secret government documents EXPOSED showing they've been hiding alien technology since 1947! The mainstream media doesn't want you to know about the advanced energy devices recovered from crash sites. Share before this gets deleted!",
            "source": "truthrevealed.net",
            "author": "patriot investigator"
        }
        
        success, response = self.run_test(
            "Analyze Fake Article",
            "POST",
            "analyze",
            200,
            data=fake_article,
            timeout=45
        )
        
        if success:
            fake_score = response.get("fake_score", 0)
            verdict = response.get("verdict", "")
            print(f"   📊 Fake Score: {fake_score}")
            print(f"   📋 Verdict: {verdict}")
            
            # Validate response structure
            required_fields = ["id", "fake_score", "verdict", "explanation", "entities", "graph_data", "timestamp"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
            
            # Check if fake score is appropriately high for fake news
            if fake_score > 50:
                print("   ✅ High fake score detected correctly")
                return True
            else:
                print(f"   ⚠️  Expected higher fake score for obvious fake news, got {fake_score}")
                return False
        return success

    def test_analyze_trustworthy_article(self):
        """Test analyzing a trustworthy article"""
        trustworthy_article = {
            "text": "The Federal Reserve announced today that it will maintain current interest rates at 5.25%, citing stable employment numbers and controlled inflation at 2.1%. Chair Jerome Powell said the committee will continue monitoring economic indicators before making any changes. Markets responded calmly with modest gains across major indices.",
            "source": "reuters",
            "author": "jane martinez"
        }
        
        success, response = self.run_test(
            "Analyze Trustworthy Article",
            "POST",
            "analyze",
            200,
            data=trustworthy_article,
            timeout=45
        )
        
        if success:
            fake_score = response.get("fake_score", 100)
            verdict = response.get("verdict", "")
            print(f"   📊 Fake Score: {fake_score}")
            print(f"   📋 Verdict: {verdict}")
            
            # Check if fake score is appropriately low for trustworthy news
            if fake_score < 50:
                print("   ✅ Low fake score detected correctly")
                return True
            else:
                print(f"   ⚠️  Expected lower fake score for trustworthy news, got {fake_score}")
                return False
        return success

    def test_get_graph_data(self):
        """Test getting graph visualization data"""
        success, response = self.run_test(
            "Get Graph Data",
            "GET",
            "graph",
            200
        )
        
        if success:
            nodes = response.get("nodes", [])
            links = response.get("links", [])
            print(f"   📊 Nodes: {len(nodes)}, Links: {len(links)}")
            
            if len(nodes) > 0 and len(links) > 0:
                print("   ✅ Graph data contains nodes and links")
                return True
            else:
                print("   ⚠️  Graph data is empty")
                return False
        return success

    def test_get_stats(self):
        """Test getting statistics"""
        success, response = self.run_test(
            "Get Statistics",
            "GET",
            "stats",
            200
        )
        
        if success:
            node_counts = response.get("node_counts", {})
            verdict_dist = response.get("verdict_distribution", {})
            suspicious_sources = response.get("suspicious_sources", [])
            
            print(f"   📊 Node counts: {node_counts}")
            print(f"   📊 Verdict distribution: {verdict_dist}")
            print(f"   📊 Suspicious sources: {len(suspicious_sources)}")
            
            required_fields = ["node_counts", "verdict_distribution", "suspicious_sources", "total_relationships"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
            
            print("   ✅ All required stats fields present")
            return True
        return success

    def test_get_history(self):
        """Test getting analysis history"""
        success, response = self.run_test(
            "Get Analysis History",
            "GET",
            "history",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   📊 History records: {len(response)}")
                if len(response) > 0:
                    # Check first record structure
                    first_record = response[0]
                    required_fields = ["id", "text_preview", "fake_score", "verdict", "source", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in first_record]
                    if missing_fields:
                        print(f"   ⚠️  Missing fields in history record: {missing_fields}")
                        return False
                print("   ✅ History data structure is correct")
                return True
            else:
                print("   ⚠️  History response is not a list")
                return False
        return success

    def test_invalid_analyze_request(self):
        """Test error handling for invalid analyze request"""
        invalid_article = {
            "text": "short",  # Too short
            "source": "test",
            "author": "test"
        }
        
        success, response = self.run_test(
            "Invalid Analyze Request (too short)",
            "POST",
            "analyze",
            400,  # Expecting 400 Bad Request
            data=invalid_article
        )
        
        if success:
            print("   ✅ Properly rejected short article")
            return True
        return success

def main():
    print("🚀 Starting Fake News Detection API Tests")
    print("=" * 60)
    
    tester = FakeNewsAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Seed Database", tester.test_seed_database),
        ("Analyze Fake Article", tester.test_analyze_fake_article),
        ("Analyze Trustworthy Article", tester.test_analyze_trustworthy_article),
        ("Get Graph Data", tester.test_get_graph_data),
        ("Get Statistics", tester.test_get_stats),
        ("Get History", tester.test_get_history),
        ("Invalid Request Handling", tester.test_invalid_analyze_request),
    ]
    
    passed_tests = []
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed_tests.append(test_name)
            else:
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            failed_tests.append(test_name)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / max(tester.tests_run, 1)) * 100:.1f}%")
    
    if passed_tests:
        print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
        for test in passed_tests:
            print(f"   • {test}")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"   • {test}")
    
    if tester.failed_tests:
        print(f"\n🔍 FAILURE DETAILS:")
        for failure in tester.failed_tests:
            print(f"   • {failure}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())