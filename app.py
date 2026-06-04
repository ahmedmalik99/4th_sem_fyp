from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import requests
import mysql.connector
import bcrypt
import os
from datetime import datetime


app = Flask(__name__, static_folder='static', template_folder='templates', static_url_path='/static')
CORS(app)
app.secret_key = 'ssuet_ai_secret_key_2026_change_this_in_production'

import mysql.connector

DB_CONFIG = {
    "host": "autorack.proxy.rlwy.net",
    "user": "root",
    "password": "imEgXytMJnnvnotQQgMrPYPmJdekNWGI",
    "database": "railway",
    "port": 36297
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
        return None
#testtttttttttttttt
conn = get_db_connection()

if conn:
    print("✅ DATABASE CONNECTED SUCCESSFULLY")

    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    
    tables = cursor.fetchall()

    print("📦 TABLES IN DATABASE:")
    for t in tables:
        print(t)

else:
    print("❌ CONNECTION FAILED")
# ── API CONFIGURATION ──
# We use a list for keys so the AI can switch if one runs out of credits
import os
from dotenv import load_dotenv

load_dotenv()

API_KEYS = [
    os.getenv("API_KEY_1"),
    os.getenv("API_KEY_2")
]

API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Priority list: Free High-Quality -> Free Fast -> Paid Stable
MODELS = [
    'gemini-2.5-flash',                   # 🥇 Best Free/Low-Cost (Ultra Fast & 1M+ Context)
    'gemini-2.5-pro',                     # 🧠 Best Coding & Deep Reasoning
    'google/gemma-2-9b-it:free',          # 🥈 High Intelligence (Open Source fallback)
    'meta-llama/llama-3-8b-instruct:free', # 🥉 Very Fast & Reliable
    'mistralai/mistral-7b-instruct:free', # 🍀 Backup Free
]



SYSTEM_PROMPT = """You are the official AI Assistant for Sir Syed University of Engineering and Technology (SSUET), Karachi, Pakistan. search for everything online first from thier official website.

SSUET KEY FACTS:
- Full name: Sir Syed University of Engineering and Technology (SSUET)
- Location: University Road, Karachi-75300, Sindh, Pakistan
- Phone: +92-21-34988000 | Email: info@ssuet.edu.pk | Website: www.ssuet.edu.pk
- Founded: 1993 | Type: Private Research University
- Recognized by: HEC and PEC

FACULTIES:
1. Faculty of Electrical & Computer Engineering (FoECE) - Dean: Dr. Farooq Ahmad
2. Faculty of Computing & Applied Sciences (FoCAS) - Dean: Dr. Salman Ahmed
3. Faculty of Civil Engineering & Architecture (FoCVA) - Dean: Dr. Asma Khan
4. Faculty of Business Management & Social Science (FoBMS) - Dean: Dr. Hassan Raza

PROGRAMS:
- BS Computer Science, Computer Engineering, Electronic Engineering, Electrical Engineering
- BS Civil Engineering, Software Engineering, Biomedical Engineering, Telecommunication Engineering
- BS Robotics & Intelligent Machines (NEW — Spring 2026)
- BBA, MBA, MS Computer Engineering, MS Electronic Engineering

CURRENT NEWS:
- Spring 2026 Admissions: CLOSED
- Fall 2026 Admissions: Opening Soon
- New Program: BS Robotics & Intelligent Machines

OFFICIAL SOCIAL MEDIA:
- Facebook: https://www.facebook.com/SSUET.Karachi
- Twitter/X: https://twitter.com/ssuet_karachi
- LinkedIn: https://www.linkedin.com/school/ssuet/
- YouTube: https://www.youtube.com/@SSUETOfficial

Be warm, friendly, helpful. Use bullet points. Respond in Urdu if user writes in Urdu. Direct fee/timetable queries to ssuet.edu.pk or +92-21-34988000."""

# ── STATIC FILES ──
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# ── MAIN ROUTES ──
@app.route('/')
def index():
    # 1. Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # ❌ REMOVED: The auto-redirect for admin is gone from here.
    # This allows the admin to actually stay on the chat page.
    
    return render_template('index.html', user_name=session.get('user_name', 'User'))


# ── AUTH ROUTES ──
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            data = request.json
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            password = data.get('password')
            
            if not all([name, email, phone, password]):
                return jsonify({"error": "All fields are required"}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "Database connection failed"}), 500
            
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": "Email already registered"}), 400
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert user
            cursor.execute(
                "INSERT INTO users (name, email, phone, password_hash) VALUES (%s, %s, %s, %s)",
                (name, email, phone, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            # Create lead entry for admission tracking
            cursor.execute(
                "INSERT INTO leads (user_id, name, email, phone) VALUES (%s, %s, %s, %s)",
                (user_id, name, email, phone)
            )
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Registration successful! Please login."})
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.json
            email = data.get('email')
            password = data.get('password')
            
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "Database connection failed"}), 500
            
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                
                # Update last login
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
                conn.commit()
                cursor.close()
                conn.close()
                
                # ✅ Auto-redirect admin to admin panel
                if email == 'admin@ssuet.edu.pk':
                    return jsonify({
                        "success": True, 
                        "message": "Login successful! Redirecting to admin panel...",
                        "redirect": "/admin"
                    })
                
                return jsonify({
                    "success": True, 
                    "message": "Login successful!",
                    "redirect": "/"
                })
            else:
                return jsonify({"error": "Invalid email or password"}), 401
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"error": "Please login first"}), 401
    
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id')
        
        # --- DATABASE: Save User Message ---
        try:
            if not session_id:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO chat_sessions (user_id, session_name) VALUES (%s, %s)",
                        (session['user_id'], f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    )
                    conn.commit()
                    session_id = cursor.lastrowid
                    cursor.close()
                    conn.close()

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (session_id, sender, content) VALUES (%s, %s, %s)",
                    (session_id, 'user', user_message)
                )
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as db_e:
            print(f"⚠️ DB Save Error: {db_e}")

        # --- CONTEXT: Get History ---
        history = []
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT sender, content FROM messages WHERE session_id = %s ORDER BY created_at ASC LIMIT 20",
                    (session_id,)
                )
                history = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
                cursor.close()
                conn.close()
        except Exception as db_e:
            print(f"⚠️ DB History Error: {db_e}")

        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": user_message}
        ]
        
        # ─── DOUBLE-LAYER FALLBACK SYSTEM ───
        # Layer 1: Try different Models
        for model in MODELS:
            # Layer 2: Try different API Keys for the same model
            for key in API_KEYS:
                try:
                    print(f"🔄 Attempting: Model={model} | Key=...{key[-5:]}")
                    
                    response = requests.post(
                        API_URL,
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {key}',
                            'HTTP-Referer': 'https://ssuet.edu.pk',
                            'X-Title': 'SSUET AI Assistant'
                        },
                        json={
                            "model": model,
                            "max_tokens": 1024,
                            "messages": messages_payload
                        },
                        timeout=15 
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        ai_reply = result['choices'][0]['message']['content']
                        
                        # Save AI response to DB
                        try:
                            conn = get_db_connection()
                            if conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "INSERT INTO messages (session_id, sender, content) VALUES (%s, %s, % laL)",
                                    (session_id, 'ai', ai_reply)
                                )
                                conn.commit()
                                cursor.close()
                                conn.close()
                        except: pass
                        
                        print(f"✅ SUCCESS! Used Model: {model}")
                        return jsonify({"reply": ai_reply, "session_id": session_id, "model": model})
                    
                    else:
                        print(f"❌ Key failed for {model} (Status: {response.status_code})")
                        continue # Try next key
                        
                except Exception as e:
                    print(f"⚠️ Request Error with {model}: {e}")
                    continue # Try next key
        
        return jsonify({"reply": "❌ All API keys and all models are currently unavailable. Please try again in a few minutes."}), 500
            
    except Exception as e:
        print(f"❌ CRITICAL SERVER ERROR: {e}")
        return jsonify({"reply": f"❌ Server Error: {str(e)}"}), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    if 'user_id' not in session:
        return jsonify({"error": "Please login first"}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, session_name, created_at FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC",
            (session['user_id'],)
        )
        sessions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/messages/<int:session_id>', methods=['GET'])
