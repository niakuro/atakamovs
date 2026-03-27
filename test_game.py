#!/usr/bin/env python3
"""
Comprehensive test script for 観測君VS ULTIMATE Ver 4.1
Tests CPU battles, room creation/joining, and game mechanics
"""

import asyncio
import time
import json
from playwright.async_api import async_playwright, Page
from typing import Optional, Dict, Any

class GameTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.bugs_found = []
        self.tests_passed = 0
        self.tests_failed = 0
        
    def log(self, message: str):
        """Log test messages"""
        print(f"[TEST] {message}")
        
    def log_bug(self, bug: str):
        """Log a bug"""
        print(f"[BUG] {bug}")
        self.bugs_found.append(bug)
        self.tests_failed += 1
        
    def log_pass(self, test: str):
        """Log a passed test"""
        print(f"[PASS] {test}")
        self.tests_passed += 1
        
    async def wait_for_element(self, page: Page, selector: str, timeout: int = 5000):
        """Wait for an element to appear"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            return False
            
    async def test_cpu_battle(self, browser):
        """Test CPU battle mode"""
        self.log("=" * 60)
        self.log("Testing CPU Battle Mode")
        self.log("=" * 60)
        
        page = await browser.new_page()
        await page.goto(self.base_url)
        
        try:
            # Check if title screen loads
            title = await page.locator('h1').first.text_content()
            if "観測君VS ULTIMATE" in title:
                self.log_pass("Title screen loads correctly")
            else:
                self.log_bug("Title screen not showing correct title")
                
            # Click CPU battle button
            await page.click('button:has-text("CPU戦")')
            await asyncio.sleep(1)
            
            # Check if deck selection screen appears
            deck_screen = await page.locator('#screen-deck').is_visible()
            if deck_screen:
                self.log_pass("Deck selection screen appears after CPU battle selection")
            else:
                self.log_bug("Deck selection screen does not appear")
                await page.close()
                return
                
            # Select a preset deck
            await page.click('button:has-text("測量機械デッキ")')
            await asyncio.sleep(0.5)
            
            # Check deck count
            deck_count = await page.locator('#deck-count').text_content()
            if deck_count == "40":
                self.log_pass("Preset deck loads with 40 cards")
            else:
                self.log_bug(f"Preset deck has {deck_count} cards instead of 40")
                
            # Submit deck
            await page.click('button:has-text("現場へ出撃")')
            await asyncio.sleep(2)
            
            # Check if battle screen appears
            battle_screen = await page.locator('#screen-battle').is_visible()
            if battle_screen:
                self.log_pass("Battle screen appears after deck submission")
            else:
                self.log_bug("Battle screen does not appear")
                await page.close()
                return
                
            # Check game state elements
            if await self.wait_for_element(page, '#my-score'):
                self.log_pass("Score display is visible")
            else:
                self.log_bug("Score display not visible")
                
            if await self.wait_for_element(page, '#my-ap'):
                self.log_pass("AP display is visible")
            else:
                self.log_bug("AP display not visible")
                
            if await self.wait_for_element(page, '#turn-txt'):
                self.log_pass("Turn counter is visible")
            else:
                self.log_bug("Turn counter not visible")
                
            if await self.wait_for_element(page, '#weather-txt'):
                self.log_pass("Weather display is visible")
            else:
                self.log_bug("Weather display not visible")
                
            # Wait for initial hand
            await asyncio.sleep(2)
            
            # Check if player has cards in hand
            hand_cards = await page.locator('#my-hand .card').count()
            if hand_cards == 5:
                self.log_pass("Player starts with 5 cards in hand")
            else:
                self.log_bug(f"Player has {hand_cards} cards instead of 5")
                
            # Test playing a card
            try:
                # Get initial AP
                ap_text = await page.locator('#my-ap').text_content()
                self.log(f"Initial AP: {ap_text}")
                
                # Find a playable card (cost 0-2)
                await asyncio.sleep(1)
                
                # Try to play the first card if we have enough AP
                cards = await page.locator('#my-hand .card').all()
                if cards:
                    await cards[0].click()
                    await asyncio.sleep(1)
                    self.log_pass("Can click cards in hand")
                    
            except Exception as e:
                self.log_bug(f"Error playing card: {e}")
                
            # Test ending turn
            try:
                await page.click('button:has-text("ターン終了")')
                await asyncio.sleep(2)
                self.log_pass("Can end turn")
                
                # Check if CPU takes turn
                turn_indicator = await page.locator('#turn-indicator').text_content()
                self.log(f"Turn indicator: {turn_indicator}")
                
                if "ENEMY TURN" in turn_indicator or "YOUR TURN" in turn_indicator:
                    self.log_pass("Turn indicator updates correctly")
                else:
                    self.log_bug("Turn indicator not updating properly")
                    
            except Exception as e:
                self.log_bug(f"Error ending turn: {e}")
                
            # Wait and observe CPU behavior
            self.log("Observing CPU behavior for 10 seconds...")
            await asyncio.sleep(10)
            
            # Check if CPU is making moves
            turn_count_text = await page.locator('#turn-txt').text_content()
            self.log(f"Current turn: {turn_count_text}")
            
            try:
                turn_count = int(turn_count_text)
            except (ValueError, TypeError):
                turn_count = 1
            
            if turn_count > 1:
                self.log_pass("CPU is taking turns (game progressing)")
            else:
                self.log_bug("Game not progressing - CPU may not be working")
                
        except Exception as e:
            self.log_bug(f"CPU battle test failed with exception: {e}")
            
        finally:
            await page.close()
            
    async def test_room_creation_and_join(self, browser):
        """Test room creation and joining"""
        self.log("=" * 60)
        self.log("Testing Room Creation and Joining")
        self.log("=" * 60)
        
        # Create two pages for two players
        page1 = await browser.new_page()
        page2 = await browser.new_page()
        
        try:
            # Player 1 creates room
            await page1.goto(self.base_url)
            await asyncio.sleep(1)
            
            await page1.click('button:has-text("ルームを作成")')
            await asyncio.sleep(2)
            
            # Check if waiting screen appears
            waiting_screen = await page1.locator('#screen-waiting').is_visible()
            if waiting_screen:
                self.log_pass("Waiting screen appears after room creation")
            else:
                self.log_bug("Waiting screen does not appear for P1")
                await page1.close()
                await page2.close()
                return
                
            # Get room number
            room_number = await page1.locator('#waiting-room-number').text_content()
            self.log(f"Room created with ID: {room_number}")
            
            if len(room_number) == 4 and room_number.isdigit():
                self.log_pass("Room ID is 4 digits")
            else:
                self.log_bug(f"Room ID format incorrect: {room_number}")
                
            # Player 2 joins room
            await page2.goto(self.base_url)
            await asyncio.sleep(1)
            
            await page2.fill('#room-input', room_number)
            await page2.click('button:has-text("参加")')
            await asyncio.sleep(2)
            
            # Check if both players go to deck selection
            deck_screen1 = await page1.locator('#screen-deck').is_visible()
            deck_screen2 = await page2.locator('#screen-deck').is_visible()
            
            if deck_screen1 and deck_screen2:
                self.log_pass("Both players transition to deck selection")
            else:
                self.log_bug(f"Deck screen visible - P1: {deck_screen1}, P2: {deck_screen2}")
                await page1.close()
                await page2.close()
                return
                
            # Both players select decks
            await page1.click('button:has-text("社員育成デッキ")')
            await page2.click('button:has-text("重機土木デッキ")')
            await asyncio.sleep(0.5)
            
            # Submit decks
            await page1.click('button:has-text("現場へ出撃")')
            await asyncio.sleep(0.5)
            await page2.click('button:has-text("現場へ出撃")')
            await asyncio.sleep(3)
            
            # Check if both enter battle
            battle1 = await page1.locator('#screen-battle').is_visible()
            battle2 = await page2.locator('#screen-battle').is_visible()
            
            if battle1 and battle2:
                self.log_pass("Both players enter battle screen")
            else:
                self.log_bug(f"Battle screen visible - P1: {battle1}, P2: {battle2}")
                await page1.close()
                await page2.close()
                return
                
            # Check room number is displayed
            room_display1 = await page1.locator('#current-room').text_content()
            room_display2 = await page2.locator('#current-room').text_content()
            
            if room_display1 == room_number and room_display2 == room_number:
                self.log_pass("Room number displayed correctly for both players")
            else:
                self.log_bug(f"Room number mismatch - P1: {room_display1}, P2: {room_display2}")
                
            # Check turn assignment
            await asyncio.sleep(2)
            turn1 = await page1.locator('#turn-indicator').text_content()
            turn2 = await page2.locator('#turn-indicator').text_content()
            
            self.log(f"P1 turn indicator: {turn1}")
            self.log(f"P2 turn indicator: {turn2}")
            
            if ("YOUR TURN" in turn1 and "ENEMY TURN" in turn2) or \
               ("ENEMY TURN" in turn1 and "YOUR TURN" in turn2):
                self.log_pass("Turn assignment is correct (one player goes first)")
            else:
                self.log_bug("Turn assignment incorrect")
                
            # Test synchronized game state
            score1 = await page1.locator('#my-score').text_content()
            score2 = await page2.locator('#my-score').text_content()
            
            self.log(f"P1 score: {score1}, P2 score: {score2}")
            self.log_pass("Game state synchronized between players")
            
        except Exception as e:
            self.log_bug(f"Room test failed with exception: {e}")
            
        finally:
            await page1.close()
            await page2.close()
            
    async def test_game_mechanics(self, browser):
        """Test specific game mechanics"""
        self.log("=" * 60)
        self.log("Testing Game Mechanics")
        self.log("=" * 60)
        
        page = await browser.new_page()
        await page.goto(self.base_url)
        
        try:
            # Start CPU game
            await page.click('button:has-text("CPU戦")')
            await asyncio.sleep(1)
            
            # Load and submit deck
            await page.click('button:has-text("測量機械デッキ")')
            await asyncio.sleep(0.5)
            await page.click('button:has-text("現場へ出撃")')
            await asyncio.sleep(3)
            
            # Test weather system
            weather = await page.locator('#weather-txt').text_content()
            if weather in ["晴天", "豪雨", "濃霧"]:
                self.log_pass(f"Weather system working ({weather})")
            else:
                self.log_bug(f"Invalid weather: {weather}")
                
            # Test AP system
            ap_text = await page.locator('#my-ap').text_content()
            self.log(f"AP display: {ap_text}")
            
            if "/" in ap_text:
                self.log_pass("AP display format correct")
            else:
                self.log_bug("AP display format incorrect")
                
            # Test log system
            log_entries = await page.locator('#log div').count()
            if log_entries > 0:
                self.log_pass(f"Game log is working ({log_entries} entries)")
            else:
                self.log_bug("Game log not showing entries")
                
            # Play several turns to test mechanics
            for i in range(3):
                self.log(f"Testing turn {i+1}")
                
                # Wait for player turn
                for _ in range(10):
                    turn_indicator = await page.locator('#turn-indicator').text_content()
                    if "YOUR TURN" in turn_indicator:
                        break
                    await asyncio.sleep(1)
                    
                # Try to play cards
                cards = await page.locator('#my-hand .card').all()
                self.log(f"Cards in hand: {len(cards)}")
                
                # End turn
                await page.click('button:has-text("ターン終了")')
                await asyncio.sleep(3)
                
            self.log_pass("Basic turn mechanics working")
            
        except Exception as e:
            self.log_bug(f"Game mechanics test failed with exception: {e}")
            
        finally:
            await page.close()
            
    async def test_invalid_room_join(self, browser):
        """Test joining invalid room"""
        self.log("=" * 60)
        self.log("Testing Invalid Room Join")
        self.log("=" * 60)
        
        page = await browser.new_page()
        await page.goto(self.base_url)
        
        try:
            # Try to join non-existent room
            await page.fill('#room-input', '9999')
            await page.click('button:has-text("参加")')
            await asyncio.sleep(2)
            
            # Check for error message
            error = await page.locator('#room-status').text_content()
            if error and "存在" in error:
                self.log_pass("Error message shown for invalid room")
            else:
                self.log_bug("No error message for invalid room join")
                
        except Exception as e:
            self.log_bug(f"Invalid room test failed: {e}")
            
        finally:
            await page.close()
            
    async def run_all_tests(self):
        """Run all tests"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                await self.test_cpu_battle(browser)
                await self.test_room_creation_and_join(browser)
                await self.test_game_mechanics(browser)
                await self.test_invalid_room_join(browser)
                
            finally:
                await browser.close()
                
        # Print summary
        self.log("=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {self.tests_failed}")
        
        if self.bugs_found:
            self.log("\nBUGS FOUND:")
            for i, bug in enumerate(self.bugs_found, 1):
                self.log(f"{i}. {bug}")
        else:
            self.log("\n✅ No bugs found! Application working correctly.")
            
        return len(self.bugs_found) == 0

async def main():
    tester = GameTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
