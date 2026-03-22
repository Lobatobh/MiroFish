"""
MiroFish Backend - Flask应用工厂
"""

import os
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, send_from_directory
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # JSON编码（支持中文）
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # Logger
    logger = setup_logger('mirofish')
    
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)
    
    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Cleanup
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")
    
    # Logs
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"请求体: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"响应: {response.status_code}")
        return response
    
    # APIs
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}

    # ===== SERVIR FRONTEND (CORREÇÃO DO 404) =====
    @app.route('/')
    def serve_frontend():
        return send_from_directory('dist', 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        try:
            return send_from_directory('dist', path)
        except:
            return send_from_directory('dist', 'index.html')
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app
