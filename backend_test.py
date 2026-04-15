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

    def test_analyze_fake_article_with_content_analysis(self):
        """Test analyzing fake article with combined graph + content scoring"""
        fake_article = {
            "text": "BREAKING: Secret government documents EXPOSED showing they've been hiding alien technology since 1947! The mainstream media doesn't want you to know about the advanced energy devices recovered from crash sites. This cure all solution works instantly and is 100% guaranteed! The government hiding this truth from us! Share before this gets deleted!",
            "source": "truthrevealed.net",
            "author": "patriot investigator"
        }
        
        success, response = self.run_test(
            "Analyze Fake Article (Combined Graph + Content Scoring)",
            "POST",
            "analyze",
            200,
            data=fake_article,
            timeout=45
        )
        
        if success:
            score = response.get("score", 0)
            label = response.get("label", "")
            reason = response.get("reason", "")
            breakdown = response.get("breakdown", {})
            explanation = response.get("explanation", [])
            
            print(f"   📊 Final Score: {score}")
            print(f"   📋 Label: {label}")
            print(f"   📝 Reason: {reason[:150]}...")
            
            # Validate NEW combined scoring breakdown structure
            required_breakdown = [
                "graph_score", "content_score", "source_count", "author_count", "topic_frequency",
                "sensational_keywords", "sensational_score", "unrealistic_claims", "unrealistic_score",
                "conspiracy_phrases", "conspiracy_score", "formula", "graph_formula", "content_formula",
                "raw_score", "capped_score"
            ]
            missing_breakdown = [field for field in required_breakdown if field not in breakdown]
            if missing_breakdown:
                print(f"   ❌ Missing breakdown fields: {missing_breakdown}")
                return False
            
            # Test combined formula calculation: final = graph + content
            graph_score = breakdown.get("graph_score", 0)
            content_score = breakdown.get("content_score", 0)
            expected_combined = graph_score + content_score
            actual_raw = breakdown.get("raw_score", 0)
            
            print(f"   🧮 Combined Formula: graph({graph_score}) + content({content_score}) = {expected_combined}")
            print(f"   🧮 Actual raw score: {actual_raw}")
            
            if abs(expected_combined - actual_raw) > 0.1:
                print(f"   ❌ Combined formula mismatch: expected {expected_combined}, got {actual_raw}")
                return False
            
            # Test content analysis detection
            sensational_keywords = breakdown.get("sensational_keywords", [])
            unrealistic_claims = breakdown.get("unrealistic_claims", [])
            conspiracy_phrases = breakdown.get("conspiracy_phrases", [])
            
            print(f"   🔍 Sensational keywords found: {sensational_keywords}")
            print(f"   🔍 Unrealistic claims found: {unrealistic_claims}")
            print(f"   🔍 Conspiracy phrases found: {conspiracy_phrases}")
            
            # Should detect sensational keywords: "breaking", "secret", "instantly"
            expected_sensational = ["breaking", "secret", "instantly"]
            found_sensational = [kw for kw in expected_sensational if kw in sensational_keywords]
            if len(found_sensational) < 2:
                print(f"   ❌ Expected to find sensational keywords {expected_sensational}, found {sensational_keywords}")
                return False
            
            # Should detect unrealistic claims: "cure all", "100% guaranteed", "instant results"
            expected_unrealistic = ["cure all", "100% guaranteed"]
            found_unrealistic = [claim for claim in expected_unrealistic if claim in unrealistic_claims]
            if len(found_unrealistic) < 1:
                print(f"   ❌ Expected to find unrealistic claims {expected_unrealistic}, found {unrealistic_claims}")
                return False
            
            # Should detect conspiracy phrases: "government hiding"
            expected_conspiracy = ["government hiding"]
            found_conspiracy = [phrase for phrase in expected_conspiracy if phrase in conspiracy_phrases]
            if len(found_conspiracy) < 1:
                print(f"   ❌ Expected to find conspiracy phrases {expected_conspiracy}, found {conspiracy_phrases}")
                return False
            
            # Test explanation format with [Graph] and [Content] tags
            graph_explanations = [exp for exp in explanation if exp.startswith("[Graph]")]
            content_explanations = [exp for exp in explanation if exp.startswith("[Content]")]
            
            print(f"   📝 Graph explanations: {len(graph_explanations)}")
            print(f"   📝 Content explanations: {len(content_explanations)}")
            
            if len(content_explanations) == 0:
                print(f"   ❌ Expected [Content] tagged explanations, found none")
                return False
            
            # Check if score is appropriate (should be high due to content analysis)
            if score >= 70:  # Should be Likely Fake
                if label == "Likely Fake":
                    print(f"   ✅ Correct label '{label}' for high score {score}")
                    return True
                else:
                    print(f"   ❌ Wrong label '{label}' for high score {score}")
                    return False
            elif score >= 30:  # Should be Suspicious
                if label == "Suspicious":
                    print(f"   ✅ Correct label '{label}' for score {score}")
                    return True
                else:
                    print(f"   ❌ Wrong label '{label}' for score {score}")
                    return False
            else:
                print(f"   ❌ Expected score >= 30 for fake article with sensational content, got {score}")
                return False
        return success

    def test_analyze_trustworthy_article_with_content_analysis(self):
        """Test analyzing trustworthy article with combined graph + content scoring"""
        trustworthy_article = {
            "text": "The Federal Reserve announced today that it will maintain current interest rates at 5.25%, citing stable employment numbers and controlled inflation at 2.1%. Chair Jerome Powell said the committee will continue monitoring economic indicators before making any changes. Markets responded calmly with modest gains across major indices.",
            "source": "reuters",
            "author": "jane martinez"
        }
        
        success, response = self.run_test(
            "Analyze Trustworthy Article (Combined Graph + Content Scoring)",
            "POST",
            "analyze",
            200,
            data=trustworthy_article,
            timeout=45
        )
        
        if success:
            score = response.get("score", 100)
            label = response.get("label", "")
            reason = response.get("reason", "")
            breakdown = response.get("breakdown", {})
            explanation = response.get("explanation", [])
            
            print(f"   📊 Final Score: {score}")
            print(f"   📋 Label: {label}")
            print(f"   📝 Reason: {reason[:150]}...")
            
            # Test combined scoring breakdown structure
            required_breakdown = [
                "graph_score", "content_score", "source_count", "author_count", "topic_frequency",
                "sensational_keywords", "sensational_score", "unrealistic_claims", "unrealistic_score",
                "conspiracy_phrases", "conspiracy_score", "formula", "graph_formula", "content_formula",
                "raw_score", "capped_score"
            ]
            missing_breakdown = [field for field in required_breakdown if field not in breakdown]
            if missing_breakdown:
                print(f"   ❌ Missing breakdown fields: {missing_breakdown}")
                return False
            
            # Test combined formula calculation: final = graph + content
            graph_score = breakdown.get("graph_score", 0)
            content_score = breakdown.get("content_score", 0)
            expected_combined = graph_score + content_score
            actual_raw = breakdown.get("raw_score", 0)
            
            print(f"   🧮 Combined Formula: graph({graph_score}) + content({content_score}) = {expected_combined}")
            print(f"   🧮 Actual raw score: {actual_raw}")
            
            if abs(expected_combined - actual_raw) > 0.1:
                print(f"   ❌ Combined formula mismatch: expected {expected_combined}, got {actual_raw}")
                return False
            
            # Test content analysis - should find NO problematic content
            sensational_keywords = breakdown.get("sensational_keywords", [])
            unrealistic_claims = breakdown.get("unrealistic_claims", [])
            conspiracy_phrases = breakdown.get("conspiracy_phrases", [])
            
            print(f"   🔍 Sensational keywords found: {sensational_keywords}")
            print(f"   🔍 Unrealistic claims found: {unrealistic_claims}")
            print(f"   🔍 Conspiracy phrases found: {conspiracy_phrases}")
            
            # Should find NO problematic content in trustworthy article
            if len(sensational_keywords) > 0 or len(unrealistic_claims) > 0 or len(conspiracy_phrases) > 0:
                print(f"   ❌ Found problematic content in trustworthy article")
                return False
            
            # Content score should be 0
            if content_score != 0:
                print(f"   ❌ Expected content_score = 0 for clean article, got {content_score}")
                return False
            
            # Test explanation format with [Graph] and [Content] tags
            graph_explanations = [exp for exp in explanation if exp.startswith("[Graph]")]
            content_explanations = [exp for exp in explanation if exp.startswith("[Content]")]
            
            print(f"   📝 Graph explanations: {len(graph_explanations)}")
            print(f"   📝 Content explanations: {len(content_explanations)}")
            
            # Should have at least one content explanation saying no problematic content found
            if len(content_explanations) == 0:
                print(f"   ❌ Expected [Content] tagged explanations, found none")
                return False
            
            # Check if score is appropriate for trustworthy source (should be low)
            if score < 30:  # Should be Likely True
                if label == "Likely True":
                    print(f"   ✅ Correct label '{label}' for low score {score}")
                    return True
                else:
                    print(f"   ❌ Wrong label '{label}' for low score {score}")
                    return False
            else:
                print(f"   ⚠️  Expected score < 30 for trustworthy source, got {score}")
                return score < 30
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

    def test_content_only_analysis(self):
        """Test analyzing unknown source with sensational content only"""
        content_only_article = {
            "text": "SHOCKING discovery reveals instant results with this miracle cure! Scientists don't want you to know about this secret breakthrough that works instantly and is 100% guaranteed to cure all diseases! The government hiding this from the public!",
            "source": "unknown",
            "author": "unknown"
        }
        
        success, response = self.run_test(
            "Content-Only Analysis (Unknown Source + Sensational Text)",
            "POST",
            "analyze",
            200,
            data=content_only_article,
            timeout=45
        )
        
        if success:
            score = response.get("score", 0)
            label = response.get("label", "")
            breakdown = response.get("breakdown", {})
            
            print(f"   📊 Final Score: {score}")
            print(f"   📋 Label: {label}")
            
            # Test that graph score is 0 (unknown source/author)
            graph_score = breakdown.get("graph_score", 0)
            content_score = breakdown.get("content_score", 0)
            
            print(f"   🧮 Graph Score: {graph_score} (should be 0 for unknown source)")
            print(f"   🧮 Content Score: {content_score} (should be > 0)")
            
            if graph_score != 0:
                print(f"   ❌ Expected graph_score = 0 for unknown source, got {graph_score}")
                return False
            
            if content_score <= 0:
                print(f"   ❌ Expected content_score > 0 for sensational text, got {content_score}")
                return False
            
            # Should detect multiple content issues
            sensational_keywords = breakdown.get("sensational_keywords", [])
            unrealistic_claims = breakdown.get("unrealistic_claims", [])
            conspiracy_phrases = breakdown.get("conspiracy_phrases", [])
            
            print(f"   🔍 Sensational: {sensational_keywords}")
            print(f"   🔍 Unrealistic: {unrealistic_claims}")
            print(f"   🔍 Conspiracy: {conspiracy_phrases}")
            
            # Should find sensational keywords: "shocking", "secret", "instantly"
            expected_sensational = ["shocking", "secret", "instantly"]
            found_sensational = [kw for kw in expected_sensational if kw in sensational_keywords]
            if len(found_sensational) < 2:
                print(f"   ❌ Expected sensational keywords, found {sensational_keywords}")
                return False
            
            # Should find unrealistic claims: "instant results", "100% guaranteed", "cure all"
            expected_unrealistic = ["instant results", "100% guaranteed", "cure all"]
            found_unrealistic = [claim for claim in expected_unrealistic if claim in unrealistic_claims]
            if len(found_unrealistic) < 2:
                print(f"   ❌ Expected unrealistic claims, found {unrealistic_claims}")
                return False
            
            # Should find conspiracy phrases: "government hiding"
            if "government hiding" not in conspiracy_phrases:
                print(f"   ❌ Expected 'government hiding' in conspiracy phrases, found {conspiracy_phrases}")
                return False
            
            # Final score should be content_score only
            if score != content_score:
                print(f"   ❌ Expected final score = content_score ({content_score}), got {score}")
                return False
            
            print(f"   ✅ Content-only analysis working correctly")
            return True
        return success

    def test_score_formula_verification(self):
        """Test score formula math verification: final = graph_score + content_score, capped at 100"""
        high_score_article = {
            "text": "BREAKING: Secret government documents EXPOSED! They don't want you to know about this shocking cure all that works instantly and is 100% guaranteed! The government hiding this miracle cure from us! This instant results formula is being suppressed by mainstream media lies!",
            "source": "truthrevealed.net",  # Known fake source
            "author": "patriot investigator"  # Known fake author
        }
        
        success, response = self.run_test(
            "Score Formula Math Verification",
            "POST",
            "analyze",
            200,
            data=high_score_article,
            timeout=45
        )
        
        if success:
            score = response.get("score", 0)
            breakdown = response.get("breakdown", {})
            
            graph_score = breakdown.get("graph_score", 0)
            content_score = breakdown.get("content_score", 0)
            raw_score = breakdown.get("raw_score", 0)
            capped_score = breakdown.get("capped_score", 0)
            
            print(f"   🧮 Graph Score: {graph_score}")
            print(f"   🧮 Content Score: {content_score}")
            print(f"   🧮 Raw Score: {raw_score}")
            print(f"   🧮 Capped Score: {capped_score}")
            print(f"   🧮 Final Score: {score}")
            
            # Test formula: final = graph + content
            expected_raw = graph_score + content_score
            if abs(raw_score - expected_raw) > 0.1:
                print(f"   ❌ Raw score calculation error: expected {expected_raw}, got {raw_score}")
                return False
            
            # Test capping at 100
            expected_capped = min(raw_score, 100)
            if abs(capped_score - expected_capped) > 0.1:
                print(f"   ❌ Capping error: expected {expected_capped}, got {capped_score}")
                return False
            
            # Final score should equal capped score
            if abs(score - capped_score) > 0.1:
                print(f"   ❌ Final score mismatch: expected {capped_score}, got {score}")
                return False
            
            # Test that we get high content score due to multiple triggers
            if content_score < 50:  # Should be high due to multiple sensational/unrealistic/conspiracy content
                print(f"   ❌ Expected high content score for loaded article, got {content_score}")
                return False
            
            print(f"   ✅ Score formula math verification passed")
            return True
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
    print("🚀 Starting Fake News Detection API Tests")
    print("=" * 60)
    
    tester = FakeNewsAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Seed Database", tester.test_seed_database),
        ("Analyze Fake Article (Combined Scoring)", tester.test_analyze_fake_article_with_content_analysis),
        ("Analyze Trustworthy Article (Combined Scoring)", tester.test_analyze_trustworthy_article_with_content_analysis),
        ("Content-Only Analysis", tester.test_content_only_analysis),
        ("Score Formula Math Verification", tester.test_score_formula_verification),
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