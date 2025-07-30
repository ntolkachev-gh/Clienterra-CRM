from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
# Heroku использует postgres:// вместо postgresql://
database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/clienterra_crm')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Добавляем фильтр для переносов строк
@app.template_filter('nl2br')
def nl2br(value):
    return re.sub(r'\n', '<br>', str(value))

# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    name = db.Column(db.String(100))
    organization = db.Column(db.String(200))
    project_description = db.Column(db.Text)
    user_brief = db.Column(db.Text(length=10000))  # Сырой бриф от пользователя (очень большое поле)
    required_functions = db.Column(db.Text)
    traffic_source = db.Column(db.String(100))
    status = db.Column(db.String(50), default='новый')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = db.relationship('Message', backref='client', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    is_from_bot = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    attachment_path = db.Column(db.String(500))

class BotSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    welcome_message = db.Column(db.Text, default="Привет! Я помогу вам создать идеального Telegram-бота для вашего бизнеса. Расскажите, что вас интересует?")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return render_template('dashboard.html', clients=clients)

@app.route('/client/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    messages = Message.query.filter_by(client_id=client_id).order_by(Message.timestamp.asc()).all()
    return render_template('client_detail.html', client=client, messages=messages)

@app.route('/update_client_status', methods=['POST'])
@login_required
def update_client_status():
    client_id = request.json.get('client_id')
    new_status = request.json.get('status')
    
    client = Client.query.get(client_id)
    if client:
        client.status = new_status
        client.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 404

@app.route('/api/save_final_message', methods=['POST'])
def save_final_message():
    """API endpoint для сохранения финального сообщения пользователя от n8n"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Извлекаем данные из запроса
        user_data = data.get('user', {})
        message_data = data.get('message', {})
        metadata = data.get('metadata', {})
        
        telegram_id = user_data.get('telegram_id')
        message_text = message_data.get('text')
        is_first_message = metadata.get('is_first_message', False)
        
        if not telegram_id or not message_text:
            return jsonify({'error': 'Missing required fields: telegram_id or message text'}), 400
        
        # Ищем или создаем клиента
        client = Client.query.filter_by(telegram_id=telegram_id).first()
        
        if not client:
            # Создаем нового клиента
            client = Client(
                telegram_id=telegram_id,
                name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                status='новый'
            )
            db.session.add(client)
            db.session.flush()  # Получаем ID клиента
        
        # Дополняем user_brief каждым новым сообщением
        if client.user_brief:
            # Если уже есть данные, добавляем новое сообщение с разделителем
            client.user_brief += f"\n\n--- Новое сообщение ---\n{message_text}"
        else:
            # Если это первое сообщение, создаем новый бриф
            client.user_brief = message_text
        
        client.updated_at = datetime.utcnow()
        
        # Сохраняем сообщение в таблицу messages
        message = Message(
            client_id=client.id,
            message_text=message_text,
            is_from_bot=False,
            timestamp=datetime.fromisoformat(message_data.get('timestamp', datetime.utcnow().isoformat()))
        )
        db.session.add(message)
        
        # Обновляем статус клиента если это первое сообщение
        if is_first_message:
            client.status = 'в работе'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'client_id': client.id,
            'message_id': message.id,
            'is_first_message': is_first_message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    bot_settings = BotSettings.query.first()
    if not bot_settings:
        bot_settings = BotSettings()
        db.session.add(bot_settings)
        db.session.commit()
    
    if request.method == 'POST':
        bot_settings.welcome_message = request.form['welcome_message']
        bot_settings.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Настройки сохранены!')
    
    return render_template('settings.html', settings=bot_settings)

@app.route('/api/add_brief', methods=['POST'])
def add_brief():
    """Упрощенный API endpoint для добавления брифа - только telegram_id и text"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        telegram_id = data.get('telegram_id')
        text = data.get('text')
        
        if not telegram_id or not text:
            return jsonify({'error': 'Missing required fields: telegram_id or text'}), 400
        
        # Ищем или создаем клиента
        client = Client.query.filter_by(telegram_id=telegram_id).first()
        
        if not client:
            # Создаем нового клиента
            client = Client(
                telegram_id=telegram_id,
                name="Пользователь",
                status='новый'
            )
            db.session.add(client)
            db.session.flush()
        
        # Дополняем user_brief
        if client.user_brief:
            client.user_brief += f"\n\n--- Новое сообщение ---\n{text}"
        else:
            client.user_brief = text
        
        client.updated_at = datetime.utcnow()
        client.status = 'в работе'
        
        # Сохраняем сообщение в таблицу messages
        message = Message(
            client_id=client.id,
            message_text=text,
            is_from_bot=False,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'client_id': client.id,
            'message_id': message.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def create_admin_user():
    """Создает администратора по умолчанию если его нет"""
    if not User.query.first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("Создан пользователь admin с паролем admin123")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 