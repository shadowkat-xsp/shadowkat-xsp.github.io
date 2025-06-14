from flask import Flask, render_template, request, jsonify
from FlightRadar24 import FlightRadar24API
import requests
import json

app = Flask(__name__)
fr_api = FlightRadar24API()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/find-routes', methods=['POST'])
def find_routes():
    data = request.get_json()
    airline_iata = data.get('airline')
    aircraft_type = data.get('aircraft')
    desired_duration_hours = data.get('flight_time')

    if not airline_iata:
        return jsonify({'error': 'Airline IATA code is required.'}), 400

    try:
        airline_flights = fr_api.get_flights(airline=airline_iata)
        
        filtered_flights = []
        for flight in airline_flights:
            # The API might not return all details for all flights, so we need to be careful
            if not all([flight.origin_airport_iata, flight.destination_airport_iata, flight.aircraft_code]):
                continue

            # Filter by aircraft type if provided
            if aircraft_type and flight.aircraft_code.upper() != aircraft_type.upper():
                continue

            # Get detailed flight info for duration
            flight_details = fr_api.get_flight_details(flight)
            flight.set_flight_details(flight_details)

            duration_seconds = flight.time_details.get('scheduled', {}).get('departure') and flight.time_details.get('scheduled', {}).get('arrival') \
                and flight.time_details['scheduled']['arrival'] - flight.time_details['scheduled']['departure']

            if duration_seconds:
                duration_hours = duration_seconds / 3600
                # Filter by duration if provided
                if desired_duration_hours:
                    if abs(duration_hours - float(desired_duration_hours)) > 0.5: # Allow 30min tolerance
                        continue
            elif desired_duration_hours:
                # If we want to filter by time but don't have it, skip.
                continue
            
            filtered_flights.append({
                'callsign': flight.callsign,
                'origin': flight.origin_airport_iata,
                'destination': flight.destination_airport_iata,
                'aircraft': flight.aircraft_code,
                'flight_time': round(duration_hours, 2) if duration_seconds else 'N/A'
            })

        return jsonify(filtered_flights)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/briefing')
def briefing():
    user_id = request.args.get('userid')
    static_id = request.args.get('staticid') # Simbrief seems to use all lowercase for params

    if not user_id and not static_id:
        # Fallback for when the redirect might not contain the params, but a POST body.
        # This is a bit of guesswork based on web standards.
        ofp_json_str = request.form.get('Simbrief_OFP_JSON')
        if ofp_json_str:
            ofp_data = json.loads(ofp_json_str)
            return render_template('briefing.html', ofp=ofp_data, ofp_json=json.dumps(ofp_data, indent=4))
        return "Could not find SimBrief data. Please check your SimBrief API configuration.", 400


    # Recommended method from docs
    fetch_url = f"https://www.simbrief.com/api/xml.fetcher.php?userid={user_id}&staticid={static_id}&json=1"
    
    try:
        response = requests.get(fetch_url)
        response.raise_for_status()
        ofp_data = response.json()
        
        # The 'downloads' section might not be a list, but a dict. Convert it.
        if 'downloads' in ofp_data and isinstance(ofp_data['downloads'], dict):
            ofp_data['downloads'] = [{'name': k, 'url': v} for k, v in ofp_data['downloads'].items()]


        return render_template('briefing.html', ofp=ofp_data, ofp_json=json.dumps(ofp_data, indent=4))

    except requests.exceptions.RequestException as e:
        return f"Error fetching data from SimBrief: {e}", 500
    except json.JSONDecodeError:
        return "Error: Invalid JSON response from SimBrief. Check if the API returned XML instead.", 500

if __name__ == '__main__':
    app.run(debug=True) 