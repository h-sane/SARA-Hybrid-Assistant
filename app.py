# app.py

from flask import Flask, request, jsonify, render_template
from host_agent import HostAgent

# Initialize the Flask web server
app = Flask(__name__)

# Create a single, persistent instance of our HostAgent
sara_os = HostAgent()

@app.route('/')
def serve_index():
    """Serves the main HTML user interface."""
    return render_template('index.html')

@app.route('/api/command', methods=['POST'])
def handle_command():
    """The API endpoint that the browser sends commands to."""
    try:
        data = request.json
        user_command = data.get('command', '')

        if not user_command:
            return jsonify({"status": "error", "response": "No command provided."}), 400

        # Pass the command to the HostAgent and get the result
        result = sara_os.process_user_command(user_command)
        
        # The HostAgent's response is already perfectly formatted for the frontend
        return jsonify({"status": "success", "response": result.get("response")}), 200

    except Exception as e:
        print(f"An error occurred in the /api/command endpoint: {e}")
        return jsonify({"status": "error", "response": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    # This starts the web server
    app.run(debug=True)