def get_messages(session_id):
    if 'user_id' not in session:
        return jsonify({"error": "Please login first"}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Verify session belongs to user
        cursor.execute("SELECT user_id FROM chat_sessions WHERE id = %s", (session_id,))
        result = cursor.fetchone()
        
        if not result or result['user_id'] != session['user_id']:
            cursor.close()
            conn.close()
            return jsonify({"error": "Unauthorized"}), 403
        
        cursor.execute(
            "SELECT sender, content, created_at FROM messages WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,)
        )
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({"messages": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── FEEDBACK ROUTES ──
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return jsonify({"error": "Please login first"}), 401
    
    try:
        data = request.json
        rating = data.get('rating')
        category = data.get('category', 'general')
        comment = data.get('comment', '')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (user_id, rating, category, comment) VALUES (%s, %s, %s, %s)",
            (session['user_id'], rating, category, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Thank you for your feedback!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── TICKET ROUTES ──
@app.route('/api/tickets', methods=['POST', 'GET'])
def tickets():
    if 'user_id' not in session:
        return jsonify({"error": "Please login first"}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Create ticket
            data = request.json
            subject = data.get('subject')
            description = data.get('description')
            priority = data.get('priority', 'medium')
            
            cursor.execute(
                "INSERT INTO tickets (user_id, subject, description, priority) VALUES (%s, %s, %s, %s)",
                (session['user_id'], subject, description, priority)
            )
            conn.commit()
            ticket_id = cursor.lastrowid
            cursor.close()
            conn.close()
            
            return jsonify({"success": True, "ticket_id": ticket_id, "message": "Ticket created successfully!"})
        
        else:
            # Get tickets
            cursor.execute(
                "SELECT id, subject, status, priority, created_at FROM tickets WHERE user_id = %s ORDER BY created_at DESC",
                (session['user_id'],)
            )
            tickets_list = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return jsonify({"tickets": tickets_list})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── ADMIN ROUTES ──
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if admin email
    if session.get('user_email') != 'admin@ssuet.edu.pk':
        return jsonify({"error": "Unauthorized - Admin access only"}), 403
    
    return render_template('admin.html')

@app.route('/api/admin/stats')
def admin_stats():
    if session.get('user_email') != 'admin@ssuet.edu.pk':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        stats = {}
        
        # Total users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = cursor.fetchone()['count']
        
        # Total messages
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        stats['total_messages'] = cursor.fetchone()['count']
        
        # Total leads
        cursor.execute("SELECT COUNT(*) as count FROM leads")
        stats['total_leads'] = cursor.fetchone()['count']
        
        # Leads by status
        cursor.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
        stats['leads_by_status'] = cursor.fetchall()
        
        # Feedback average rating
        cursor.execute("SELECT AVG(rating) as avg_rating FROM feedback")
        stats['avg_rating'] = cursor.fetchone()['avg_rating'] or 0
        
        # Tickets by status
        cursor.execute("SELECT status, COUNT(*) as count FROM tickets GROUP BY status")
        stats['tickets_by_status'] = cursor.fetchall()
        
        # Messages per day (last 7 days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM messages 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """)
        stats['messages_per_day'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/leads')
def admin_leads():
    if session.get('user_email') != 'admin@ssuet.edu.pk':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({"leads": leads})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/faculty')
def get_faculty():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM faculty ORDER BY department, name")
        faculty = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({"faculty": faculty})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── HEALTH CHECK ──
@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok",
        "message": "SSUET AI Server is running!",
        "models_available": len(MODELS),
        "free_models": len([m for m in MODELS if ":free" in m])
    })

# ── MAIN ──
# ── MAIN ──
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 SSUET AI Assistant Server Starting...")
    print("="*60)

    app.run(host="0.0.0.0", port=5000)
