import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
from threading import Lock
import traceback

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-truly-secret-key-for-roulette'
socketio = SocketIO(app, async_mode='eventlet')
thread = None
thread_lock = Lock()
game_state = {'timer': 30, 'spinning': False, 'winning_number': None}

# --- Roulette Game Data & Logic ---
WHEEL_NUMBERS = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
PAYOUTS = {
    'single': 35, 'dozen': 2, 'column': 2, 'red': 1, 'black': 1,
    'even': 1, 'odd': 1, 'low': 1, 'high': 1
}

def get_bet_type_and_values(bet_key):
    parts = bet_key.split('_')
    bet_type = parts[0]
    if len(parts) == 1: return bet_type, []
    values = [int(p) for p in parts[1:]]
    return bet_type, values

def calculate_winnings(bets, winning_number):
    total_return = 0
    win_details = {}
    for bet_key, amount in bets.items():
        bet_type, values = get_bet_type_and_values(bet_key)
        won = False
        if winning_number == 0 and bet_type not in ['single']: continue

        if bet_type == 'single' and winning_number in values: won = True
        elif bet_type == 'red' and winning_number in RED_NUMBERS: won = True
        elif bet_type == 'black' and winning_number in BLACK_NUMBERS: won = True
        elif bet_type == 'even' and winning_number != 0 and winning_number % 2 == 0: won = True
        elif bet_type == 'odd' and winning_number % 2 != 0: won = True
        elif bet_type == 'low' and 1 <= winning_number <= 18: won = True
        elif bet_type == 'high' and 19 <= winning_number <= 36: won = True
        elif bet_type == 'dozen':
            if values[0] == 1 and 1 <= winning_number <= 12: won = True
            elif values[0] == 2 and 13 <= winning_number <= 24: won = True
            elif values[0] == 3 and 25 <= winning_number <= 36: won = True
        elif bet_type == 'column':
            if winning_number == 0: continue
            col = 3 if winning_number % 3 == 0 else winning_number % 3
            if values[0] == col: won = True

        if won:
            payout = PAYOUTS.get(bet_type, 0)
            winnings = (amount * payout)
            total_return += winnings + amount
            win_details[bet_key] = winnings + amount
    return total_return, win_details

# --- Background Thread ---
def game_timer_thread():
    global game_state
    while True:
        try:
            socketio.sleep(1)
            if not game_state['spinning']:
                game_state['timer'] -= 1
                if game_state['timer'] <= 0:
                    game_state['spinning'] = True
                    game_state['timer'] = 5
                    socketio.emit('start_spin', {'duration': 4500})
                    
                    winning_number = random.choice(WHEEL_NUMBERS)
                    game_state['winning_number'] = winning_number
                    socketio.sleep(4.5)
                    
                    socketio.emit('spin_result', {
                        'winning_number': winning_number,
                        'wheel_position': WHEEL_NUMBERS.index(winning_number)
                    })
                    game_state['spinning'] = False
                    game_state['timer'] = 30
            socketio.emit('timer_update', {'countdown': game_state['timer'], 'spinning': game_state['spinning']})
        except Exception:
            print("--- FATAL ERROR IN BACKGROUND THREAD ---")
            print(traceback.format_exc())
            print("--------------------------------------")

# --- Routes & SocketIO Events ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=game_timer_thread)
    session['balance'] = 1000
    session['bets'] = {}
    session['last_bets'] = {}
    emit('game_state', {'balance': session['balance'], 'timer': game_state['timer']})

@socketio.on('place_bet')
def handle_place_bet(data):
    if game_state.get('spinning') or game_state.get('timer', 0) <= 5: return
    bet_type, amount = data.get('bet_type'), int(data.get('amount', 0))
    if not bet_type or amount <= 0 or session.get('balance', 0) < amount: return
    session['balance'] -= amount
    session['bets'][bet_type] = session['bets'].get(bet_type, 0) + amount
    session.modified = True
    emit('bet_placed', {'bet_type': bet_type, 'total_bet_on_type': session['bets'][bet_type]})
    emit('balance_update', {'balance': session['balance']})

@socketio.on('repeat_bet')
def handle_repeat_bet():
    if game_state.get('spinning') or game_state.get('timer', 0) <= 5: return
    last_bets = session.get('last_bets', {})
    total_last_bet = sum(last_bets.values())
    if not last_bets or session.get('balance', 0) < total_last_bet: return
    session['bets'] = last_bets.copy()
    session['balance'] -= total_last_bet
    session.modified = True
    emit('bets_cleared')
    for bet_type, amount in session['bets'].items():
        emit('bet_placed', {'bet_type': bet_type, 'total_bet_on_type': amount})
    emit('balance_update', {'balance': session['balance']})

