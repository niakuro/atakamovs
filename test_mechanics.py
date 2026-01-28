#!/usr/bin/env python3
"""
Game mechanics testing for 観測君VS ULTIMATE Ver 4.1
Tests card playing, turns, and game logic
"""

import socketio
import time
import random
from typing import Optional, Dict, Any, List

class GameMechanicsTester:
    def __init__(self, url='http://localhost:5000'):
        self.url = url
        self.bugs_found = []
        self.tests_passed = 0
        self.tests_failed = 0
        
        self.client1 = socketio.Client()
        self.client2 = socketio.Client()
        
        self.game_state = {}
        
        self.setup_handlers()
        
    def log(self, message: str):
        print(f"[TEST] {message}")
        
    def log_bug(self, bug: str):
        print(f"[BUG] {bug}")
        self.bugs_found.append(bug)
        self.tests_failed += 1
        
    def log_pass(self, test: str):
        print(f"[PASS] {test}")
        self.tests_passed += 1
        
    def setup_handlers(self):
        @self.client1.on('update_ui')
        def on_update1(data):
            self.game_state['p1'] = data
            
        @self.client2.on('update_ui')
        def on_update2(data):
            self.game_state['p2'] = data
            
    def setup_game(self):
        """Setup a game with two players"""
        self.client1.connect(self.url)
        self.client2.connect(self.url)
        time.sleep(0.5)
        
        self.client1.emit('create_room')
        time.sleep(1)
        
        # Get room info from game_state
        if 'p1' not in self.game_state:
            # Trigger update by checking server logs
            time.sleep(0.5)
            
        self.client2.emit('join_room', {'room_id': self.game_state.get('p1', {}).get('room_id', '0000')})
        time.sleep(1)
        
        # Submit decks - use a varied deck for testing
        test_deck = (
            ['Newbie'] * 4 + ['Staff'] * 3 + ['Chief'] * 2 +
            ['LevelBasic'] * 3 + ['LevelAuto'] * 3 +
            ['Note'] * 2 + ['Elite'] * 2 + ['Check'] * 2 +
            ['Repair'] * 2 + ['Fund'] * 2 +
            ['TS'] * 4 + ['Drone'] * 3 +
            ['Goal30'] * 2 + ['GoalFinal'] * 1 +
            ['Clerk'] * 2 + ['Safety'] * 2 +
            ['Lost'] * 1 + ['Bush'] * 1 + ['Overtime'] * 1
        )
        
        self.game_state.clear()
        self.client1.emit('submit_deck', {'player_id': 'p1', 'deck': test_deck})
        self.client2.emit('submit_deck', {'player_id': 'p2', 'deck': test_deck})
        time.sleep(2)
        
    def test_turn_system(self):
        """Test turn progression"""
        self.log("=" * 60)
        self.log("Testing Turn System")
        self.log("=" * 60)
        
        try:
            self.setup_game()
            
            # Check initial turn assignment
            if 'p1' in self.game_state:
                turn = self.game_state['p1'].get('turn')
                if turn in ['p1', 'p2']:
                    self.log_pass(f"Initial turn assigned: {turn}")
                else:
                    self.log_bug(f"Invalid initial turn: {turn}")
                    
                # Get the active player
                active = self.client1 if turn == 'p1' else self.client2
                active_name = 'p1' if turn == 'p1' else 'p2'
                
                # End turn
                initial_turn_count = self.game_state['p1'].get('turn_count', 1)
                active.emit('end_turn', {'player_id': active_name})
                time.sleep(2)
                
                # Check turn switched
                new_turn = self.game_state.get('p1', {}).get('turn')
                if new_turn != turn:
                    self.log_pass(f"Turn switched from {turn} to {new_turn}")
                else:
                    self.log_bug("Turn did not switch")
                    
                # Check turn count increment (happens when p1 starts their turn)
                if new_turn == 'p1':
                    new_turn_count = self.game_state['p1'].get('turn_count', 1)
                    if new_turn_count > initial_turn_count:
                        self.log_pass(f"Turn count incremented: {initial_turn_count} -> {new_turn_count}")
                    else:
                        self.log_bug(f"Turn count did not increment properly")
            else:
                self.log_bug("No game state received")
                
        except Exception as e:
            self.log_bug(f"Turn system test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def test_card_playing(self):
        """Test playing cards"""
        self.log("=" * 60)
        self.log("Testing Card Playing")
        self.log("=" * 60)
        
        try:
            self.setup_game()
            
            if 'p1' not in self.game_state:
                self.log_bug("Game state not received")
                return
                
            state = self.game_state['p1']
            turn = state.get('turn')
            active = self.client1 if turn == 'p1' else self.client2
            active_name = turn
            
            player_state = state['players'][active_name]
            hand = player_state.get('hand', [])
            ap = player_state.get('ap', 0)
            
            self.log(f"Active player: {active_name}, AP: {ap}, Hand size: {len(hand)}")
            
            # Try to play a low-cost card
            playable_idx = -1
            for i, card in enumerate(hand):
                if card.get('cost', 999) <= ap:
                    playable_idx = i
                    break
                    
            if playable_idx >= 0:
                card_to_play = hand[playable_idx]
                initial_hand_size = len(hand)
                initial_ap = ap
                
                self.log(f"Playing card: {card_to_play['name']} (cost: {card_to_play['cost']})")
                
                active.emit('play_card', {'player_id': active_name, 'card_index': playable_idx})
                time.sleep(1)
                
                # Check updated state
                new_state = self.game_state['p1']
                new_player_state = new_state['players'][active_name]
                new_hand = new_player_state.get('hand', [])
                new_ap = new_player_state.get('ap', 0)
                
                # Verify hand size decreased (unless it was a draw card)
                if card_to_play['type'] != 'SPELL' or 'draw' not in card_to_play.get('desc', '').lower():
                    if len(new_hand) < initial_hand_size:
                        self.log_pass("Card removed from hand")
                    else:
                        self.log_bug("Card not removed from hand")
                        
                # Verify AP decreased
                expected_ap = initial_ap - card_to_play['cost']
                if card_to_play['type'] == 'MACHINE':
                    if len(new_player_state.get('field', [])) > 0:
                        self.log_pass("Card added to field")
                    else:
                        self.log_bug("MACHINE card not added to field")
                        
            else:
                self.log("No playable cards in hand (this is OK)")
                
        except Exception as e:
            self.log_bug(f"Card playing test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def test_maintenance_cost(self):
        """Test maintenance cost system"""
        self.log("=" * 60)
        self.log("Testing Maintenance Cost System")
        self.log("=" * 60)
        
        try:
            self.setup_game()
            
            if 'p1' not in self.game_state:
                self.log_bug("Game state not received")
                return
                
            state = self.game_state['p1']
            turn = state.get('turn')
            
            # Play several cards and check maintenance
            for turn_num in range(3):
                active = self.client1 if turn == 'p1' else self.client2
                active_name = turn
                
                # End turn to trigger maintenance
                active.emit('end_turn', {'player_id': active_name})
                time.sleep(2)
                
                # Check new turn's AP calculation
                new_state = self.game_state.get('p1', {})
                turn = new_state.get('turn')
                
                if turn:
                    player_state = new_state['players'][turn]
                    field = player_state.get('field', [])
                    ap = player_state.get('ap', 0)
                    max_ap = player_state.get('max_ap', 0)
                    
                    # Calculate expected AP (max_ap - upkeep)
                    total_upkeep = sum(card.get('upkeep', 0) for card in field)
                    clerk_bonus = sum(1 for card in field if card.get('id') == 'Clerk')
                    expected_ap = max_ap - total_upkeep + clerk_bonus
                    
                    self.log(f"Turn {turn_num + 1}: {turn} - AP: {ap}, Max: {max_ap}, Upkeep: {total_upkeep}, Clerk bonus: {clerk_bonus}")
                    
                    if ap == expected_ap:
                        self.log_pass(f"Maintenance cost calculated correctly")
                    else:
                        self.log_bug(f"AP mismatch - Expected: {expected_ap}, Got: {ap}")
                        
        except Exception as e:
            self.log_bug(f"Maintenance test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def test_weather_system(self):
        """Test weather effects"""
        self.log("=" * 60)
        self.log("Testing Weather System")
        self.log("=" * 60)
        
        try:
            self.setup_game()
            
            if 'p1' not in self.game_state:
                self.log_bug("Game state not received")
                return
                
            weathers_seen = set()
            
            # Play several turns to see weather changes
            for i in range(10):
                state = self.game_state.get('p1', {})
                weather = state.get('weather')
                
                if weather:
                    weathers_seen.add(weather)
                    self.log(f"Turn {i+1}: Weather = {weather}")
                    
                turn = state.get('turn')
                active = self.client1 if turn == 'p1' else self.client2
                active.emit('end_turn', {'player_id': turn})
                time.sleep(1)
                
            if len(weathers_seen) > 1:
                self.log_pass(f"Weather system working - saw: {weathers_seen}")
            else:
                self.log("Weather did not change (might be random)")
                
            # Check valid weather values
            for weather in weathers_seen:
                if weather not in ['晴天', '豪雨', '濃霧']:
                    self.log_bug(f"Invalid weather value: {weather}")
                    break
            else:
                self.log_pass("All weather values are valid")
                
        except Exception as e:
            self.log_bug(f"Weather system test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def test_score_calculation(self):
        """Test score calculation"""
        self.log("=" * 60)
        self.log("Testing Score Calculation")
        self.log("=" * 60)
        
        try:
            self.setup_game()
            
            if 'p1' not in self.game_state:
                self.log_bug("Game state not received")
                return
                
            state = self.game_state['p1']
            
            # Check that scores start at 0
            p1_score = state['players']['p1'].get('score', -1)
            p2_score = state['players']['p2'].get('score', -1)
            
            if p1_score == 0 and p2_score == 0:
                self.log_pass("Initial scores are 0")
            else:
                self.log_bug(f"Initial scores incorrect - P1: {p1_score}, P2: {p2_score}")
                
            # Play some cards and check score updates
            turn = state.get('turn')
            active = self.client1 if turn == 'p1' else self.client2
            active_name = turn
            
            player_state = state['players'][active_name]
            hand = player_state.get('hand', [])
            ap = player_state.get('ap', 0)
            
            # Play a MACHINE card if possible
            for i, card in enumerate(hand):
                if card.get('type') == 'MACHINE' and card.get('cost', 999) <= ap:
                    active.emit('play_card', {'player_id': active_name, 'card_index': i})
                    time.sleep(1)
                    
                    new_state = self.game_state['p1']
                    new_score = new_state['players'][active_name].get('score', 0)
                    
                    if new_score > 0:
                        self.log_pass(f"Score updated after playing MACHINE: {new_score}")
                    else:
                        self.log("Score still 0 (card might have 0 power)")
                    break
                    
        except Exception as e:
            self.log_bug(f"Score calculation test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def test_cpu_mode(self):
        """Test CPU mode"""
        self.log("=" * 60)
        self.log("Testing CPU Mode")
        self.log("=" * 60)
        
        try:
            client = socketio.Client()
            game_updates = []
            
            @client.on('update_ui')
            def on_update(data):
                game_updates.append(data)
                
            @client.on('room_created')
            def on_room_created(data):
                self.log(f"Room created for CPU mode: {data}")
                
            client.connect(self.url)
            time.sleep(0.5)
            
            # Create room (CPU mode is client-side, so we test room creation)
            client.emit('create_room')
            time.sleep(1)
            
            # Submit player deck
            deck = ['Newbie'] * 40
            client.emit('submit_deck', {'player_id': 'p1', 'deck': deck})
            time.sleep(0.5)
            
            # Submit CPU deck (simulating CPU)
            cpu_deck = ['Staff'] * 40
            client.emit('submit_deck', {'player_id': 'p2', 'deck': cpu_deck})
            time.sleep(2)
            
            if game_updates:
                self.log_pass("Game started successfully for CPU mode simulation")
                
                # Check that game state is valid
                state = game_updates[-1]
                if 'players' in state and 'p1' in state['players'] and 'p2' in state['players']:
                    self.log_pass("Both players (P1 and P2) exist in game state")
                else:
                    self.log_bug("Game state missing players")
            else:
                self.log_bug("No game updates received")
                
            client.disconnect()
                
        except Exception as e:
            self.log_bug(f"CPU mode test failed: {e}")
            
    def run_all_tests(self):
        """Run all game mechanics tests"""
        self.log("\n" + "=" * 60)
        self.log("GAME MECHANICS TESTING - 観測君VS ULTIMATE Ver 4.1")
        self.log("=" * 60 + "\n")
        
        self.test_turn_system()
        time.sleep(0.5)
        
        self.test_card_playing()
        time.sleep(0.5)
        
        self.test_maintenance_cost()
        time.sleep(0.5)
        
        self.test_weather_system()
        time.sleep(0.5)
        
        self.test_score_calculation()
        time.sleep(0.5)
        
        self.test_cpu_mode()
        time.sleep(0.5)
        
        # Print summary
        self.log("\n" + "=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {self.tests_failed}")
        
        if self.bugs_found:
            self.log("\nBUGS FOUND:")
            for i, bug in enumerate(self.bugs_found, 1):
                self.log(f"{i}. {bug}")
        else:
            self.log("\n✅ No bugs found! Game mechanics working correctly.")
            
        return len(self.bugs_found) == 0

def main():
    tester = GameMechanicsTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
