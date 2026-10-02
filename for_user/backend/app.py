from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import uuid
import json
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Allow all for now during dev, usually restrict to frontend port

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'network_diag_user.db'))
ADMIN_BACKEND_URL = os.environ.get('ADMIN_BACKEND_URL', 'http://localhost:5425')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class UserTest(db.Model):
    __tablename__ = 'user_tests'
    id = db.Column(db.Integer, primary_key=True)
    session_uuid = db.Column(db.String(36), unique=True, nullable=False)
    target_urls = db.Column(db.JSON, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class DiagnosticReport(db.Model):
    __tablename__ = 'diagnostic_reports'
    id = db.Column(db.Integer, primary_key=True)
    session_uuid = db.Column(db.String(36), db.ForeignKey('user_tests.session_uuid'), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    status_code = db.Column(db.String(50), nullable=True) # Integer or String as per req
    error_message = db.Column(db.Text, nullable=True)
    client_info = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Routes
@app.route('/api/check-session/<session_uuid>', methods=['GET'])
def check_session(session_uuid):
    ut = UserTest.query.filter_by(session_uuid=session_uuid).first()
    if not ut:
        # Try to fetch from Admin Backend (Port 5425)
        try:
            import requests
            admin_res = requests.get(f'{ADMIN_BACKEND_URL}/api/check-session/{session_uuid}', timeout=5)
            if admin_res.status_code == 200:
                return jsonify(admin_res.json())
        except Exception as e:
            print(f"Failed to fetch from admin: {e}")
        
        return jsonify({'error': 'Session not found'}), 404
        
    # Check expiration (using GMT+8 logic)
    now_gmt8 = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    if ut.expires_at < now_gmt8:
        return jsonify({'error': 'Session expired'}), 403
        
    return jsonify({
        'session_uuid': ut.session_uuid,
        'target_urls': ut.target_urls,
        'expires_at': ut.expires_at.isoformat()
    })



@app.route('/api/admin/sessions', methods=['GET'])
def list_sessions():
    sessions = UserTest.query.order_by(UserTest.expires_at.desc()).all()
    results = []
    for s in sessions:
        results.append({
            'session_uuid': s.session_uuid,
            'target_urls': s.target_urls,
            'expires_at': s.expires_at.isoformat()
        })
    return jsonify(results)

@app.route('/api/admin/sessions', methods=['POST'])
def create_session():
    data = request.json
    raw_targets = data.get('target_urls', [])
    if not isinstance(raw_targets, list) or not raw_targets:
        return jsonify({'error': 'target_urls must be a non-empty list'}), 400
    
    # Normalize targets to [{name, url}]
    targets = []
    for t in raw_targets:
        if isinstance(t, str):
            targets.append({'name': t, 'url': t})
        elif isinstance(t, dict) and 'url' in t:
            targets.append({
                'name': t.get('name', t['url']), 
                'url': t['url'],
                'classification': t.get('classification', ''),
                'checking_which_content': t.get('checking_which_content', '')
            })
            
    u = uuid.uuid4()
    # Use GMT+8 as requested
    gmt8 = datetime.timezone(datetime.timedelta(hours=8))
    now_gmt8 = datetime.datetime.now(gmt8)
    # Naive time representing GMT+8
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=8) + datetime.timedelta(hours=data.get('expires_in_hours', 1))
    
    ut = UserTest(
        session_uuid=str(u),
        target_urls=targets,
        expires_at=expires
    )
    db.session.add(ut)
    db.session.commit()
    print(f"Created session: {u}")
    return jsonify({'session_uuid': str(u)}), 201

@app.route('/api/admin/sessions/<session_uuid>', methods=['DELETE'])
def delete_session(session_uuid):
    ut = UserTest.query.filter_by(session_uuid=session_uuid).first()
    if not ut:
        return jsonify({'error': 'Session not found'}), 404
    
    # Manually delete related reports first to avoid constraint errors
    DiagnosticReport.query.filter_by(session_uuid=session_uuid).delete()
    db.session.delete(ut)
    db.session.commit()
    return jsonify({'status': 'deleted'}), 200

@app.route('/api/admin/sessions/<session_uuid>', methods=['PUT'])
def update_session(session_uuid):
    data = request.json
    raw_targets = data.get('target_urls')
    if not isinstance(raw_targets, list) or not raw_targets:
        return jsonify({'error': 'target_urls must be a non-empty list'}), 400
        
    ut = UserTest.query.filter_by(session_uuid=session_uuid).first()
    if not ut:
        return jsonify({'error': 'Session not found'}), 404

    # Normalize targets to [{name, url}]
    targets = []
    for t in raw_targets:
        if isinstance(t, str):
            targets.append({'name': t, 'url': t})
        elif isinstance(t, dict) and 'url' in t:
            targets.append({
                'name': t.get('name', t['url']), 
                'url': t['url'],
                'classification': t.get('classification', ''),
                'checking_which_content': t.get('checking_which_content', '')
            })
        
    ut.target_urls = targets
    db.session.commit()
    return jsonify({'status': 'updated'}), 200

@app.route('/api/submit-report', methods=['POST'])
def submit_report():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Basic validation
    required_fields = ['session_uuid', 'url']
    for field in required_fields:
        if field not in data:
             return jsonify({'error': f'Missing field: {field}'}), 400

    report = DiagnosticReport(
        session_uuid=data['session_uuid'],
        url=data['url'],
        status_code=str(data.get('status_code')),
        error_message=data.get('error_message'),
        client_info=data.get('client_info')
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'status': 'success', 'report_id': report.id}), 201

