from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for local development to allow the HTML file to make a request to the server
CORS(app)

# This function calculates a "score" for each bank based on the input ratios using the RANK SUM METHOD.
# The overall rank is determined by the lowest sum of individual metric ranks.


def calculate_points(bank_data):
    # --- 1. Define Metric Groups based on User Instructions ---
    # LDR is explicitly excluded from ranking calculation, only used for display.

    # Higher value is better -> Lower Rank is better
    HIGHER_IS_BETTER = ['kppm', 'roa', 'roe', 'nim']

    # Lower value is better -> Lower Rank is better
    LOWER_IS_BETTER = ['ab', 'apb', 'ckpn',
                       'npl_gross', 'npl_net', 'bopo', 'cir']

    # The set of metrics used for calculating the total rank sum
    RANKED_METRICS = HIGHER_IS_BETTER + LOWER_IS_BETTER

    # All inputs required, including LDR
    ALL_INPUT_METRICS = RANKED_METRICS + ['ldr']

    banks_processed = []

    # --- 2. Pre-process Data and Check Validity ---
    for bank in bank_data:
        # Initialize dictionary to store final data and individual ranks
        processed_bank = {'name': bank['name'], 'ldr': 0.0, 'ranks': {}}
        try:
            # Convert all metric strings to floats
            for metric in ALL_INPUT_METRICS:
                processed_bank[metric] = float(bank[metric])

            # Store LDR for the result table display
            processed_bank['ldr'] = processed_bank['ldr']

            banks_processed.append(processed_bank)
        except (ValueError, KeyError):
            # Handle cases where input data is invalid or missing
            return jsonify({'error': 'Invalid input data. Please check all fields.'}), 400

    if not banks_processed:
        return jsonify({'error': 'No valid bank data provided.'}), 400

    # --- 3. Calculate Ranks for each Metric (Standard Competition Ranking) ---
    for metric in RANKED_METRICS:
        is_higher_better = metric in HIGHER_IS_BETTER

        # Create a list of tuples: (metric_value, original_index) for sorting
        sortable_list = [(bank[metric], i)
                         for i, bank in enumerate(banks_processed)]

        # Sort: descending if higher is better, ascending if lower is better
        sortable_list.sort(key=lambda x: x[0], reverse=is_higher_better)

        # Assign ranks with tie handling (e.g., if ranks are 2, 2, the next rank is 4)
        current_rank = 1

        for i, (value, original_index) in enumerate(sortable_list):

            # If the current value is the same as the previous one, use the same rank
            if i > 0 and value == sortable_list[i-1][0]:
                pass  # current_rank remains the same
            else:
                # Value is new or it's the first item; assign the next available rank position
                current_rank = i + 1

            banks_processed[original_index]['ranks'][metric] = current_rank

    # --- 4. Calculate Total Rank Sum ---
    # Only sums the ranks from the metrics in RANKED_METRICS
    for bank in banks_processed:
        total_rank_sum = sum(bank['ranks'].values())
        bank['total_rank_sum'] = total_rank_sum
        # Remove temporary rank details
        del bank['ranks']

    # --- 5. Final Ranking (Lowest Total Rank Sum Wins) ---
    # Sort banks by total_rank_sum in ascending order (lowest sum = Rank 1)
    banks_processed.sort(key=lambda x: x['total_rank_sum'], reverse=False)

    # --- 6. Assign Final Rank and Format Output ---
    final_ranked_banks = []

    for i, bank in enumerate(banks_processed):
        final_ranked_banks.append({
            'name': bank['name'],
            'ldr': bank['ldr'],  # LDR value is included here for display
            # The rank sum is now displayed as the 'Total Points'
            'total_points': bank['total_rank_sum'],
            'rank': i + 1
        })

    return final_ranked_banks


@app.route('/')
def home():
    """Serves the main HTML page. (Note: this is only needed if using Flask to serve the HTML)"""
    # For the canvas environment, this is often mocked or ignored.
    return "This server is only for calculation endpoints."


@app.route('/calculate', methods=['POST'])
def calculate_ranking():
    """Receives bank data, calculates ranks, sums them, sorts, and returns the results."""
    # Get JSON data from the request body
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({'error': 'Invalid request format. Expected a list of bank data.'}), 400

    # Calculate points (rank sum) and sort the banks
    ranked_banks = calculate_points(data)

    # If calculate_points returned an error tuple, return it directly
    if isinstance(ranked_banks, tuple):
        return ranked_banks

    # Return the sorted data as a JSON response
    return jsonify(ranked_banks)


if __name__ == '__main__':
    # Run the Flask application on localhost at the specified port
    app.run(host='0.0.0.0', port=5000)
