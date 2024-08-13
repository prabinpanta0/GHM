from flask import Flask, render_template, request, jsonify
from form_filler import FormFiller
import threading

app = Flask(__name__)
form_filler = FormFiller()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_form_filling():
    url = request.json['url']
    iterations = int(request.json['iterations'])
    
    def run_form_filler():
        form_filler.fill_form_in_parallel(url, iterations)
    
    form_filler.total_iterations = iterations
    form_filler.iterations_left = iterations
    form_filler.responses_sent = 0
    form_filler.errors = 0
    form_filler.environment_status = []
    
    thread = threading.Thread(target=run_form_filler)
    thread.start()
    
    return jsonify({"message": "Form filling started"})

@app.route('/stop', methods=['POST'])
def stop_form_filling():
    form_filler.stop()
    return jsonify({"message": "Form filling stopped"})

@app.route('/status', methods=['GET'])
def get_status():
    with form_filler.lock:
        if form_filler.responses_sent == 0 and form_filler.errors == 0 and form_filler.iterations_left == form_filler.total_iterations:
            # This condition checks if everything is still initializing
            return jsonify({
                "total_iterations": form_filler.total_iterations,
                "responses_sent": None,  # Return None instead of 0 to indicate uninitialized
                "errors": None,
                "iterations_left": form_filler.iterations_left,
                "environment_status": None
            })
        else:
            return jsonify({
                "total_iterations": form_filler.total_iterations,
                "responses_sent": form_filler.responses_sent,
                "errors": form_filler.errors,
                "iterations_left": form_filler.iterations_left,
                "environment_status": list(form_filler.environment_status)
            })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)