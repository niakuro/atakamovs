#!/usr/bin/env python3
"""
Backend testing for 観測君VS ULTIMATE Ver 4.1
Tests server-side logic and Socket.IO communication
"""

import socketio
import time
import threading
from typing import Optional, Dict, Any

class BackendTester:
    def __init__(self, url='http://localhost:5000'):
        self.url = url
        self.bugs_found = []
        self.tests_passed = 0
        self.tests_failed = 0
        
        # Create socket clients
        self.client1 = socketio.Client()
        self.client2 = socketio.Client()
        
        # Store received data
        self.client1_data = {}
        self.client2_data = {}
        
        # Setup event handlers
        self.setup_client1_handlers()
        self.setup_client2_handlers()
        
    def log(self, message: str):
        print(f"[TEST] {message}")
        
    def log_bug(self, bug: str):
        print(f"[BUG] {bug}")
        self.bugs_found.append(bug)
        self.tests_failed += 1
        
    def log_pass(self, test: str):
        print(f"[PASS] {test}")
        self.tests_passed += 1
        
    def setup_client1_handlers(self):
        @self.client1.on('room_created')
        def on_room_created(data):
            self.client1_data['room_created'] = data
            self.log(f"Client 1: Room created - {data}")
            
        @self.client1.on('room_joined')
        def on_room_joined(data):
            self.client1_data['room_joined'] = data
            self.log(f"Client 1: Room joined - {data}")
            
        @self.client1.on('room_ready')
        def on_room_ready(data):
            self.client1_data['room_ready'] = data
            self.log(f"Client 1: Room ready - {data}")
            
        @self.client1.on('update_ui')
        def on_update_ui(data):
            self.client1_data['update_ui'] = data
            self.log(f"Client 1: UI update received")
            
        @self.client1.on('error')
        def on_error(data):
            self.client1_data['error'] = data
            self.log(f"Client 1: Error - {data}")
            
    def setup_client2_handlers(self):
        @self.client2.on('room_created')
        def on_room_created(data):
            self.client2_data['room_created'] = data
            self.log(f"Client 2: Room created - {data}")
            
        @self.client2.on('room_joined')
        def on_room_joined(data):
            self.client2_data['room_joined'] = data
            self.log(f"Client 2: Room joined - {data}")
            
        @self.client2.on('room_ready')
        def on_room_ready(data):
            self.client2_data['room_ready'] = data
            self.log(f"Client 2: Room ready - {data}")
            
        @self.client2.on('update_ui')
        def on_update_ui(data):
            self.client2_data['update_ui'] = data
            self.log(f"Client 2: UI update received")
            
        @self.client2.on('error')
        def on_error(data):
            self.client2_data['error'] = data
            self.log(f"Client 2: Error - {data}")
            
    def test_room_creation(self):
        """Test room creation"""
        self.log("=" * 60)
        self.log("Testing Room Creation")
        self.log("=" * 60)
        
        try:
            self.client1.connect(self.url)
            time.sleep(0.5)
            
            if self.client1.connected:
                self.log_pass("Client 1 connected to server")
            else:
                self.log_bug("Client 1 failed to connect")
                return
                
            # Create room
            self.client1_data.clear()
            self.client1.emit('create_room')
            time.sleep(1)
            
            if 'room_created' in self.client1_data:
                room_data = self.client1_data['room_created']
                self.log_pass("Room creation event received")
                
                if 'room_id' in room_data:
                    room_id = room_data['room_id']
                    if len(room_id) == 4 and room_id.isdigit():
                        self.log_pass(f"Room ID is valid 4-digit number: {room_id}")
                    else:
                        self.log_bug(f"Room ID format invalid: {room_id}")
                else:
                    self.log_bug("Room ID not in response")
                    
                if 'player_id' in room_data:
                    player_id = room_data['player_id']
                    if player_id == 'p1':
                        self.log_pass("Creator assigned as P1")
                    else:
                        self.log_bug(f"Creator got wrong player ID: {player_id}")
                else:
                    self.log_bug("Player ID not in response")
            else:
                self.log_bug("No room_created event received")
                
        except Exception as e:
            self.log_bug(f"Room creation test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
                
    def test_room_join(self):
        """Test joining a room"""
        self.log("=" * 60)
        self.log("Testing Room Join")
        self.log("=" * 60)
        
        try:
            # Connect client 1 and create room
            self.client1.connect(self.url)
            time.sleep(0.5)
            
            self.client1_data.clear()
            self.client1.emit('create_room')
            time.sleep(1)
            
            if 'room_created' not in self.client1_data:
                self.log_bug("Failed to create room for join test")
                return
                
            room_id = self.client1_data['room_created']['room_id']
            self.log(f"Room created: {room_id}")
            
            # Connect client 2 and join room
            self.client2.connect(self.url)
            time.sleep(0.5)
            
            if self.client2.connected:
                self.log_pass("Client 2 connected to server")
            else:
                self.log_bug("Client 2 failed to connect")
                return
                
            self.client2_data.clear()
            self.client2.emit('join_room', {'room_id': room_id})
            time.sleep(1)
            
            if 'room_joined' in self.client2_data:
                self.log_pass("Client 2 received room_joined event")
                
                join_data = self.client2_data['room_joined']
                if join_data.get('player_id') == 'p2':
                    self.log_pass("Joiner assigned as P2")
                else:
                    self.log_bug(f"Joiner got wrong player ID: {join_data.get('player_id')}")
            else:
                self.log_bug("Client 2 did not receive room_joined event")
                
            # Check if both clients receive room_ready
            time.sleep(0.5)
            if 'room_ready' in self.client1_data:
                self.log_pass("Client 1 received room_ready event")
            else:
                self.log_bug("Client 1 did not receive room_ready event")
                
            if 'room_ready' in self.client2_data:
                self.log_pass("Client 2 received room_ready event")
            else:
                self.log_bug("Client 2 did not receive room_ready event")
                
        except Exception as e:
            self.log_bug(f"Room join test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def test_invalid_room_join(self):
        """Test joining non-existent room"""
        self.log("=" * 60)
        self.log("Testing Invalid Room Join")
        self.log("=" * 60)
        
        try:
            self.client1.connect(self.url)
            time.sleep(0.5)
            
            self.client1_data.clear()
            self.client1.emit('join_room', {'room_id': '9999'})
            time.sleep(1)
            
            if 'error' in self.client1_data:
                error_msg = self.client1_data['error'].get('message', '')
                if '存在' in error_msg or 'not' in error_msg.lower():
                    self.log_pass(f"Error message received for invalid room: {error_msg}")
                else:
                    self.log_bug(f"Unexpected error message: {error_msg}")
            else:
                self.log_bug("No error event received for invalid room")
                
        except Exception as e:
            self.log_bug(f"Invalid room test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
                
    def test_deck_submission(self):
        """Test deck submission and game start"""
        self.log("=" * 60)
        self.log("Testing Deck Submission")
        self.log("=" * 60)
        
        try:
            # Create room and join
            self.client1.connect(self.url)
            self.client2.connect(self.url)
            time.sleep(0.5)
            
            self.client1.emit('create_room')
            time.sleep(1)
            
            room_id = self.client1_data['room_created']['room_id']
            self.client2.emit('join_room', {'room_id': room_id})
            time.sleep(1)
            
            # Submit decks
            deck = ['Newbie'] * 40  # Simple 40-card deck
            
            self.client1_data.clear()
            self.client2_data.clear()
            
            self.client1.emit('submit_deck', {'player_id': 'p1', 'deck': deck})
            time.sleep(0.5)
            self.client2.emit('submit_deck', {'player_id': 'p2', 'deck': deck})
            time.sleep(2)
            
            # Check if game starts
            if 'update_ui' in self.client1_data:
                game_state = self.client1_data['update_ui']
                self.log_pass("Client 1 received game state update")
                
                # Check game state structure
                if 'players' in game_state:
                    self.log_pass("Game state contains players")
                    
                    p1 = game_state['players'].get('p1', {})
                    p2 = game_state['players'].get('p2', {})
                    
                    if len(p1.get('hand', [])) > 0:
                        self.log_pass(f"P1 has {len(p1['hand'])} cards in hand")
                    else:
                        self.log_bug("P1 has no cards in hand")
                        
                    if len(p2.get('hand', [])) > 0:
                        self.log_pass(f"P2 has {len(p2['hand'])} cards in hand")
                    else:
                        self.log_bug("P2 has no cards in hand")
                        
                    # Check turn assignment
                    current_turn = game_state.get('turn')
                    if current_turn in ['p1', 'p2']:
                        self.log_pass(f"Turn assigned to {current_turn}")
                    else:
                        self.log_bug(f"Invalid turn value: {current_turn}")
                        
                    # Check weather
                    weather = game_state.get('weather')
                    if weather in ['晴天', '豪雨', '濃霧']:
                        self.log_pass(f"Weather system working: {weather}")
                    else:
                        self.log_bug(f"Invalid weather: {weather}")
                else:
                    self.log_bug("Game state missing players")
            else:
                self.log_bug("No update_ui event received after deck submission")
                
        except Exception as e:
            self.log_bug(f"Deck submission test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def test_full_room_join(self):
        """Test joining a full room"""
        self.log("=" * 60)
        self.log("Testing Full Room Join")
        self.log("=" * 60)
        
        try:
            client3 = socketio.Client()
            
            # Create room with 2 players
            self.client1.connect(self.url)
            self.client2.connect(self.url)
            time.sleep(0.5)
            
            self.client1.emit('create_room')
            time.sleep(1)
            
            room_id = self.client1_data['room_created']['room_id']
            self.client2.emit('join_room', {'room_id': room_id})
            time.sleep(1)
            
            # Try to join with 3rd client
            client3_data = {}
            
            @client3.on('error')
            def on_error(data):
                client3_data['error'] = data
                
            client3.connect(self.url)
            time.sleep(0.5)
            
            client3.emit('join_room', {'room_id': room_id})
            time.sleep(1)
            
            if 'error' in client3_data:
                error_msg = client3_data['error'].get('message', '')
                if '満員' in error_msg or 'full' in error_msg.lower():
                    self.log_pass(f"Correct error for full room: {error_msg}")
                else:
                    self.log_bug(f"Unexpected error message: {error_msg}")
            else:
                self.log_bug("No error when joining full room")
                
            client3.disconnect()
                
        except Exception as e:
            self.log_bug(f"Full room test failed: {e}")
        finally:
            if self.client1.connected:
                self.client1.disconnect()
            if self.client2.connected:
                self.client2.disconnect()
                
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("\n" + "=" * 60)
        self.log("BACKEND TESTING - 観測君VS ULTIMATE Ver 4.1")
        self.log("=" * 60 + "\n")
        
        self.test_room_creation()
        time.sleep(0.5)
        
        self.test_room_join()
        time.sleep(0.5)
        
        self.test_invalid_room_join()
        time.sleep(0.5)
        
        self.test_deck_submission()
        time.sleep(0.5)
        
        self.test_full_room_join()
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
            self.log("\n✅ No bugs found! Backend working correctly.")
            
        return len(self.bugs_found) == 0

def main():
    tester = BackendTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
