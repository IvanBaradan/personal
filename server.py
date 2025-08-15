from flask import Flask, request, jsonify, render_template_string
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker
import random
from datetime import datetime

app = Flask(__name__)

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///cat_game.db', echo=False)
Session = sessionmaker(bind=engine)

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    coins = Column(Integer, default=0)
    join_time = Column(DateTime, default=datetime.utcnow)

class Coin(Base):
    __tablename__ = 'coins'
    
    id = Column(Integer, primary_key=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)

# Create tables
Base.metadata.create_all(engine)

# Initialize coin if not exists
def init_coin():
    session = Session()
    if session.query(Coin).count() == 0:
        coin = Coin(x=random.randint(0, 15), y=random.randint(0, 11))
        session.add(coin)
        session.commit()
    session.close()

init_coin()

@app.route('/api/join', methods=['POST'])
def join_game():
    """API endpoint for bot to create new player"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    username = data.get('username')
    
    if not telegram_id or not username:
        return jsonify({'error': 'Missing telegram_id or username'}), 400
    
    session = Session()
    
    # Check if player already exists
    existing_player = session.query(Player).filter_by(telegram_id=telegram_id).first()
    if existing_player:
        session.close()
        return jsonify({'error': 'Player already exists'}), 400
    
    # Create new player at random position
    player = Player(
        telegram_id=telegram_id,
        username=username,
        x=random.randint(0, 15),
        y=random.randint(0, 11),
        coins=0
    )
    
    session.add(player)
    session.commit()
    session.close()
    
    return jsonify({'success': True, 'message': 'Player joined successfully'})

@app.route('/api/move', methods=['POST'])
def move_player():
    """API endpoint for bot to move player"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    direction = data.get('direction')
    
    if not telegram_id or not direction:
        return jsonify({'error': 'Missing telegram_id or direction'}), 400
    
    session = Session()
    player = session.query(Player).filter_by(telegram_id=telegram_id).first()
    
    if not player:
        session.close()
        return jsonify({'error': 'Player not found'}), 404
    
    # Calculate new position
    new_x, new_y = player.x, player.y
    
    if direction == 'up' and player.y > 0:
        new_y = player.y - 1
    elif direction == 'down' and player.y < 11:
        new_y = player.y + 1
    elif direction == 'left' and player.x > 0:
        new_x = player.x - 1
    elif direction == 'right' and player.x < 15:
        new_x = player.x + 1
    
    # Check if player moved
    if new_x != player.x or new_y != player.y:
        player.x = new_x
        player.y = new_y
        
        # Check for coin collection
        coin = session.query(Coin).filter_by(x=player.x, y=player.y).first()
        if coin:
            player.coins += 1
            session.delete(coin)
            
            # Create new coin at random position
            while True:
                new_coin_x = random.randint(0, 15)
                new_coin_y = random.randint(0, 11)
                
                # Check if position is not occupied by any player
                occupied = session.query(Player).filter_by(x=new_coin_x, y=new_coin_y).first()
                if not occupied:
                    new_coin = Coin(x=new_coin_x, y=new_coin_y)
                    session.add(new_coin)
                    break
    
    session.commit()
    session.close()
    
    return jsonify({'success': True})

@app.route('/api/game_state', methods=['GET'])
def get_game_state():
    """API endpoint for game window to get current state"""
    session = Session()
    
    players = session.query(Player).all()
    coin = session.query(Coin).first()
    
    players_data = []
    for player in players:
        players_data.append({
            'username': player.username,
            'x': player.x,
            'y': player.y,
            'coins': player.coins
        })
    
    coin_data = None
    if coin:
        coin_data = {'x': coin.x, 'y': coin.y}
    
    session.close()
    
    return jsonify({
        'players': players_data,
        'coin': coin_data
    })

@app.route('/leaderboard')
def leaderboard():
    """Leaderboard page"""
    session = Session()
    players = session.query(Player).order_by(Player.coins.desc()).all()
    session.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cat Game Leaderboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .header { text-align: center; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐱 Cat Game Leaderboard 🐱</h1>
        </div>
        <table>
            <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Coins</th>
                <th>Join Time</th>
                <th>Duration</th>
            </tr>
    """
    
    for i, player in enumerate(players, 1):
        duration = datetime.utcnow() - player.join_time
        duration_str = f"{duration.days}d {duration.seconds//3600}h {(duration.seconds%3600)//60}m"
        
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{player.username}</td>
                <td>{player.coins}</td>
                <td>{player.join_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                <td>{duration_str}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html

@app.route('/about')
def about():
    """About page with AI experience"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>About - AI Experience</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .section { margin-bottom: 30px; }
            h2 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .skill { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Experience & Skills</h1>
            </div>
            
            <div class="section">
                <h2>Machine Learning & Deep Learning</h2>
                <div class="skill">
                    <strong>Neural Networks:</strong> Experience with CNN, RNN, LSTM, Transformer architectures
                </div>
                <div class="skill">
                    <strong>Frameworks:</strong> TensorFlow, PyTorch, Keras, Scikit-learn
                </div>
                <div class="skill">
                    <strong>Computer Vision:</strong> Image classification, object detection, segmentation
                </div>
                <div class="skill">
                    <strong>NLP:</strong> Text processing, sentiment analysis, language models
                </div>
            </div>
            
            <div class="section">
                <h2>Natural Language Processing</h2>
                <div class="skill">
                    <strong>Language Models:</strong> GPT, BERT, T5, and custom transformer models
                </div>
                <div class="skill">
                    <strong>Text Processing:</strong> Tokenization, embedding, attention mechanisms
                </div>
                <div class="skill">
                    <strong>Applications:</strong> Chatbots, text generation, translation, summarization
                </div>
            </div>
            
            <div class="section">
                <h2>Data Science & Analytics</h2>
                <div class="skill">
                    <strong>Data Processing:</strong> Pandas, NumPy, data cleaning and preprocessing
                </div>
                <div class="skill">
                    <strong>Visualization:</strong> Matplotlib, Seaborn, Plotly, interactive dashboards
                </div>
                <div class="skill">
                    <strong>Statistics:</strong> Hypothesis testing, A/B testing, statistical modeling
                </div>
            </div>
            
            <div class="section">
                <h2>Software Development</h2>
                <div class="skill">
                    <strong>Languages:</strong> Python, JavaScript, SQL, with focus on AI/ML applications
                </div>
                <div class="skill">
                    <strong>APIs:</strong> RESTful APIs, GraphQL, microservices architecture
                </div>
                <div class="skill">
                    <strong>Deployment:</strong> Docker, cloud platforms, model serving
                </div>
            </div>
            
            <div class="section">
                <h2>Projects & Experience</h2>
                <div class="skill">
                    <strong>Real-world Applications:</strong> Developed AI solutions for various industries
                </div>
                <div class="skill">
                    <strong>Research:</strong> Published papers and contributed to open-source AI projects
                </div>
                <div class="skill">
                    <strong>Teaching:</strong> Mentored students and conducted AI workshops
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
