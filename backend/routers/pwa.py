from flask import Blueprint, render_template, jsonify, Response
from flask_login import login_required

bp = Blueprint('pwa', __name__)

@bp.route('/app')
@login_required
def app_index():
    return render_template('pwa/app.html')

@bp.route('/manifest.json')
def manifest():
    data = {
        "name": "Nobre Elegancy Noivas",
        "short_name": "Nobre Elegancy",
        "start_url": "/app",
        "display": "standalone",
        "background_color": "#FAF6F7",
        "theme_color": "#B76E79",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    import json
    return Response(json.dumps(data), mimetype='application/json')

@bp.route('/sw.js')
def service_worker():
    js = "self.addEventListener('fetch', function(event) {});"
    return Response(js, mimetype='application/javascript')
