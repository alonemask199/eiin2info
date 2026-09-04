from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)
app.json.ensure_ascii = False

CSRF_TOKEN = 'FYdlvws4yxuNHAUXRaOXLRG1WGYsclc-uNAWXja4RHm7YCERV2tTpJgluf620W_IkrhILwj5GeW6EjPvoM3j7qdJRNZoJw1Tjwc8ovOZo841'
COOKIE = f'__RequestVerificationToken_L2VtaXM1=1DqrczM4sG0NP9yE0-nyvq0oDK5LZ1QnI1ZWFIQEVd89sInfrE7ojetoO5oC8WysTs2ZrXbkhxJldFZbxv1_fJFCgvtiMU_2jOV6yO2BxSg1; CSRF-TOKEN={CSRF_TOKEN}'

# ছবি এক্সট্র্যাক্ট করার ফাংশন
def extract_image_url(image_html):
    if not image_html or image_html == "-":
        return None
    # HTML ট্যাগ থেকে src লিংক খুঁজে বের করা
    match = re.search(r'src=[\'"]([^\'"]+)[\'"]', image_html)
    if match:
        path = match.group(1)
        if path.startswith('http'):
            return path
        return f"https://emis.gov.bd{path}"
    return None

@app.route('/find', methods=['GET'])
def get_teacher_details():
    eiin = request.args.get('eiin', '').strip()

    if not eiin.isdigit():
        return jsonify({
            'success': False,
            'error': 'Valid eiin parameter is required'
        }), 400

    url = 'https://emis.gov.bd/emis/Portal/GetTeacherDetails'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 15; N76 Build/AP3A.240905.015.A2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7977.64 Mobile Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-CSRF-Token': CSRF_TOKEN,
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://emis.gov.bd',
        'Referer': 'https://emis.gov.bd/EMIS/portalone',
        'Cookie': COOKIE
    }

    payload = {
        'instituteId': '',
        'EIIN': eiin,
        'isTeacher': ''
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=30)
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 502

    try:
        data = response.json()
        
        # প্রতিজন শিক্ষকের ছবির লিংক ক্লিন ও ফুল ইউআরএল (Full URL) বানানো
        if isinstance(data, list):
            for item in data:
                raw_image = item.get('Image', '')
                item['ImageUrl'] = extract_image_url(raw_image)  # সরাসরি ছবির ফুল লিংক
                # অতিরিক্ত কোটেশন যেমন '20-May-1978' ক্লিন করা
                if 'DateofBirth' in item and item['DateofBirth']:
                    item['DateofBirth'] = item['DateofBirth'].replace("'", "")
                
        return jsonify(data), response.status_code
    except ValueError:
        return jsonify({
            'success': True,
            'response': response.text
        }), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
