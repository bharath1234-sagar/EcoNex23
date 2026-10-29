import os, json, sqlite3, hashlib
from datetime import date
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "econex-carbon-os-secret-2026")

BASE = Path(__file__).resolve().parent
DB = BASE / 'econex.db'
UPLOAD_FOLDER = BASE / 'static' / 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)

def hash_pw(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

TEXTS = {
    'en': {
        'overview': 'Overview & Dashboard',
        'profile_page': 'Profile Settings',
        'logger': 'Emission Logger',
        'simulator': 'Reduction Simulator',
        'leaderboard': 'Challenges & Quests',
        'recommendations': 'AI Recommendations',
        'sign_out': 'Sign Out',
        'brand_subtitle': 'Carbon Intelligence Platform',
        'active_role': 'Active Persona',
        'export_report': 'Export Report',
        'last_30_days': 'Last 30 Days',
        'lifetime_emissions': 'Total Footprint',
        'verified_reductions': 'Verified Reductions',
        'benchmark': 'National Benchmark',
        'command_center': 'Sustainability Command Center',
        'categories_title': 'Persona Category & Operational Role',
        'categories_subtitle': 'EcoNex adjusts greenhouse gas emission factors to your exact operational persona.',
        'log_activity': 'Log Daily Consumption',
        'log_subtitle': 'Calculated using official national grid and fuel emission intensity factors',
        'select_activity': 'Select Activity Stream',
        'input_quantity': 'Enter Quantity',
        'compute_btn': '+ Record & Compute Footprint',
        'sim_title': 'Interactive "What-If" Reduction Simulator',
        'sim_subtitle': 'Simulate and project your environmental and monetary savings before committing',
        'commit_plan': 'Commit to this Reduction Plan ✓',
        'challenges_title': 'Sustainability Challenges & Badges',
        'challenges_sub': 'Complete micro-actions to cut emissions and earn EcoPoints',
        'community_board': 'Sustainability Leaderboard',
        'audit_log': 'Consumption & Emission Audit Log',
        'language': 'Language'
    },
    'kn': {
        'overview': 'ಮುಖಪುಟ ಫಲಕ (Dashboard)',
        'profile_page': 'ಪ್ರೊಫೈಲ್ ಸೆಟ್ಟಿಂಗ್ಸ್',
        'logger': 'ಹೊರಸೂಸುವಿಕೆ ದಾಖಲಕ',
        'simulator': 'ಕಡಿತ ಸಿಮ್ಯುಲೇಟರ್',
        'leaderboard': 'ಸವಾಲುಗಳು & ಶ್ರೇಯಾಂಕ',
        'recommendations': 'ಕಾರ್ಬನ್ ಕಡಿತ ಶಿಫಾರಸುಗಳು',
        'sign_out': 'ಲಾಗ್ ಔಟ್',
        'brand_subtitle': 'ಕಾರ್ಬನ್ ಇಂಟೆಲಿಜೆನ್ಸ್ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್',
        'active_role': 'ಪ್ರಸ್ತುತ ಪ್ರೊಫೈಲ್',
        'export_report': 'ವರದಿ ಡೌನ್‌ಲೋಡ್',
        'last_30_days': 'ಕಳೆದ 30 ದಿನಗಳು',
        'lifetime_emissions': 'ಒಟ್ಟು ಹೊರಸೂಸುವಿಕೆ',
        'verified_reductions': 'ಉಳಿತಾಯವಾದ ಕಾರ್ಬನ್',
        'benchmark': 'ರಾಷ್ಟ್ರೀಯ ಸರಾಸರಿ',
        'command_center': 'ಸುಸ್ಥಿರತೆ ನಿರ್ವಹಣಾ ಕೇಂದ್ರ',
        'categories_title': 'ವ್ಯಕ್ತಿ ಅಥವಾ ಸಂಸ್ಥೆಯ ವರ್ಗ',
        'categories_subtitle': 'ಇಕೋನೆಕ್ಸ್ ನಿಮ್ಮ ಪಾತ್ರಕ್ಕೆ ತಕ್ಕಂತೆ ಹೊರಸೂಸುವಿಕೆ ಲೆಕ್ಕಾಚಾರವನ್ನು ಕಸ್ಟಮೈಸ್ ಮಾಡುತ್ತದೆ.',
        'log_activity': 'ದೈನಂದಿನ ಬಳಕೆ ದಾಖಲಿಸಿ',
        'log_subtitle': 'ಅಧಿಕೃತ ಗ್ರಿಡ್ ಮತ್ತು ಇಂಧನ ಸೂತ್ರಗಳ ಆಧಾರದ ಮೇಲೆ ಲೆಕ್ಕಹಾಕಲಾಗುತ್ತದೆ',
        'select_activity': 'ಚಟುವಟಿಕೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
        'input_quantity': 'ಪ್ರಮಾಣ ನಮೂದಿಸಿ',
        'compute_btn': '+ ಲೆಕ್ಕಹಾಕಿ ದಾಖಲಿಸಿ',
        'sim_title': 'ಪರ್ಯಾಯ ಕಡಿತ ಸಿಮ್ಯುಲೇಟರ್ ("What-If")',
        'sim_subtitle': 'ಕ್ರಮ ಕೈಗೊಳ್ಳುವ ಮುನ್ನ ಪರಿಸರ ಮತ್ತು ಹಣಕಾಸು ಉಳಿತಾಯವನ್ನು ಅಂದಾಜಿಸಿ',
        'commit_plan': 'ಈ ಕಡಿತ ಯೋಜನೆಯನ್ನು ಸ್ವೀಕರಿಸಿ ✓',
        'challenges_title': 'ಸುಸ್ಥಿರತೆಯ ಸವಾಲುಗಳು ಮತ್ತು ಬ್ಯಾಡ್ಜ್‌ಗಳು',
        'challenges_sub': 'ಸಣ್ಣ ಸಣ್ಣ ಕ್ರಮಗಳನ್ನು ದಾಖಲಿಸಿ ಪರಿಸರ ಅಂಕಗಳನ್ನು ಗಳಿಸಿ',
        'community_board': 'ಸಮುದಾಯ ಲೀಡರ್‌ಬೋರ್ಡ್',
        'audit_log': 'ಆಡಿಟ್ ಇತಿಹಾಸ ದಾಖಲೆ',
        'language': 'ಭಾಷೆ'
    },
    'hi': {
        'overview': 'डैशबोर्ड अवलोकन',
        'profile_page': 'प्रोफ़ाइल सेटिंग्स',
        'logger': 'उत्सर्जन लॉगर',
        'simulator': 'कटौती सिम्युलेटर',
        'leaderboard': 'चुनौतियां और रैंकिंग',
        'recommendations': 'कार्बन कटौती सिफारिशें',
        'sign_out': 'साइन आउट',
        'brand_subtitle': 'कार्बन इंटेलिजेंस प्लेटफॉर्म',
        'active_role': 'सक्रिय प्रोफ़ाइल',
        'export_report': 'रिपोर्ट डाउनलोड करें',
        'last_30_days': 'पिछले 30 दिन',
        'lifetime_emissions': 'कुल पदचिह्न',
        'verified_reductions': 'प्रमाणित कटौती',
        'benchmark': 'राष्ट्रीय मानक',
        'command_center': 'सस्टेनेबिलिटी कमांड सेंटर',
        'categories_title': 'कार्यक्षेत्र एवं संगठन श्रेणी',
        'categories_subtitle': 'इकोनेक्स आपकी विशिष्ट श्रेणी के अनुसार उत्सर्जन मानकों को समायोजित करता है।',
        'log_activity': 'दैनिक उपयोग दर्ज करें',
        'log_subtitle': 'राष्ट्रीय ग्रिड और ईंधन उत्सर्जन मानकों के आधार पर गणना',
        'select_activity': 'गतिविधि चुनें',
        'input_quantity': 'मात्रा दर्ज करें',
        'compute_btn': '+ गणना करें और सहेजें',
        'sim_title': 'इंटरैक्टिव कार्बन कटौती सिम्युलेटर',
        'sim_subtitle': 'कदम उठाने से पहले अपने वित्तीय और पर्यावरणीय प्रभाव का विश्लेषण करें',
        'commit_plan': 'यह कटौती योजना अपनाएं ✓',
        'challenges_title': 'पर्यावरण चुनौतियां और बैज',
        'challenges_sub': 'कदम उठाएं और इको-पॉइंट अर्जित करें',
        'community_board': 'सामुदायिक लीडरबोर्ड',
        'audit_log': 'गतिविधि ऑडिट रिकॉर्ड',
        'language': 'भाषा'
    },
    'ta': {
        'overview': 'கண்ணோட்டம்',
        'profile_page': 'சுயவிவர அமைப்புகள்',
        'logger': 'வெளியீட்டுப் பதிவு',
        'simulator': 'குறைப்பு உருவகப்படுத்துதல்',
        'leaderboard': 'சவால்கள் & தரவரிசை',
        'recommendations': 'கார்பன் குறைப்பு பரிந்துரைகள்',
        'sign_out': 'வெளியேறு',
        'brand_subtitle': 'கார்பன் நுண்ணறிவு தளம்',
        'active_role': 'தற்போதைய பங்கு',
        'export_report': 'அறிக்கையைப் பதிவிறக்கு',
        'last_30_days': 'கடந்த 30 நாட்கள்',
        'lifetime_emissions': 'மொத்த உமிழ்வு',
        'verified_reductions': 'சரிபார்க்கப்பட்ட சேமிப்பு',
        'benchmark': 'தேசிய அளவுகோல்',
        'command_center': 'நிலைத்தன்மை கட்டுப்பாட்டு மையம்',
        'categories_title': 'பயனர் அல்லது நிறுவன வகை',
        'categories_subtitle': 'உங்கள் பாத்திரத்திற்கு ஏற்ப கார்பன் சூத்திரங்களை அமைக்கிறது.',
        'log_activity': 'தினசரி நுகர்வை பதிவு செய்க',
        'log_subtitle': 'அதிகாரப்பூர்வ உமிழ்வு காரணிகள் மூலம் கணக்கிடப்பட்டது',
        'select_activity': 'செயல்பாட்டைத் தேர்ந்தெடுக்கவும்',
        'input_quantity': 'அளவை உள்ளிடவும்',
        'compute_btn': '+ கணக்கிட்டு சேமிக்கவும்',
        'sim_title': 'கார்பன் குறைப்பு உருவகப்படுத்துதல்',
        'sim_subtitle': 'நடவடிக்கை எடுப்பதற்கு முன் சேமிப்பை மதிப்பிடுங்கள்',
        'commit_plan': 'இந்தத் திட்டத்தை ஏற்கவும் ✓',
        'challenges_title': 'சுற்றுச்சூழல் சவால்கள் & பேட்ஜ்கள்',
        'challenges_sub': 'பணிகளை முடித்து சுற்றுச்சூழல் புள்ளிகளைப் பெறுங்கள்',
        'community_board': 'சமூக முன்னணி பலகை',
        'audit_log': 'தணிக்கை பதிவு',
        'language': 'மொழி'
    },
    'te': {
        'overview': 'డాష్‌బోర్డ్ అవలోకనం',
        'profile_page': 'ప్రొఫైల్ సెట్టింగ్‌లు',
        'logger': 'ఉద్గారాల నమోదు',
        'simulator': 'తగ్గింపు సిమ్యులేటర్',
        'leaderboard': 'సవాళ్లు మరియు ర్యాంకింగ్',
        'recommendations': 'కార్బన్ తగ్గింపు సిఫార్సులు',
        'sign_out': 'లాగ్ అవుట్',
        'brand_subtitle': 'కార్బన్ ఇంటెలిజెన్స్ ప్లాట్‌ఫారమ్',
        'active_role': 'ప్రస్తుత పాత్ర',
        'export_report': 'నివేదికను డౌన్‌లోడ్ చేయండి',
        'last_30_days': 'గత 30 రోజులు',
        'lifetime_emissions': 'మొత్తం ఉద్గారాలు',
        'verified_reductions': 'ధృవీకరించబడిన తగ్గింపు',
        'benchmark': 'జాతీయ ప్రమాణం',
        'command_center': 'సుస్థిరత నియంత్రణ కేంద్రం',
        'categories_title': 'వ్యక్తి లేదా సంస్థ వర్గం',
        'categories_subtitle': 'మీ పాత్రకు తగినట్లుగా కార్బన్ గణనలను రూపొందిస్తుంది.',
        'log_activity': 'రోజువారీ వినియోగాన్ని నమోదు చేయండి',
        'log_subtitle': 'అధికారిక గ్రిడ్ మరియు ఇంధన కారకాలతో లెక్కించబడింది',
        'select_activity': 'కార్యాచరణను ఎంచుకోండి',
        'input_quantity': 'పరిమాణం నమోదు చేయండి',
        'compute_btn': '+ లెక్కించి సేవ్ చేయండి',
        'sim_title': 'ఇంటరాక్టివ్ తగ్గింపు ఇంజిన్',
        'sim_subtitle': 'చర్యలు చేపట్టే ముందు పొదుపును అంచనా వేయండి',
        'commit_plan': 'ఈ ప్రణాళికను స్వీకరించండి ✓',
        'challenges_title': 'సుస్థిరత సవాళ్లు & బ్యాడ్జ్‌లు',
        'challenges_sub': 'పనులను పూర్తి చేసి ఎకోపాయింట్లను సంపాదించండి',
        'community_board': 'కమ్యూనిటీ లీడర్‌బోర్డ్',
        'audit_log': 'ఆడిట్ రికార్డు',
        'language': 'భాష'
    }
}


PROFILES = {
    'Household': {
        'icon': '🏡', 'label': 'Household / Family', 'badge': 'Residential',
        'desc': 'For families, residential homes, and apartment dwellers.',
        'unit': 'household',
        'fields': [('electricity', 'Grid Electricity', 'kWh', 0.82), ('lpg', 'Cooking LPG', 'kg', 3.00), ('car', 'Private Car Travel', 'km', 0.17), ('waste', 'Municipal Mixed Waste', 'kg', 0.50)]
    },
    'City Resident': {
        'icon': '🚲', 'label': 'Urban Working Professional', 'badge': 'Commuter',
        'desc': 'For urban professionals commuting by cabs, metro, and city buses.',
        'unit': 'commuter',
        'fields': [('electricity', 'Apartment Power', 'kWh', 0.82), ('car', 'Cab / Car Travel', 'km', 0.17), ('bus', 'Metro & City Bus', 'km', 0.08), ('waste', 'Mixed Waste', 'kg', 0.50)]
    },
    'Student / Campus': {
        'icon': '🎓', 'label': 'Student & Campus Hosteller', 'badge': 'Education',
        'desc': 'For college students tracking hostel power, mess food, and campus transit.',
        'unit': 'student',
        'fields': [('electricity', 'Hostel Electricity', 'kWh', 0.82), ('bus', 'Campus Shuttle / Bus', 'km', 0.08), ('waste', 'Hostel Waste', 'kg', 0.50), ('solar', 'Rooftop Solar Offset', 'kWh', -0.82)]
    },
    'College / Institution': {
        'icon': '🏫', 'label': 'College / Organization Admin', 'badge': 'Campus Admin',
        'desc': 'For institution authorities managing campus fleets, buildings, and backup power.',
        'unit': 'campus',
        'fields': [('electricity', 'Campus Grid Power', 'kWh', 0.82), ('diesel', 'Generator / Fleet Diesel', 'litres', 2.68), ('car', 'Institutional Travel', 'km', 0.17), ('waste', 'Campus Landfill Waste', 'kg', 0.50)]
    },
    'Farmer / Dairy Farm': {
        'icon': '🌾', 'label': 'Farmer & Dairy Producer', 'badge': 'Agriculture',
        'desc': 'For agricultural plots, irrigation pumps, tractors, and livestock.',
        'unit': 'farm output',
        'fields': [('electricity', 'Irrigation Pump Power', 'kWh', 0.82), ('diesel', 'Tractor & Machinery Diesel', 'litres', 2.68), ('fertilizer', 'Nitrogen Fertilizer', 'kg', 5.50), ('livestock', 'Livestock Units', 'head', 100.0)]
    },
    'Industry': {
        'icon': '🏭', 'label': 'Industrial / Manufacturing Plant', 'badge': 'Enterprise',
        'desc': 'For factories, workshops, and commercial manufacturing facilities.',
        'unit': 'production units',
        'fields': [('electricity', '3-Phase Grid Electricity', 'kWh', 0.82), ('diesel', 'Boiler / Generator Diesel', 'litres', 2.68), ('waste', 'Industrial Solid Waste', 'kg', 0.50), ('water', 'Industrial Water Use', 'kL', 0.34)]
    }
}

ACTIVITIES = {
    'electricity': ('Grid Electricity', 'kWh', 0.82),
    'diesel': ('Diesel / Generator Fuel', 'litres', 2.68),
    'lpg': ('LPG Cylinder', 'kg', 3.00),
    'car': ('Petrol / Diesel Car Travel', 'km', 0.17),
    'bus': ('Bus / Metro Transit', 'km', 0.08),
    'waste': ('Mixed Waste to Landfill', 'kg', 0.50),
    'water': ('Water Usage', 'kL', 0.34),
    'fertilizer': ('Nitrogen Fertilizer', 'kg', 5.50),
    'livestock': ('Livestock Emission Factor', 'animal unit', 100.0),
    'solar': ('Solar Clean Energy Offset', 'kWh', -0.82)
}

CHALLENGES = [
    {
        'id': 'commute',
        'title': 'Clean Commute Challenge',
        'desc': 'Take metro, bus, bicycle, or carpool instead of driving solo.',
        'icon': '🚲',
        'points': 50,
        'activities': [
            {'title': 'Rode Metro / City Bus', 'saving': '1.8 kg CO₂e', 'cat': 'Commute', 'val': 1.8},
            {'title': 'Carpool / Shared Ride', 'saving': '1.2 kg CO₂e', 'cat': 'Commute', 'val': 1.2},
            {'title': 'Cycled / Walked to work', 'saving': '2.5 kg CO₂e', 'cat': 'Commute', 'val': 2.5}
        ]
    },
    {
        'id': 'energy',
        'title': 'Energy Mindful Challenge',
        'desc': 'Reduce electrical load by adopting efficient lighting and appliances.',
        'icon': '⚡',
        'points': 40,
        'activities': [
            {'title': 'Switched to 9W LED Bulbs', 'saving': '3.8 kg CO₂e', 'cat': 'Energy', 'val': 3.8},
            {'title': 'AC set to Eco 24°C', 'saving': '2.1 kg CO₂e', 'cat': 'Energy', 'val': 2.1},
            {'title': 'Unplugged Phantom Loads', 'saving': '0.9 kg CO₂e', 'cat': 'Energy', 'val': 0.9}
        ]
    }
]

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    try:
        cur = c.cursor()
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT,
                name TEXT,
                picture TEXT,
                profile_category TEXT DEFAULT 'City Resident',
                org TEXT DEFAULT '',
                location TEXT DEFAULT 'Bengaluru',
                language TEXT DEFAULT 'en'
            );
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day TEXT,
                period TEXT,
                profile TEXT,
                payload TEXT,
                total REAL
            );
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day TEXT,
                title TEXT,
                category TEXT,
                saved REAL,
                note TEXT
            );
            CREATE TABLE IF NOT EXISTS challenge_done (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                done INTEGER DEFAULT 0,
                UNIQUE(user_id, title)
            );
            CREATE TABLE IF NOT EXISTS user_simulation (
                user_id INTEGER PRIMARY KEY,
                slider1 INTEGER DEFAULT 8,
                slider2 INTEGER DEFAULT 6,
                slider3 INTEGER DEFAULT 5,
                saved_co2 REAL DEFAULT 48.2,
                saved_inr INTEGER DEFAULT 1850
            );
        ''')
        c.commit()

        demo_pw = hash_pw('password123')
        cur.execute("INSERT OR IGNORE INTO users(id, email, password_hash, name, picture, profile_category, org, location, language) VALUES(1, 'bharath@gmail.com', ?, 'Bharath Sagar', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80', 'City Resident', 'GreenTech Bengaluru', 'Bengaluru', 'en')", (demo_pw,))
        cur.execute("INSERT OR IGNORE INTO user_simulation(user_id) VALUES(1)")
        for ch in CHALLENGES:
            cur.execute("INSERT OR IGNORE INTO challenge_done(user_id, title, done) VALUES(1, ?, 0)", (ch['title'],))
        c.commit()
    finally:
        c.close()

init_db()

def generate_recs(profile_cat, streams, tot_saved, row_count):
    if row_count == 0 or not streams:
        return [{
            'title': 'No Consumption Data Logged Yet',
            'desc': 'Enter your daily electricity, fuel, or waste usage in the Emission Logger above to receive tailored, high-impact reduction recommendations.',
            'potential_co2': '—',
            'potential_money': '—',
            'action_title': 'Log Your First Activity Above 👆',
            'action_saved': 0.0,
            'category': 'General',
            'icon': '📝',
            'priority': 'GET STARTED'
        }]
    
    recs = []
    sorted_s = sorted(streams.items(), key=lambda x: x[1], reverse=True)
    
    for idx, (stream_name, stream_val) in enumerate(sorted_s):
        prio = 'HIGH' if idx == 0 else ('MEDIUM' if idx == 1 else 'EASY WIN')
        if 'Electricity' in stream_name or 'Power' in stream_name:
            recs.append({
                'title': f'Optimize {stream_name} Consumption',
                'desc': f'You generated {round(stream_val, 1)} kg CO₂e from grid power. Switch bulbs to 9W LEDs, use inverter appliances, and maintain AC at 24°C.',
                'potential_co2': f'{round(stream_val * 0.25, 1)} kg CO₂e / month',
                'potential_money': f'₹{int(stream_val * 8)} / month saved',
                'action_title': f'Upgrade {stream_name} Efficiency Protocol',
                'action_saved': round(stream_val * 0.25, 1),
                'category': 'Energy',
                'icon': '💡',
                'priority': prio
            })
        elif 'Travel' in stream_name or 'Car' in stream_name or 'Bus' in stream_name:
            recs.append({
                'title': f'Mitigate {stream_name} Footprint',
                'desc': f'Vehicular travel accounts for {round(stream_val, 1)} kg CO₂e. Shift 2–3 commute days each week to Metro rail, city bus transit, or carpooling.',
                'potential_co2': f'{round(stream_val * 0.30, 1)} kg CO₂e / month',
                'potential_money': f'₹{int(stream_val * 12)} / month saved',
                'action_title': 'Shift Commute to Public Transit / Carpool',
                'action_saved': round(stream_val * 0.30, 1),
                'category': 'Mobility',
                'icon': '🚇',
                'priority': prio
            })
        elif 'Waste' in stream_name:
            recs.append({
                'title': f'Divert & Compost {stream_name}',
                'desc': f'Landfill waste contributes {round(stream_val, 1)} kg CO₂e. Segregate wet kitchen waste for home composting.',
                'potential_co2': f'{round(stream_val * 0.40, 1)} kg CO₂e / month',
                'potential_money': '₹300 / month saved',
                'action_title': 'Segregate & Compost Organic Kitchen Waste',
                'action_saved': round(stream_val * 0.40, 1),
                'category': 'Waste',
                'icon': '🌱',
                'priority': prio
            })
        else:
            recs.append({
                'title': f'Reduce {stream_name} Intensity',
                'desc': f'{stream_name} contributes {round(stream_val, 1)} kg CO₂e. Implement resource conservation protocols to minimize overhead.',
                'potential_co2': f'{round(stream_val * 0.20, 1)} kg CO₂e / month',
                'potential_money': '₹400 / month saved',
                'action_title': f'Conserve {stream_name} Usage',
                'action_saved': round(stream_val * 0.20, 1),
                'category': 'General',
                'icon': '⚡',
                'priority': prio
            })

    if len(recs) < 4:
        recs.append({
            'title': 'Install Rooftop Solar / Clean Power',
            'desc': 'Solar electricity generation offsets carbon at 0.82 kg CO₂e per kWh compared to coal-fired grid electricity.',
            'potential_co2': '82.0 kg CO₂e / month',
            'potential_money': '₹2,400 / month saved',
            'action_title': 'Solar Clean Power Utilization Plan',
            'action_saved': 82.0,
            'category': 'Solar',
            'icon': '☀️',
            'priority': 'MAX IMPACT'
        })

    return recs

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    lang = session.get('lang', 'en')
    t = TEXTS.get(lang, TEXTS['en'])
    
    c = conn()
    try:
        cur = c.cursor()
        cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        
        cur.execute('SELECT * FROM activities WHERE user_id = ? ORDER BY day DESC', (user_id,))
        rows = [dict(x) for x in cur.fetchall()]

        cur.execute('SELECT * FROM actions WHERE user_id = ? ORDER BY day DESC', (user_id,))
        actions = [dict(x) for x in cur.fetchall()]

        cur.execute('SELECT * FROM challenge_done WHERE user_id = ?', (user_id,))
        done_map = {x['title']: x['done'] for x in cur.fetchall()}

        cur.execute('SELECT * FROM user_simulation WHERE user_id = ?', (user_id,))
        sim_row = cur.fetchone()
    finally:
        c.close()

    for r in rows:
        try:
            pl = json.loads(r['payload'])
            r['summary'] = ', '.join(f"{ACTIVITIES[k][0]}: {v} {ACTIVITIES[k][1]}" for k, v in pl.items() if k in ACTIVITIES)
        except Exception:
            r['summary'] = 'Recorded activity'

    category = user['profile_category'] if user and user['profile_category'] in PROFILES else 'City Resident'
    curr_profile = PROFILES[category]
    
    monthly_kg = sum(r['total'] for r in rows)
    total_lifetime = sum(r['total'] for r in rows)
    total_saved = sum(a['saved'] for a in actions)
    
    stream_totals = {}
    for r in rows:
        try:
            pl = json.loads(r['payload'])
            for k, v in pl.items():
                if k in ACTIVITIES:
                    lbl = ACTIVITIES[k][0]
                    stream_totals[lbl] = stream_totals.get(lbl, 0) + (float(v) * ACTIVITIES[k][2])
        except Exception:
            pass

    recommendations = generate_recs(category, stream_totals, total_saved, len(rows))

    challenges_with_state = []
    for ch in CHALLENGES:
        item = dict(ch)
        item['done'] = done_map.get(ch['title'], 0) == 1
        challenges_with_state.append(item)

    leaderboard = [
        {'name': 'GreenTech Campus', 'category': 'College / Institution', 'points': 880},
        {'name': user['name'] + ' (You)', 'category': category, 'points': int(total_saved * 4 + 180), 'you': True},
        {'name': 'EcoFarm Agro', 'category': 'Farmer / Dairy Farm', 'points': 740}
    ]

    return render_template('index.html',
                           user=user,
                           profiles=PROFILES,
                           current_profile=curr_profile,
                           category_key=category,
                           activities=ACTIVITIES,
                           rows=rows,
                           actions=actions,
                           challenges=challenges_with_state,
                           recommendations=recommendations,
                           monthly_kg=round(monthly_kg, 2),
                           total_lifetime=round(total_lifetime, 2),
                           total_saved=round(total_saved, 2),
                           stream_totals=stream_totals,
                           leaderboard=leaderboard,
                           sim_data=sim_row,
                           t=t,
                           current_lang=lang)

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('login.html', t=TEXTS['en'])

@app.route('/profile')
def profile_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    c = conn()
    try:
        cur = c.cursor()
        cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
    finally:
        c.close()
    category = user['profile_category'] if user and user['profile_category'] in PROFILES else 'City Resident'
    return render_template('profile.html', user=user, profiles=PROFILES, current_profile=PROFILES[category], category_key=category, t=TEXTS['en'])

@app.post('/auth/login')
def auth_login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    c = conn()
    try:
        cur = c.cursor()
        cur.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cur.fetchone()
        if not user or user['password_hash'] != hash_pw(password):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
        session['user_id'] = user['id']
    finally:
        c.close()
    return redirect(url_for('home'))

@app.post('/auth/demo')
def auth_demo():
    session['user_id'] = 1
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.post('/activity/add')
def add_activity():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    c = conn()
    try:
        cur = c.cursor()
        cur.execute('SELECT profile_category FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        profile = user['profile_category'] if user else 'City Resident'
        act_key = request.form.get('activity_key', '')
        quantity = max(0.0, float(request.form.get('quantity', 0) or 0))
        day = request.form.get('day') or date.today().isoformat()
        
        if act_key in ACTIVITIES and quantity > 0:
            factor = ACTIVITIES[act_key][2]
            total = round(quantity * factor, 3)
            payload = json.dumps({act_key: quantity})
            cur.execute('INSERT INTO activities(user_id, day, period, profile, payload, total) VALUES (?, ?, ?, ?, ?, ?)',
                        (user_id, day, day[:7], profile, payload, total))
            c.commit()
    finally:
        c.close()
    return redirect(url_for('home'))

@app.post('/action/add')
def add_action():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    title = request.form.get('title', 'Sustainable Action')
    category = request.form.get('category', 'Energy')
    saved = float(request.form.get('saved', 0))
    day = date.today().isoformat()
    
    c = conn()
    try:
        cur = c.cursor()
        cur.execute('INSERT INTO actions(user_id, day, title, category, saved, note) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, day, title, category, saved, 'Adopted recommendation'))
        c.commit()
    finally:
        c.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'status': 'success', 'saved': saved})
    return redirect(url_for('home') + '#recommendations-section')

@app.post('/challenge/toggle')
def challenge_toggle():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    title = request.form.get('title', '')
    c = conn()
    try:
        cur = c.cursor()
        cur.execute('INSERT OR IGNORE INTO challenge_done(user_id, title, done) VALUES(?, ?, 0)', (user_id, title))
        cur.execute('UPDATE challenge_done SET done = 1 - done WHERE user_id = ? AND title = ?', (user_id, title))
        c.commit()
    finally:
        c.close()
    return redirect(url_for('home') + '#challenges-section')

@app.post('/challenge/quick_log')
def challenge_quick_log():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    title = request.form.get('title', 'Challenge Activity')
    category = request.form.get('category', 'General')
    saved = float(request.form.get('saved', 1.5))
    day = date.today().isoformat()

    c = conn()
    try:
        cur = c.cursor()
        # Record into actions (which feeds total saved and audit log)
        cur.execute('INSERT INTO actions(user_id, day, title, category, saved, note) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, day, title, category, saved, 'Logged via Challenge micro-action'))
        
        # Also mark parent challenge as done
        for ch in CHALLENGES:
            for act in ch['activities']:
                if act['title'] == title:
                    cur.execute('INSERT OR IGNORE INTO challenge_done(user_id, title, done) VALUES(?, ?, 1)', (user_id, ch['title']))
                    cur.execute('UPDATE challenge_done SET done = 1 WHERE user_id = ? AND title = ?', (user_id, ch['title']))
        c.commit()

        cur.execute('SELECT coalesce(sum(saved), 0) as tot_saved FROM actions WHERE user_id = ?', (user_id,))
        new_tot = round(cur.fetchone()['tot_saved'], 1)
    finally:
        c.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'status': 'success', 'saved': saved, 'total_saved': new_tot, 'title': title})
    return redirect(url_for('home') + '#challenges-section')


@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    new_cat = request.form.get('profile_category', 'City Resident')
    name = request.form.get('name', '').strip()
    org = request.form.get('org', '').strip()
    location = request.form.get('location', '').strip()
    picture = request.form.get('picture', '').strip()

    file = request.files.get('avatar_file')
    if file and file.filename != '':
        filename = secure_filename(f"user_{user_id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        picture = f"/static/uploads/{filename}"
    
    if new_cat in PROFILES:
        c = conn()
        try:
            cur = c.cursor()
            if picture:
                cur.execute('UPDATE users SET profile_category = ?, name = ?, org = ?, location = ?, picture = ? WHERE id = ?',
                            (new_cat, name, org, location, picture, user_id))
            else:
                cur.execute('UPDATE users SET profile_category = ?, name = ?, org = ?, location = ? WHERE id = ?',
                            (new_cat, name, org, location, user_id))
            c.commit()
        finally:
            c.close()
    return redirect(url_for('profile_page'))


@app.route('/set_language', methods=['POST'])
def set_language():
    lang = request.form.get('lang', 'en')
    if lang in TEXTS:
        session['lang'] = lang
        user_id = session.get('user_id')
        if user_id:
            c = conn()
            try:
                cur = c.cursor()
                cur.execute('UPDATE users SET language = ? WHERE id = ?', (lang, user_id))
                c.commit()
            finally:
                c.close()
    return redirect(request.referrer or url_for('home'))


@app.post('/auth/register')
def auth_register():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    profile_category = request.form.get('profile_category', 'City Resident')
    
    if not email or not password:
        flash('Email and password are required.', 'error')
        return redirect(url_for('login'))
        
    c = conn()
    try:
        cur = c.cursor()
        cur.execute('SELECT id FROM users WHERE email = ?', (email,))
        existing = cur.fetchone()
        if existing:
            flash('Email already registered. Please sign in.', 'error')
            return redirect(url_for('login'))
            
        pw_hash = hash_pw(password)
        default_pic = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'
        cur.execute('INSERT INTO users(email, password_hash, name, picture, profile_category, location, language) VALUES(?, ?, ?, ?, ?, ?, ?)',
                    (email, pw_hash, name or 'Eco User', default_pic, profile_category, 'Bengaluru', 'en'))
        c.commit()
        
        cur.execute('SELECT id FROM users WHERE email = ?', (email,))
        new_user = cur.fetchone()
        session['user_id'] = new_user['id']
        
        # Initialize default simulation & challenges
        cur.execute('INSERT OR IGNORE INTO user_simulation(user_id) VALUES(?)', (new_user['id'],))
        for ch in CHALLENGES:
            cur.execute('INSERT OR IGNORE INTO challenge_done(user_id, title, done) VALUES(?, ?, 0)', (new_user['id'], ch['title']))
        c.commit()
    finally:
        c.close()
        
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
