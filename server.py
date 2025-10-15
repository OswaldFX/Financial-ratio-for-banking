from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='.')
CORS(app)

# --- Calculation Logic (same as before) ---


def calculate_points(bank_data):
    HIGHER_IS_BETTER = ['kppm', 'roa', 'roe', 'nim']
    LOWER_IS_BETTER = ['ab', 'apb', 'ckpn',
                       'npl_gross', 'npl_net', 'bopo', 'cir']
    RANKED_METRICS = HIGHER_IS_BETTER + LOWER_IS_BETTER
    ALL_INPUT_METRICS = RANKED_METRICS + ['ldr']

    banks_processed = []
    for bank in bank_data:
        processed = {'name': bank['name'], 'ldr': 0.0, 'ranks': {}}
        try:
            for metric in ALL_INPUT_METRICS:
                processed[metric] = float(bank[metric])
            processed['ldr'] = processed['ldr']
            banks_processed.append(processed)
        except (ValueError, KeyError):
            return jsonify({'error': 'Invalid input data.'}), 400

    for metric in RANKED_METRICS:
        is_higher = metric in HIGHER_IS_BETTER
        sortable = [(bank[metric], i)
                    for i, bank in enumerate(banks_processed)]
        sortable.sort(key=lambda x: x[0], reverse=is_higher)
        current_rank = 1
        for i, (val, idx) in enumerate(sortable):
            if i > 0 and val == sortable[i - 1][0]:
                pass
            else:
                current_rank = i + 1
            banks_processed[idx]['ranks'][metric] = current_rank

    for bank in banks_processed:
        bank['total_rank_sum'] = sum(bank['ranks'].values())
        del bank['ranks']

    banks_processed.sort(key=lambda x: x['total_rank_sum'])
    final = []
    for i, bank in enumerate(banks_processed):
        final.append({
            'name': bank['name'],
            'ldr': bank['ldr'],
            'total_points': bank['total_rank_sum'],
            'rank': i + 1
        })
    return final


# --- Serve Frontend ---
@app.route('/')
def index():
    return app.send_static_file('index.html')


# --- API Endpoint ---
@app.route('/calculate', methods=['POST'])
def calculate_ranking():
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({'error': 'Invalid request format. Expected a list.'}), 400

    ranked_banks = calculate_points(data)
    if isinstance(ranked_banks, tuple):
        return ranked_banks
    return jsonify(ranked_banks)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