@socketio.on('clear_bets')
def handle_clear_bets():
    if game_state.get('spinning') or game_state.get('timer', 0) <= 5: return
    session['balance'] += sum(session.get('bets', {}).values())
    session['bets'] = {}
    session.modified = True
    emit('bets_cleared')
    emit('balance_update', {'balance': session['balance']})

@socketio.on('payout_complete')
def handle_payout_complete():
    winning_number = game_state.get('winning_number')
    if winning_number is None: return
    bets = session.get('bets', {})
    total_spent = sum(bets.values())
    total_return, win_details = calculate_winnings(bets, winning_number)
    session['balance'] += total_return
    net_change = total_return - total_spent
    session['last_bets'] = bets.copy()
    session['bets'] = {}
    session.modified = True
    emit('payout_result', {'balance': session['balance'], 'net_change': net_change, 'win_details': win_details})

# --- HTML, CSS, JavaScript Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask Roulette Game</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --board-green: #2c6b2f;
            --felt-green: #3a8a40;
            --wood-dark: #3d2a1a;
            --wood-light: #5a3e26;
            --gold: #ffd700;
            --chip-red: #d9534f;
            --chip-blue: #0275d8;
            --chip-green: #5cb85c;
            --chip-black: #292b2c;
            --num-red: #e74c3c;
            --num-black: #2c3e50;
        }
        body {
            background-color: var(--wood-dark);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow-x: hidden;
        }
        .game-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            gap: 20px;
        }
        .top-section {
            display: flex;
            justify-content: space-around;
            width: 100%;
            max-width: 1200px;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        .wheel-container {
            position: relative;
            width: 300px;
            height: 300px;
        }
        .wheel {
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, var(--felt-green) 40%, var(--board-green) 42%);
            border-radius: 50%;
            transition: transform 4.5s cubic-bezier(0.2, 0.8, 0.2, 1);
            border: 10px solid var(--wood-light);
            box-shadow: 0 0 20px rgba(0,0,0,0.5) inset, 0 0 15px black;
            position: relative;
        }
        .wheel-number {
            position: absolute;
            top: 50%;
            left: 50%;
            transform-origin: center center;
            width: 30px;
            height: 30px;
            margin-left: -15px;
            margin-top: -15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: bold;
            color: white;
        }
        .wheel-number.red { background-color: var(--num-red); border-radius: 5px; }
        .wheel-number.black { background-color: var(--num-black); border-radius: 5px; }
        .wheel-number.green { background-color: var(--board-green); border-radius: 50%; }

        .wheel-pointer {
            position: absolute;
            top: -15px; /* Adjusted to sit nicely on the border */
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-top: 25px solid var(--gold);
            z-index: 10;
        }
        .winning-number-display {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            background-color: rgba(0,0,0,0.7);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 3em;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 4px black;
            border: 5px solid var(--gold);
        }
        .history-bar {
            display: flex;
            gap: 5px;
            background-color: rgba(0,0,0,0.3);
            padding: 5px;
            border-radius: 5px;
            height: 50px;
            align-items: center;
            flex-wrap: nowrap;
            overflow-x: auto;
        }
        .history-number {
            flex-shrink: 0;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
        }
        .history-number.red { background-color: var(--num-red); }
        .history-number.black { background-color: var(--num-black); }
        .history-number.green { background-color: var(--board-green); }

        .betting-table-container {
            background-color: var(--board-green);
            padding: 15px;
            border-radius: 10px;
            border: 5px solid var(--wood-light);
            box-shadow: 0 0 15px black;
            width: 100%;
            max-width: 900px;
        }
        .betting-grid {
            display: grid;
            grid-template-columns: 50px repeat(12, 1fr);
            grid-template-rows: repeat(5, 1fr);
            gap: 3px;
        }
        .bet-spot {
            background-color: var(--felt-green);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            font-weight: bold;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            min-height: 50px;
            border-radius: 5px;
            transition: all 0.2s;
            position: relative;
            font-size: clamp(0.7rem, 2.5vw, 1.1rem);
        }
        .bet-spot:hover { background-color: #4caf50; transform: scale(1.05); z-index: 10; }
        .bet-spot.red-area { background-color: var(--num-red); }
        .bet-spot.black-area { background-color: var(--num-black); }
        .bet-spot.winning {
            box-shadow: 0 0 25px var(--gold);
            transform: scale(1.1);
            border-color: var(--gold);
        }
        .zero { grid-row: 1 / span 3; grid-column: 1 / span 1; }
        .col-btn { grid-column: 14 / span 1; }
        .dozen { grid-column: span 4; }
        .outside-bet { grid-column: span 2; }

        .chip-display {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(0,0,0,0.6);
            color: var(--gold);
            padding: 2px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        }
        .bet-spot .chip-display.visible { opacity: 1; }

        .bottom-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            max-width: 1200px;
            background-color: rgba(0,0,0,0.4);
            padding: 10px;
            border-radius: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .chips-container .chip {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin: 0 5px;
            cursor: pointer;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            border: 3px solid white;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .chips-container .chip.selected {
            transform: scale(1.15);
            box-shadow: 0 0 15px var(--gold);
        }
        .chip[data-value="1"] { background-color: var(--chip-blue); color: white;}
        .chip[data-value="5"] { background-color: var(--chip-red); color: white;}
        .chip[data-value="25"] { background-color: var(--chip-green); color: white;}
        .chip[data-value="100"] { background-color: var(--chip-black); color: var(--gold);}

        .player-info, .controls {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .balance-display { font-size: 1.5em; }
        
        .timer {
            font-size: 2em;
            font-weight: bold;
            width: 150px;
            text-align: center;
        }
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(-100px);
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            z-index: 1000;
            opacity: 0;
            transition: all 0.5s ease-in-out;
            font-size: 1.2em;
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }
        .notification.show { opacity: 1; transform: translateX(-50%) translateY(0); }
        .notification.win { background-color: var(--board-green); border: 2px solid var(--gold); }
        .notification.loss { background-color: var(--num-red); }
        .notification.error { background-color: #f0ad4e; }
    </style>
</head>
<body>
    <div class="game-container">
        <div class="top-section">
            <div class="wheel-container">
                <div class="wheel" id="wheel">
                    </div>
                <div class="wheel-pointer"></div>
                <div class="winning-number-display" id="winning-number-display">--</div>
            </div>
            <div>
                <h4>Recent Numbers</h4>
                <div class="history-bar" id="history-bar"></div>
                 <div class="timer mt-3" id="timer"></div>
            </div>
        </div>

        <div class="betting-table-container">
            <div class="betting-grid" id="betting-grid">
                </div>
        </div>

        <div class="bottom-bar">
            <div class="player-info">
                <span>Balance:</span>
                <span class="balance-display" id="balance-display">$1000</span>
            </div>
            <div class="chips-container" id="chips-container">
                <div class="chip" data-value="1">1</div>
                <div class="chip selected" data-value="5">5</div>
                <div class="chip" data-value="25">25</div>
                <div class="chip" data-value="100">100</div>
            </div>
            <div class="controls">
                <button id="repeat-bet-btn" class="btn btn-info">Repeat Bet</button>
                <button id="clear-bets-btn" class="btn btn-warning">Clear Bets</button>
            </div>
        </div>
    </div>
    
    <div id="notification" class="notification"></div>

    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const socket = io();
            const wheel = document.getElementById('wheel');
            const bettingGrid = document.getElementById('betting-grid');
            const balanceDisplay = document.getElementById('balance-display');
            const chipsContainer = document.getElementById('chips-container');
            const winNumDisplay = document.getElementById('winning-number-display');
            const timerDisplay = document.getElementById('timer');
            const historyBar = document.getElementById('history-bar');
            
            const RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36];
            const BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35];
            const WHEEL_NUMBERS_ORDER = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26];

            let selectedChipValue = 5;
            let currentRotation = 0;
            let numberChangeInterval;
            let history = [];

            function initializeGame() {
                createBettingBoard();
                createWheel();
            }

            function createWheel() {
                const wheelFragment = document.createDocumentFragment();
                WHEEL_NUMBERS_ORDER.forEach((num, i) => {
                    const numberEl = document.createElement('div');
                    numberEl.classList.add('wheel-number');
                    if (RED_NUMBERS.includes(num)) numberEl.classList.add('red');
                    else if (BLACK_NUMBERS.includes(num)) numberEl.classList.add('black');
                    else numberEl.classList.add('green');
                    
                    numberEl.textContent = num;
                    
                    const angle = (i / WHEEL_NUMBERS_ORDER.length) * 360;
                    const radius = '130px'; // Wheel radius is 150px, place numbers slightly inside
                    
                    numberEl.style.transform = `rotate(${angle}deg) translate(0, -${radius}) rotate(-${angle}deg)`;
                    wheelFragment.appendChild(numberEl);
                });
                wheel.appendChild(wheelFragment);
            }

            function createBettingBoard() {
                bettingGrid.innerHTML = '';
                const fragment = document.createDocumentFragment();
                const zero = document.createElement('div');
                zero.className = 'bet-spot zero';
                zero.dataset.betType = 'single_0';
                zero.innerHTML = '0<span class="chip-display" id="chip-display-single_0"></span>';
                fragment.appendChild(zero);

                for (let i = 1; i <= 36; i++) {
                    const numberSpot = document.createElement('div');
                    numberSpot.classList.add('bet-spot');
                    if (RED_NUMBERS.includes(i)) numberSpot.classList.add('red-area');
                    if (BLACK_NUMBERS.includes(i)) numberSpot.classList.add('black-area');
                    const row = 3 - ((i - 1) % 3);
                    const col = Math.floor((i - 1) / 3) + 2;
                    numberSpot.style.gridRow = `${row}`;
                    numberSpot.style.gridColumn = `${col}`;
                    numberSpot.dataset.betType = `single_${i}`;
                    numberSpot.innerHTML = `${i}<span class="chip-display" id="chip-display-single_${i}"></span>`;
                    fragment.appendChild(numberSpot);
                }

                for (let i = 1; i <= 3; i++) {
                    const colSpot = document.createElement('div');
                    colSpot.className = 'bet-spot col-btn';
                    colSpot.style.gridRow = `${4 - i}`;
                    colSpot.dataset.betType = `column_${i}`;
                    colSpot.innerHTML = `2-1<span class="chip-display" id="chip-display-column_${i}"></span>`;
                    fragment.appendChild(colSpot);
                }

                for (let i = 1; i <= 3; i++) {
                    const dozenSpot = document.createElement('div');
                    dozenSpot.className = 'bet-spot dozen';
                    dozenSpot.style.gridRow = '4';
                    dozenSpot.style.gridColumn = `${(i-1)*4 + 2} / span 4`;
                    dozenSpot.dataset.betType = `dozen_${i}`;
                    dozenSpot.innerHTML = `${i === 1 ? '1st' : i === 2 ? '2nd' : '3rd'} 12<span class="chip-display" id="chip-display-dozen_${i}"></span>`;
                    fragment.appendChild(dozenSpot);
                }
                
                const outsideBets = [
                    { type: 'low', text: '1-18' }, { type: 'even', text: 'EVEN' }, { type: 'red', text: '◆', class: 'red-area' },
                    { type: 'black', text: '◆', class: 'black-area' }, { type: 'odd', text: 'ODD' }, { type: 'high', text: '19-36' }
                ];
                outsideBets.forEach((bet, i) => {
                    const betSpot = document.createElement('div');
                    betSpot.className = 'bet-spot outside-bet';
                    if (bet.class) betSpot.classList.add(bet.class);
                    betSpot.style.gridRow = '5';
                    betSpot.style.gridColumn = `${i*2 + 2} / span 2`;
                    betSpot.dataset.betType = bet.type;
                    betSpot.innerHTML = `${bet.text}<span class="chip-display" id="chip-display-${bet.type}"></span>`;
                    fragment.appendChild(betSpot);
                });
                bettingGrid.appendChild(fragment);
            }
            
            initializeGame();

            // --- Event Listeners ---
            chipsContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('chip')) {
                    document.querySelector('.chip.selected').classList.remove('selected');
                    e.target.classList.add('selected');
                    selectedChipValue = parseInt(e.target.dataset.value);
                }
            });

            bettingGrid.addEventListener('click', (e) => {
                const betSpot = e.target.closest('.bet-spot');
                if (betSpot) {
                    const betType = betSpot.dataset.betType;
                    socket.emit('place_bet', { bet_type: betType, amount: selectedChipValue });
                }
            });

            document.getElementById('repeat-bet-btn').addEventListener('click', () => socket.emit('repeat_bet'));
            document.getElementById('clear-bets-btn').addEventListener('click', () => socket.emit('clear_bets'));

            // --- SocketIO Handlers ---
            socket.on('connect', () => console.log('Connected to server'));
            socket.on('game_state', (data) => updateBalance(data.balance));
            socket.on('balance_update', (data) => updateBalance(data.balance));

            socket.on('bet_placed', (data) => {
                const chipDisplay = document.getElementById(`chip-display-${data.bet_type}`);
                if (chipDisplay) {
                    chipDisplay.textContent = `$${data.total_bet_on_type}`;
                    chipDisplay.classList.add('visible');
                }
            });
            
            socket.on('bets_cleared', () => {
                document.querySelectorAll('.chip-display').forEach(d => {
                    d.textContent = '';
                    d.classList.remove('visible');
                });
            });

            socket.on('timer_update', (data) => {
                timerDisplay.style.color = (data.countdown <= 5 && !data.spinning) ? 'var(--chip-red)' : 'white';
                if (data.spinning) {
                    timerDisplay.textContent = "Spinning...";
                } else if (data.countdown <= 5) {
                    timerDisplay.textContent = `Bets Closed`;
                } else {
                    timerDisplay.textContent = `Spin in: ${data.countdown}`;
                }
            });
            
            socket.on('start_spin', (data) => {
                winNumDisplay.textContent = '??';
                let flickerSpeed = 50;
                clearInterval(numberChangeInterval);
                const flicker = () => {
                    winNumDisplay.textContent = Math.floor(Math.random() * 37);
                    flickerSpeed *= 1.05;
                    if (flickerSpeed < 500) {
                        setTimeout(flicker, flickerSpeed);
                    }
                };
                flicker();
            });

            socket.on('spin_result', (data) => {
                const { winning_number, wheel_position } = data;
                const degreesPerSlot = 360 / WHEEL_NUMBERS_ORDER.length;
                const randomOffset = (Math.random() - 0.5) * degreesPerSlot * 0.8;
                const targetAngle = 360 - (wheel_position * degreesPerSlot + randomOffset);
                const fullSpins = 360 * (5 + Math.floor(Math.random() * 3));
                
                currentRotation = (Math.floor(currentRotation / 360) + 1) * 360 + fullSpins + targetAngle;
                wheel.style.transform = `rotate(${currentRotation}deg)`;
                
                setTimeout(() => {
                    clearInterval(numberChangeInterval);
                    winNumDisplay.textContent = winning_number;
                    updateHistory(winning_number);
                    socket.emit('payout_complete');
                }, 4000); // Wait for wheel to settle
            });

            socket.on('payout_result', (data) => {
                const { balance, net_change, win_details } = data;
                document.querySelectorAll('.bet-spot.winning').forEach(el => el.classList.remove('winning'));
                
                Object.keys(win_details).forEach(bet_key => {
                    const spot = document.querySelector(`[data-bet-type="${bet_key}"]`);
                    if (spot) spot.classList.add('winning');
});

                if (net_change > 0) {
                    showNotification(`You won $${net_change}!`, 'win');
                } else if (net_change < 0) {
                    showNotification(`You lost $${Math.abs(net_change)}`, 'loss');
                } else {
                    showNotification('Push. Your bet was returned.', 'error');
                }
                updateBalance(balance);

                setTimeout(() => {
                    document.querySelectorAll('.chip-display').forEach(d => { d.textContent = ''; d.classList.remove('visible'); });
                    document.querySelectorAll('.bet-spot.winning').forEach(el => el.classList.remove('winning'));
                }, 3000);
            });

            socket.on('error', (data) => showNotification(data.message, 'error'));

            // --- UI Helper Functions ---
            function updateBalance(newBalance) {
                balanceDisplay.textContent = `$${newBalance}`;
            }

            function showNotification(message, type) {
                const notification = document.getElementById('notification');
                notification.textContent = message;
                notification.className = `notification show ${type}`;
                setTimeout(() => {
                    notification.classList.remove('show');
                }, 3000);
            }

            function updateHistory(number) {
                history.unshift(number);
                if (history.length > 15) history.pop();
                
                historyBar.innerHTML = '';
                history.forEach(num => {
                    const el = document.createElement('div');
                    el.classList.add('history-number');
                    el.textContent = num;
                    if (RED_NUMBERS.includes(num)) el.classList.add('red');
                    else if (BLACK_NUMBERS.includes(num)) el.classList.add('black');
                    else el.classList.add('green');
                    historyBar.appendChild(el);
                });
            }
        });
    </script>
</body>
</html>
"""

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting Flask Roulette server...")
    print("Open http://127.0.0.1:5000 in your browser.")
    socketio.run(app, host='0.0.0.0', port=5000)