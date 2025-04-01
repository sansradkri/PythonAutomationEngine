from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import subprocess
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://automation_user:yourpassword@localhost/python_automation_engine'
db = SQLAlchemy(app)

class ScriptResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    script_name = db.Column(db.String(100), nullable=False)
    trigger_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    result_status = db.Column(db.String(50), nullable=False)

    def __init__(self, script_name, trigger_time, duration_minutes, result_status):
        self.script_name = script_name
        self.trigger_time = trigger_time
        self.duration_minutes = duration_minutes
        self.result_status = result_status

@app.route('/run_scripts', methods=['POST'])
def run_scripts():
    scripts_path = 'scripts'
    if not os.path.exists(scripts_path):
        return jsonify({'message': 'Scripts folder not found', 'status': 'error'})

    scripts = [f for f in os.listdir(scripts_path) if os.path.isfile(os.path.join(scripts_path, f))]
    for script in scripts:
        trigger_time = datetime.datetime.now()
        start_time = datetime.datetime.now()
        process = subprocess.Popen(['python', os.path.join(scripts_path, script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        end_time = datetime.datetime.now()
        duration_minutes = (end_time - start_time).seconds // 60
        result_status = 'success' if process.returncode == 0 else 'failed'

        # Save result to database
        new_result = ScriptResult(script_name=script, trigger_time=trigger_time, duration_minutes=duration_minutes, result_status=result_status)
        db.session.add(new_result)
        db.session.commit()

    return jsonify({'message': 'Scripts executed successfully', 'status': 'success'})

@app.route('/save_script_result', methods=['POST'])
def save_script_result():
    data = request.get_json()
    new_result = ScriptResult(
        script_name=data['script_name'],
        trigger_time=datetime.datetime.strptime(data['trigger_time'], '%Y-%m-%dT%H:%M:%S'),
        duration_minutes=data['duration_minutes'],
        result_status=data['result_status']
    )
    db.session.add(new_result)
    db.session.commit()
    return jsonify({'message': 'Result saved successfully', 'status': 'success'})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)