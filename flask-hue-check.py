from flask import Flask, request, jsonify
import requests
import gunicorn


app = Flask(__name__)

def search_string_on_website(url, wallet_address):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            text_content = response.text

            updated_text_content = text_content.replace('"miner_id":"THEIRWALLETADDRESS"', f'"miner_id":"{wallet_address}"')

            if wallet_address in updated_text_content:
                info = extract_info(updated_text_content, wallet_address)
                global_total_count = calculate_global_total_count(updated_text_content)
                total_count = calculate_total_count(info)
                percentage = calculate_percentage(total_count, global_total_count)
                statement = generate_mining_power_statement(percentage)
                equivalent_value = (percentage * 500000) / 100

                return {
                    "info": info,
                    "global_total_24h_count": global_total_count,
                    "your_total_24h_count": total_count,
                    "percentage": percentage,
                    "statement": statement,
                    "equivalent_value": equivalent_value
                }
            else:
                return {'error': 'Exact match not found on the website'}
        else:
            return {'error': f'Request to {url} failed with status code {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'error': f'An error occurred: {e}'}

# Existing functions

def extract_info(text_content, wallet_address):
    start_index = text_content.find(wallet_address) + len(wallet_address)
    end_index = text_content.find('"miner_id"', start_index)
    info = text_content[start_index:end_index]
    info = info.replace(',', ',\n').rstrip(',').replace('{', '')
    return info

def calculate_total_count(info):
    image_count = int(info.split('"last_24_hours_image_count":"')[1].split('"')[0])
    text_count = int(info.split('"last_24_hours_text_count":"')[1].split('"')[0])
    total_count = image_count + text_count
    return total_count

def calculate_global_total_count(text_content):
    last_24_hours_image_count = int(text_content.split('"last24HrsImageCount":')[1].split(',')[0])
    last_24_hours_text_count = int(text_content.split('"last24HrsTextCount":')[1].split(',')[0])
    global_total_count = last_24_hours_image_count + last_24_hours_text_count
    return global_total_count

def calculate_percentage(total_count, global_total_count):
    percentage = (total_count / global_total_count) * 100
    return percentage

def generate_mining_power_statement(percentage):
    return f"Your wallet represents {percentage:.2f}% of the Heurist testnet mining power!"

@app.route('/stats', methods=['GET'])
def get_stats():
    url = "https://d2hfhz0c37x28y.cloudfront.net/prod/stats?details=true"
    wallet_address = request.args.get('wallet_address').lower()
    result = search_string_on_website(url, wallet_address)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