# Helper to init db
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")

# Helper to create a dummy test session
@app.cli.command("create-test-session")
def create_test_session():
    u = uuid.uuid4()
    # Adding some test URLs including expected 200, 404, and maybe a delay one if we could, 
    # but for now just standard public ones and localhost.
    test_urls = [
        {"name": "Google", "url": "https://www.google.com", "classification": "Search", "checking_which_content": "Main Page"},
        {"name": "Example", "url": "https://www.example.com", "classification": "Demo", "checking_which_content": "Content"},
        {"name": "404 Test", "url": "http://httpstat.us/404", "classification": "Test", "checking_which_content": "Status"},
        {"name": "302 Test", "url": "http://httpstat.us/302", "classification": "Test", "checking_which_content": "Redirect"},
        {"name": "500 Test", "url": "http://httpstat.us/500", "classification": "Test", "checking_which_content": "Error"},
        {"name": "Local Invalid", "url": "http://localhost:5425/api/check-session/invalid", "classification": "Local", "checking_which_content": "API"}
    ]
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    
    ut = UserTest(
        session_uuid=str(u),
        target_urls=test_urls,
        expires_at=expires
    )
    db.session.add(ut)
    db.session.commit()
    print(f"Created session: {u}")

class DiagnosticHar(db.Model):
    __tablename__ = 'diagnostic_hars'
    id = db.Column(db.Integer, primary_key=True)
    session_uuid = db.Column(db.String(36), nullable=False)
    har_content = db.Column(db.JSON, nullable=False)
    summary = db.Column(db.JSON, nullable=False)
    client_info = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@app.route('/api/upload-har', methods=['POST'])
def upload_har():
    data = request.json
    if not data:
         return jsonify({'error': 'No data provided'}), 400

    # Determine HAR root (wrapped vs direct)
    har_root = data.get('har', data)
    
    if 'log' not in har_root:
        return jsonify({'error': 'Invalid HAR format'}), 400
    
    entries = har_root['log'].get('entries', [])
    
    # Analysis
    stats = {
        'total': len(entries),
        'status_counts': {},
        'avg_time': 0,
        'errors': 0
    }
    
    total_time = 0
    for entry in entries:
        resp = entry.get('response', {})
        status = resp.get('status', 0)
        status_text = resp.get('statusText', '')
        
        # Normailize status for bucketing
        if status == 0:
            key = 'CORS/Network Error'
            stats['errors'] += 1
        else:
            key = str(status)
            if status >= 400:
                stats['errors'] += 1
        
        stats['status_counts'][key] = stats['status_counts'].get(key, 0) + 1
        total_time += entry.get('time', 0)
        
    if stats['total'] > 0:
        stats['avg_time'] = round(total_time / stats['total'], 2)
        
    session_uuid = data.get('session_uuid', 'unknown')
    client_info = data.get('client_info', {})
    
    report = DiagnosticHar(
        session_uuid=session_uuid,
        har_content=har_root,
        summary=stats,
        client_info=client_info
    )
    
    db.session.add(report)
    db.session.commit()
    
    # Forward to Admin Backend (Port 5425) so it appears in the Admin UI
    try:
        import requests
        # We send the original data payload
        requests.post(f'{ADMIN_BACKEND_URL}/api/upload-har', json=data, timeout=5)
    except Exception as e:
        print(f"Failed to forward HAR to admin: {e}")
    
    return jsonify({'status': 'uploaded', 'id': report.id, 'summary': stats}), 201

@app.route('/api/admin/hars', methods=['GET'])
def list_hars():
    hars = DiagnosticHar.query.order_by(DiagnosticHar.created_at.desc()).all()
    results = []
    for h in hars:
        results.append({
            'id': h.id,
            'session_uuid': h.session_uuid,
            'created_at': h.created_at.isoformat(),
            'summary': h.summary
        })
    return jsonify(results)

@app.route('/api/admin/hars/<int:har_id>', methods=['GET'])
def get_har(har_id):
    har = DiagnosticHar.query.get(har_id)
    if not har:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': har.id,
        'session_uuid': har.session_uuid,
        'created_at': har.created_at.isoformat(),
        'summary': har.summary,
        'har': har.har_content
    })

if __name__ == '__main__':
    # Initial DB creation handling within app context if run directly (though CLI is better)
    with app.app_context():
        # This is just for dev convenience to ensure tables exist
        pass
    app.run(host='0.0.0.0', port=5427)
