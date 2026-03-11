from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import random
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Load country data
DATA_FILE = Path(__file__).parent / 'data' / 'game_data_with_flags.json'

def load_country_data():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        # Convert array to dictionary with country names as keys
        return {item['country']: {
            'gdp': item.get('GDP', 'N/A'),
            'flag': item.get('flag_url', ''),
            'top_export': item.get('top_export', 'N/A')
        } for item in data if 'country' in item}

def filter_countries_by_difficulty(data, difficulty):
    if difficulty == 'easy':
        # Filter for countries with GDP > $500B
        return {country: info for country, info in data.items() 
                if isinstance(info['gdp'], (int, float)) and info['gdp'] > 500_000_000_000}
    elif difficulty == 'medium':
        # Filter for countries with GDP > $10B
        return {country: info for country, info in data.items() 
                if isinstance(info['gdp'], (int, float)) and info['gdp'] > 10_000_000_000}
    else:  # hard mode
        return data

def get_random_countries(count=5, difficulty='medium'):
    data = load_country_data()
    filtered_data = filter_countries_by_difficulty(data, difficulty)
    
    if not filtered_data:
        return {
            'countries': [],
            'gdps': [],
            'flags': [],
            'exports': [],
            'correct_matches': {}
        }
    
    selected_countries = random.sample(list(filtered_data.items()), min(count, len(filtered_data)))
    
    # Create shuffled columns
    countries = [country for country, _ in selected_countries]
    gdps = [data[country]['gdp'] for country in countries]
    flags = [data[country]['flag'] for country in countries]
    exports = [data[country]['top_export'] for country in countries]
    
    random.shuffle(countries)
    random.shuffle(gdps)
    random.shuffle(flags)
    random.shuffle(exports)
    
    return {
        'countries': countries,
        'gdps': gdps,
        'flags': flags,
        'exports': exports,
        'correct_matches': {
            country: {
                'gdp': data[country]['gdp'],
                'flag': data[country]['flag'],
                'top_export': data[country]['top_export']
            }
            for country in countries
        }
    }

@app.route('/api/game', methods=['GET'])
def get_game_data():
    difficulty = request.args.get('difficulty', 'medium')
    return jsonify(get_random_countries(difficulty=difficulty))

@app.route('/api/validate_matches', methods=['POST'])
def validate_matches():
    data = request.json
    matches = data['matches']
    correct_matches = data['correct_matches']
    
    score = 0
    feedback = {}
    
    for country, match in matches.items():
        correct = correct_matches[country]
        country_score = 0
        country_feedback = {}
        
        for field in ['gdp', 'flag', 'top_export']:
            if match[field] == correct[field]:
                country_score += 1
                country_feedback[field] = 'correct'
            else:
                country_feedback[field] = 'incorrect'
        
        score += country_score
        feedback[country] = {
            'score': country_score,
            'feedback': country_feedback
        }
    
    return jsonify({
        'total_score': score,
        'max_score': len(matches) * 3,
        'feedback': feedback
    })

if __name__ == '__main__':
    app.run(debug=False, port=5001)