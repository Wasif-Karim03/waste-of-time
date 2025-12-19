"""Modern web UI for job search with user authentication."""

import io
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_file,
    session,
    url_for,
)

from app.config import get_settings
from app.connectors.greenhouse import fetch as fetch_greenhouse
from app.connectors.indeed_rss import fetch as fetch_indeed
from app.connectors.lever import fetch as fetch_lever
from app.connectors.linkedin_rss import fetch as fetch_linkedin
from app.connectors.glassdoor_rss import fetch as fetch_glassdoor
from app.connectors.handshake_rss import fetch as fetch_handshake
from app.core.freshness import filter_fresh
from app.core.ids import deduplicate_jobs
from app.core.keywords import sort_jobs, tag_job
from app.core.normalize import normalize_all
from app.core.rss_matcher import match_indeed_feeds, match_rss_feeds
from app.export_csv import export_jobs_to_csv
from app.resume_parser import parse_resume
from app.storage.user_store import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_count,
    init_user_db,
    verify_user,
)
from app.storage.user_activity import (
    init_activity_db,
    save_search,
    save_resume,
    get_user_searches,
    get_user_resumes,
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize user database
# Use environment variables for production, fallback to local paths for development
USER_DB_PATH = os.environ.get('USER_DB_PATH', './users.db')
ACTIVITY_DB_PATH = os.environ.get('ACTIVITY_DB_PATH', './user_activity.db')
init_user_db(USER_DB_PATH)
init_activity_db(ACTIVITY_DB_PATH)


# Landing page template
LANDING_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>un!mployed - Find Your Next Opportunity</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #fafafa;
            color: #1a1a1a;
            line-height: 1.6;
        }
        .navbar {
            padding: 24px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a1a1a;
            letter-spacing: -0.5px;
        }
        .nav-links {
            display: flex;
            gap: 30px;
            align-items: center;
        }
        .nav-links a {
            color: #666;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }
        .nav-links a:hover {
            color: #1a1a1a;
        }
        .btn-primary {
            background: #1a1a1a;
            color: white;
            padding: 12px 28px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .btn-primary:hover {
            background: #333;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transform: translateY(-1px);
        }
        .hero {
            max-width: 1200px;
            margin: 0 auto;
            padding: 120px 40px 100px;
            text-align: center;
            background: #ffffff;
            border-radius: 0 0 24px 24px;
            margin-bottom: 40px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
        }
        .hero h1 {
            font-size: 4.5rem;
            font-weight: 800;
            margin-bottom: 28px;
            letter-spacing: -2px;
            line-height: 1.1;
            background: linear-gradient(180deg, #1a1a1a 0%, #3a3a3a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero p {
            font-size: 1.3rem;
            color: #666;
            margin-bottom: 32px;
            max-width: 650px;
            margin-left: auto;
            margin-right: auto;
            font-weight: 400;
            line-height: 1.7;
        }
        .user-count-display {
            margin: 50px 0;
            padding: 50px 60px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f8f8 50%, #ffffff 100%);
            border-radius: 24px;
            border: 3px solid transparent;
            background-clip: padding-box;
            display: inline-block;
            animation: fadeInUp 0.8s ease-out, shimmer 3s ease-in-out infinite;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08), 
                        0 0 0 1px rgba(0, 0, 0, 0.05),
                        inset 0 1px 0 rgba(255, 255, 255, 0.9);
            position: relative;
            overflow: hidden;
        }
        .user-count-display::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            animation: shine 3s infinite;
        }
        .user-count-number {
            font-size: 5.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #1a1a1a 0%, #3a3a3a 50%, #1a1a1a 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: inline-block;
            line-height: 1;
            margin-right: 12px;
            animation: countUp 1.5s cubic-bezier(0.34, 1.56, 0.64, 1), 
                       gradientShift 3s ease infinite;
            position: relative;
            text-shadow: 0 0 30px rgba(0, 0, 0, 0.1);
            letter-spacing: -2px;
        }
        .user-count-number::after {
            content: '+';
            font-size: 4rem;
            vertical-align: top;
            margin-left: 6px;
            background: linear-gradient(135deg, #1a1a1a 0%, #3a3a3a 50%, #1a1a1a 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 3s ease infinite;
        }
        .user-count-text {
            font-size: 1.5rem;
            color: #555;
            margin-top: 16px;
            font-weight: 600;
            letter-spacing: -0.3px;
            animation: fadeInText 1s ease-out 0.5s both;
        }
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(40px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        @keyframes countUp {
            0% {
                opacity: 0;
                transform: scale(0.3) rotate(-5deg);
            }
            50% {
                transform: scale(1.1) rotate(2deg);
            }
            100% {
                opacity: 1;
                transform: scale(1) rotate(0deg);
            }
        }
        @keyframes gradientShift {
            0%, 100% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
        }
        @keyframes shimmer {
            0%, 100% {
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08), 
                            0 0 0 1px rgba(0, 0, 0, 0.05),
                            inset 0 1px 0 rgba(255, 255, 255, 0.9);
            }
            50% {
                box-shadow: 0 16px 50px rgba(0, 0, 0, 0.12), 
                            0 0 0 1px rgba(0, 0, 0, 0.08),
                            inset 0 1px 0 rgba(255, 255, 255, 0.9);
            }
        }
        @keyframes shine {
            0% {
                transform: translateX(-100%) translateY(-100%) rotate(45deg);
            }
            100% {
                transform: translateX(100%) translateY(100%) rotate(45deg);
            }
        }
        @keyframes fadeInText {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
                border-color: transparent;
            }
            50% {
                transform: scale(1.02);
                border-color: #1a1a1a;
            }
        }
        .user-count-display:hover {
            animation: pulse 1.5s ease-in-out infinite, shimmer 3s ease-in-out infinite;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 
                        0 0 0 2px rgba(26, 26, 26, 0.1),
                        inset 0 1px 0 rgba(255, 255, 255, 0.9);
            transform: translateY(-4px);
        }
        .user-count-display:hover .user-count-number {
            transform: scale(1.05);
        }
        .hero-buttons {
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn-large {
            padding: 18px 36px;
            font-size: 1.1rem;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: -0.2px;
        }
        .btn-large:hover {
            transform: translateY(-3px);
        }
        .btn-large-primary {
            background: #1a1a1a;
            color: white;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        }
        .btn-large-primary:hover {
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
            background: #2a2a2a;
        }
        .btn-large-secondary {
            background: #ffffff;
            color: #1a1a1a;
            border: 2px solid #1a1a1a;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        .btn-large-secondary:hover {
            background: #1a1a1a;
            color: white;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        }
        .features {
            max-width: 1200px;
            margin: 0 auto;
            padding: 100px 40px;
            background: #ffffff;
            border-radius: 24px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
            margin-bottom: 40px;
        }
        .features-header {
            text-align: center;
            margin-bottom: 80px;
        }
        .features-header h2 {
            font-size: 2.75rem;
            font-weight: 800;
            margin-bottom: 20px;
            letter-spacing: -1px;
            color: #1a1a1a;
        }
        .features-header p {
            font-size: 1.25rem;
            color: #666;
            font-weight: 400;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 32px;
            max-width: 1100px;
            margin: 0 auto;
        }
        .feature-card {
            padding: 48px 40px;
            border: 1px solid #e8e8e8;
            border-radius: 16px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            background: #ffffff;
            position: relative;
            overflow: hidden;
        }
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #1a1a1a, #4a4a4a);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .feature-card:hover {
            border-color: #1a1a1a;
            transform: translateY(-8px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
        }
        .feature-card:hover::before {
            transform: scaleX(1);
        }
        .feature-card h3 {
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: #1a1a1a;
            letter-spacing: -0.3px;
        }
        .feature-card p {
            color: #666;
            line-height: 1.75;
            font-size: 1.05rem;
            flex: 1;
        }
        @media (max-width: 1024px) {
            .features-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        @media (max-width: 640px) {
            .features-grid {
                grid-template-columns: 1fr;
            }
            .feature-card {
                padding: 36px 32px;
            }
        }
        .cta {
            max-width: 1200px;
            margin: 0 auto;
            padding: 100px 40px;
            text-align: center;
            background: linear-gradient(180deg, #1a1a1a 0%, #2a2a2a 100%);
            border-radius: 24px;
            margin-bottom: 80px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
            position: relative;
            overflow: hidden;
        }
        .cta::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.05) 0%, transparent 50%);
        }
        .cta h2 {
            font-size: 2.75rem;
            font-weight: 800;
            margin-bottom: 20px;
            color: #ffffff;
            letter-spacing: -1px;
            position: relative;
            z-index: 1;
        }
        .cta p {
            font-size: 1.25rem;
            color: rgba(255, 255, 255, 0.85);
            margin-bottom: 48px;
            position: relative;
            z-index: 1;
        }
        .cta-user-count {
            font-size: 4.5rem;
            font-weight: 900;
            color: #ffffff;
            margin: 30px 0;
            display: inline-block;
            animation: countUp 1.5s cubic-bezier(0.34, 1.56, 0.64, 1), 
                       glow 2s ease-in-out infinite;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.3),
                         0 0 40px rgba(255, 255, 255, 0.2),
                         0 4px 8px rgba(0, 0, 0, 0.3);
            letter-spacing: -2px;
        }
        .cta-user-count::after {
            content: '+';
            font-size: 3.5rem;
            vertical-align: top;
            margin-left: 6px;
        }
        @keyframes glow {
            0%, 100% {
                text-shadow: 0 0 20px rgba(255, 255, 255, 0.3),
                             0 0 40px rgba(255, 255, 255, 0.2),
                             0 4px 8px rgba(0, 0, 0, 0.3);
            }
            50% {
                text-shadow: 0 0 30px rgba(255, 255, 255, 0.5),
                             0 0 60px rgba(255, 255, 255, 0.3),
                             0 4px 8px rgba(0, 0, 0, 0.3);
            }
        }
        .cta .btn-large-primary {
            background: #ffffff;
            color: #1a1a1a;
            position: relative;
            z-index: 1;
        }
        .cta .btn-large-primary:hover {
            background: #f5f5f5;
            color: #1a1a1a;
        }
        footer {
            border-top: 1px solid #e8e8e8;
            padding: 50px 40px;
            text-align: center;
            color: #999;
            background: #ffffff;
            margin-top: 40px;
        }
        @media (max-width: 768px) {
            .hero h1 {
                font-size: 2.5rem;
            }
            .hero p {
                font-size: 1.1rem;
            }
            .navbar {
                padding: 20px;
            }
            .nav-links {
                gap: 16px;
            }
            .features {
                padding: 60px 20px;
            }
            .features-header {
                margin-bottom: 50px;
            }
            .features-header h2 {
                font-size: 2rem;
            }
            .features-header p {
                font-size: 1rem;
            }
            .user-count-display {
                padding: 30px 20px;
            }
            .user-count-number {
                font-size: 3.5rem;
            }
            .user-count-number::after {
                font-size: 2.5rem;
            }
            .user-count-text {
                font-size: 1.1rem;
            }
            .cta-user-count {
                font-size: 2.5rem;
            }
            .cta-user-count::after {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">un!mployed</div>
        <div class="nav-links">
            <a href="#features">Features</a>
            <a href="/auth">Sign In</a>
            <a href="/auth" class="btn-primary">Get Started</a>
        </div>
    </nav>
    
    <section class="hero">
        <h1>Find Your Next<br>Opportunity</h1>
        <p>Search thousands of job listings from top companies. Get intelligent matches, filter by location, and export results instantly.</p>
        
        <div class="user-count-display">
            <div class="user-count-number">{{ user_count }}</div>
            <div class="user-count-text">users already searching<br>for their dream jobs</div>
        </div>
        
        <div class="hero-buttons">
            <a href="/auth" class="btn-large btn-large-primary">Get Started</a>
            <a href="#features" class="btn-large btn-large-secondary">Learn More</a>
        </div>
    </section>
    
    <section class="features" id="features">
        <div class="features-header">
            <h2>Everything you need to find your dream job</h2>
            <p>Powerful features designed to make job searching effortless</p>
        </div>
        <div class="features-grid">
            <div class="feature-card">
                <h3>Newly Posted Jobs</h3>
                <p>Find the freshest job opportunities as soon as they're posted. Filter by time windows from 24 hours to 30 days to discover the latest openings across hundreds of companies and job boards.</p>
            </div>
            <div class="feature-card">
                <h3>Resume Keyword Matching</h3>
                <p>Our intelligent system analyzes your resume keywords and matches them to relevant job listings. Enter your skills and experience, and we'll find jobs that align with your background.</p>
            </div>
            <div class="feature-card">
                <h3>Resume Match Scores</h3>
                <p>Every job listing includes a match score that shows how well it aligns with your resume keywords. Jobs are automatically sorted by relevance, so the best matches appear first.</p>
            </div>
        </div>
    </section>
    
    <section class="cta">
        <h2>Ready to find your next role?</h2>
        <div class="cta-user-count">{{ user_count }}</div>
        <p>job seekers using un!mployed to discover their next opportunity</p>
        <a href="/auth" class="btn-large btn-large-primary">Get Started Free</a>
    </section>
    
    <footer>
        <p>&copy; 2025 un!mployed. All rights reserved.</p>
    </footer>
</body>
</html>
"""

# Auth page template (sign in/sign up)
AUTH_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign In - un!mployed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #ffffff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            color: #1a1a1a;
        }
        .container {
            width: 100%;
            max-width: 420px;
        }
        .logo {
            text-align: center;
            margin-bottom: 50px;
        }
        .logo a {
            font-size: 2.5rem;
            font-weight: 600;
            color: #1a1a1a;
            text-decoration: none;
            letter-spacing: -0.5px;
        }
        .auth-card {
            background: #ffffff;
            border: 1px solid #e5e5e5;
            border-radius: 12px;
            padding: 40px;
        }
        .tabs {
            display: flex;
            margin-bottom: 32px;
            border-bottom: 1px solid #e5e5e5;
        }
        .tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            font-weight: 500;
            color: #999;
            transition: color 0.2s;
            border: none;
            background: none;
            font-size: 0.95rem;
            position: relative;
        }
        .tab.active {
            color: #1a1a1a;
        }
        .tab.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 2px;
            background: #1a1a1a;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #1a1a1a;
            font-size: 0.9rem;
        }
        input[type="text"],
        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            font-size: 0.95rem;
            transition: border-color 0.2s;
            background: #fff;
            color: #1a1a1a;
        }
        input:focus {
            outline: none;
            border-color: #1a1a1a;
        }
        input::placeholder {
            color: #999;
        }
        small {
            display: block;
            margin-top: 6px;
            font-size: 0.85rem;
            color: #999;
        }
        button[type="submit"] {
            width: 100%;
            padding: 12px;
            background: #1a1a1a;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 8px;
        }
        button[type="submit"]:hover {
            background: #333;
        }
        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 0.9rem;
        }
        .alert-success {
            background: #f0f9f4;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        .alert-error {
            background: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        @media (max-width: 480px) {
            .auth-card {
                padding: 32px 24px;
            }
            .logo a {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <a href="/">un!mployed</a>
        </div>
        
        <div class="auth-card">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('login')">Sign In</button>
                <button class="tab" onclick="switchTab('signup')">Sign Up</button>
            </div>
            
            {% if message %}
            <div class="alert alert-{{ message_type }}">
                {{ message }}
            </div>
            {% endif %}
            
            <div id="login-tab" class="tab-content active">
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label for="login-email">Email</label>
                        <input type="email" id="login-email" name="email" placeholder="you@example.com" required>
                    </div>
                    <div class="form-group">
                        <label for="login-password">Password</label>
                        <input type="password" id="login-password" name="password" placeholder="••••••••" required>
                    </div>
                    <button type="submit">Sign In</button>
                </form>
            </div>
            
            <div id="signup-tab" class="tab-content">
                <form method="POST" action="/signup">
                    <div class="form-group">
                        <label for="signup-name">Name</label>
                        <input type="text" id="signup-name" name="name" placeholder="John Doe" required>
                    </div>
                    <div class="form-group">
                        <label for="signup-email">Email</label>
                        <input type="email" id="signup-email" name="email" placeholder="you@example.com" required>
                    </div>
                    <div class="form-group">
                        <label for="signup-password">Password</label>
                        <input type="password" id="signup-password" name="password" placeholder="••••••••" minlength="6" required>
                        <small>Minimum 6 characters</small>
                    </div>
                    <button type="submit">Create Account</button>
                </form>
            </div>
        </div>
    </div>
    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(tab + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

# Search page template (existing functionality)
SEARCH_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Search - un!mployed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #fafafa;
            color: #1a1a1a;
            min-height: 100vh;
        }
        .navbar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a1a1a;
            letter-spacing: -0.5px;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .user-info span {
            color: #666;
            font-weight: 500;
        }
        .logout-btn, .admin-btn {
            background: #1a1a1a;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .logout-btn:hover, .admin-btn:hover {
            background: #333;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .main-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 40px;
        }
        .page-header {
            text-align: left;
            margin-bottom: 80px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        .page-header h1 {
            font-size: 4rem;
            font-weight: 900;
            margin-bottom: 24px;
            letter-spacing: -3px;
            line-height: 1.1;
            color: #1a1a1a;
        }
        .page-header p {
            font-size: 1.25rem;
            color: #666;
            font-weight: 400;
            letter-spacing: -0.2px;
            line-height: 1.6;
        }
        .search-card {
            max-width: 800px;
            margin: 0 auto;
            animation: fadeInUp 0.8s ease-out;
        }
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        form {
            display: grid;
            gap: 48px;
        }
        .form-group {
            position: relative;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
        }
        label {
            display: block;
            margin-bottom: 16px;
            font-weight: 700;
            color: #1a1a1a;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 1.2px;
        }
        .input-wrapper {
            position: relative;
        }
        .autocomplete-wrapper {
            position: relative;
            width: 100%;
        }
        .autocomplete-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #d0d0d0;
            border-top: none;
            max-height: 320px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
            display: none;
            animation: fadeInDown 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            margin-top: -1px;
        }
        .autocomplete-dropdown.active {
            display: block;
        }
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-8px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        .autocomplete-item {
            padding: 14px 0;
            padding-left: 20px;
            padding-right: 20px;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border-bottom: 1px solid #f0f0f0;
            color: #1a1a1a;
            font-size: 1rem;
            font-weight: 400;
            line-height: 1.5;
            position: relative;
            display: flex;
            align-items: center;
            letter-spacing: -0.2px;
        }
        .autocomplete-item::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 0;
            background: linear-gradient(90deg, #1a1a1a 0%, transparent 100%);
            transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            opacity: 0.05;
        }
        .autocomplete-item:hover {
            background: linear-gradient(90deg, #f9f9f9 0%, #ffffff 100%);
            padding-left: 24px;
            transform: translateX(2px);
        }
        .autocomplete-item:hover::before {
            width: 3px;
        }
        .autocomplete-item.selected {
            background: linear-gradient(90deg, #f5f5f5 0%, #ffffff 100%);
            padding-left: 24px;
            transform: translateX(2px);
        }
        .autocomplete-item.selected::before {
            width: 3px;
        }
        .autocomplete-item:last-child {
            border-bottom: none;
        }
        .autocomplete-item strong {
            font-weight: 700;
            color: #1a1a1a;
            background: linear-gradient(135deg, #1a1a1a 0%, #3a3a3a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        /* Custom scrollbar for autocomplete */
        .autocomplete-dropdown::-webkit-scrollbar {
            width: 6px;
        }
        .autocomplete-dropdown::-webkit-scrollbar-track {
            background: #f9f9f9;
        }
        .autocomplete-dropdown::-webkit-scrollbar-thumb {
            background: #d0d0d0;
            border-radius: 3px;
        }
        .autocomplete-dropdown::-webkit-scrollbar-thumb:hover {
            background: #b0b0b0;
        }
        input[type="text"], select {
            width: 100%;
            padding: 18px 0;
            border: none;
            border-bottom: 1px solid #d0d0d0;
            font-size: 1.125rem;
            box-sizing: border-box;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: transparent;
            color: #1a1a1a;
            font-weight: 400;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border-bottom-color: #1a1a1a;
            border-bottom-width: 2px;
            padding-bottom: 17px;
        }
        select {
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'%3E%3Cpath fill='%231a1a1a' d='M7 10L2 5h10z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right center;
            background-size: 14px;
            padding-right: 24px;
        }
        input::placeholder {
            color: #aaa;
            font-weight: 400;
        }
        small {
            display: block;
            margin-top: 12px;
            font-size: 0.8125rem;
            color: #888;
            font-weight: 400;
            letter-spacing: 0;
        }
        .checkbox-wrapper {
            position: relative;
            padding-top: 8px;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 0;
            background: transparent;
            border: none;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .checkbox-group:hover {
            opacity: 0.7;
        }
        .custom-checkbox {
            position: relative;
            width: 22px;
            height: 22px;
            flex-shrink: 0;
        }
        .custom-checkbox input[type="checkbox"] {
            position: absolute;
            opacity: 0;
            width: 22px;
            height: 22px;
            cursor: pointer;
            margin: 0;
        }
        .checkmark {
            position: absolute;
            top: 0;
            left: 0;
            width: 22px;
            height: 22px;
            border: 2px solid #1a1a1a;
            border-radius: 3px;
            background: transparent;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .custom-checkbox input[type="checkbox"]:checked ~ .checkmark {
            background: #1a1a1a;
            border-color: #1a1a1a;
        }
        .checkmark::after {
            content: '';
            position: absolute;
            display: none;
            left: 6px;
            top: 2px;
            width: 5px;
            height: 10px;
            border: solid white;
            border-width: 0 2px 2px 0;
            transform: rotate(45deg);
        }
        .custom-checkbox input[type="checkbox"]:checked ~ .checkmark::after {
            display: block;
        }
        .checkbox-group label {
            margin: 0;
            cursor: pointer;
            font-weight: 500;
            color: #1a1a1a;
            font-size: 1rem;
            text-transform: none;
            letter-spacing: -0.2px;
        }
        .file-upload-wrapper {
            margin-top: 8px;
        }
        .file-upload-label {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px;
            border: 2px dashed #e5e5e5;
            border-radius: 8px;
            background: #fafafa;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 0;
        }
        .file-upload-label:hover {
            border-color: #1a1a1a;
            background: #f5f5f5;
        }
        .file-upload-label.dragover {
            border-color: #1a1a1a;
            background: #f0f0f0;
        }
        .file-upload-icon {
            font-size: 1.5rem;
            flex-shrink: 0;
        }
        .file-upload-text {
            color: #666;
            font-size: 0.95rem;
            flex: 1;
        }
        .file-upload-label.has-file .file-upload-text {
            color: #1a1a1a;
            font-weight: 500;
        }
        .resume-analysis-container {
            background: #fafafa;
            border: 2px solid #e5e5e5;
            border-radius: 12px;
            padding: 25px;
            margin-top: 20px;
            animation: fadeIn 0.3s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes simpleFadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        .resume-analysis-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #1a1a1a;
        }
        .resume-analysis-header h3 {
            font-size: 1.3rem;
            color: #1a1a1a;
            margin: 0;
            font-weight: 600;
        }
        .resume-filename {
            color: #666;
            font-size: 0.9rem;
            font-weight: 500;
            padding: 6px 12px;
            background: #f0f0f0;
            border-radius: 20px;
        }
        .resume-analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        .resume-analysis-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border: 1px solid #e5e5e5;
        }
        .resume-analysis-card.full-width {
            grid-column: 1 / -1;
        }
        .resume-analysis-card h4 {
            font-size: 1rem;
            margin-bottom: 12px;
            color: #1a1a1a;
            font-weight: 600;
        }
        .skill-tags-container, .keyword-tags-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .skill-tag-display, .keyword-tag-display {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
            display: inline-block;
            opacity: 0;
            animation: simpleFadeIn 0.3s ease-out forwards;
        }
        .skill-tag-display {
            background: #1a1a1a;
            color: white;
            border: none;
        }
        .skill-tag-display.soft {
            background: #666;
            color: white;
        }
        .keyword-tag-display {
            background: #f0f0f0;
            color: #1a1a1a;
            border: 1px solid #e5e5e5;
        }
        .info-container {
            color: #1a1a1a;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .info-container .info-item {
            margin-bottom: 8px;
        }
        .empty-message {
            color: #999;
            font-style: italic;
            font-size: 0.9rem;
            padding: 20px;
            text-align: center;
        }
        .submit-wrapper {
            margin-top: 32px;
            padding-top: 32px;
            border-top: 1px solid #e5e5e5;
        }
        button[type="submit"] {
            background: #1a1a1a;
            color: white;
            padding: 20px 56px;
            border: none;
            border-radius: 0;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            width: auto;
            min-width: 200px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            letter-spacing: 0.5px;
            text-transform: uppercase;
            position: relative;
            overflow: hidden;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        button[type="submit"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
            transition: left 0.6s;
        }
        button[type="submit"]:hover::before {
            left: 100%;
        }
        button[type="submit"]:hover {
            background: #2a2a2a;
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }
        button[type="submit"]:active {
            transform: translateY(-1px);
        }
        button[type="submit"]::after {
            content: '→';
            font-size: 1.2rem;
            transition: transform 0.3s ease;
        }
        button[type="submit"]:hover::after {
            transform: translateX(4px);
        }
        .alert {
            margin-top: 30px;
            padding: 20px 24px;
            border-radius: 12px;
            font-size: 1rem;
            animation: fadeInUp 0.4s ease-out;
        }
        .info {
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            color: #1565c0;
        }
        .error {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            color: #c62828;
        }
        .success {
            background-color: #e8f5e9;
            border-left: 4px solid #4CAF50;
            color: #2e7d32;
            padding: 40px;
            margin-top: 32px;
            border-radius: 0;
            animation: fadeInUp 0.6s ease-out;
        }
        .success strong {
            display: block;
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 12px;
            color: #2e7d32;
            letter-spacing: -0.3px;
        }
        .success p {
            margin-bottom: 24px;
            color: #388e3c;
            font-size: 1rem;
        }
        .success a {
            display: inline-block;
            background: #1a1a1a;
            color: white;
            padding: 16px 32px;
            border-radius: 0;
            font-weight: 700;
            text-decoration: none;
            margin-top: 8px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.875rem;
            position: relative;
            overflow: hidden;
        }
        .success a::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        .success a:hover::before {
            left: 100%;
        }
        .success a:hover {
            background: #2a2a2a;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        /* Loading Overlay */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.99) 0%, rgba(250, 250, 250, 0.99) 100%);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            z-index: 9999;
            display: none;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            opacity: 0;
            transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .loading-overlay.active {
            display: flex;
            opacity: 1;
        }
        .loading-content {
            text-align: center;
            max-width: 600px;
            padding: 60px 40px;
            position: relative;
            animation: fadeInScale 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        @keyframes fadeInScale {
            from {
                opacity: 0;
                transform: scale(0.95) translateY(20px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }
        .loading-spinner {
            width: 80px;
            height: 80px;
            margin: 0 auto 40px;
            position: relative;
        }
        .spinner-circle {
            width: 100%;
            height: 100%;
            border: 5px solid transparent;
            border-top: 5px solid #1a1a1a;
            border-right: 5px solid #1a1a1a;
            border-radius: 50%;
            animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
            box-shadow: 0 0 20px rgba(26, 26, 26, 0.1);
        }
        .spinner-inner {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 50px;
            height: 50px;
            border: 4px solid transparent;
            border-top: 4px solid #1a1a1a;
            border-left: 4px solid #1a1a1a;
            border-radius: 50%;
            animation: spin 0.9s cubic-bezier(0.5, 0, 0.5, 1) infinite reverse;
        }
        .spinner-core {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 24px;
            height: 24px;
            background: #1a1a1a;
            border-radius: 50%;
            animation: pulse 2s ease-in-out infinite;
            box-shadow: 0 0 15px rgba(26, 26, 26, 0.3);
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
            0%, 100% {
                transform: translate(-50%, -50%) scale(1);
                opacity: 1;
            }
            50% {
                transform: translate(-50%, -50%) scale(1.1);
                opacity: 0.8;
            }
        }
        .loading-text {
            font-size: 1.75rem;
            font-weight: 800;
            background: linear-gradient(135deg, #1a1a1a 0%, #3a3a3a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 12px;
            letter-spacing: -1px;
            min-height: 2.5rem;
            animation: textFade 0.5s ease;
        }
        @keyframes textFade {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .loading-subtext {
            font-size: 1.05rem;
            color: #666;
            line-height: 1.7;
            min-height: 3.5rem;
            font-weight: 400;
            letter-spacing: -0.2px;
            animation: textFade 0.5s ease 0.1s backwards;
        }
        .platform-list {
            margin-top: 40px;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 12px;
            max-width: 600px;
        }
        .platform-tag {
            padding: 10px 20px;
            background: linear-gradient(135deg, #f8f8f8 0%, #f0f0f0 100%);
            border: 2px solid #e8e8e8;
            border-radius: 50px;
            font-size: 0.875rem;
            font-weight: 700;
            color: #999;
            opacity: 0.5;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: 0.5px;
            text-transform: uppercase;
            position: relative;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }
        .platform-tag::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
            transition: left 0.6s;
        }
        .platform-tag.active {
            opacity: 1;
            background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            color: white;
            border-color: #1a1a1a;
            transform: translateY(-4px) scale(1.05);
            box-shadow: 0 8px 24px rgba(26, 26, 26, 0.25), 0 4px 12px rgba(26, 26, 26, 0.15);
        }
        .platform-tag.active::before {
            left: 100%;
        }
        .platform-tag.active::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 50px;
            padding: 2px;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0));
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            animation: shimmer 2s infinite;
        }
        @keyframes shimmer {
            0% {
                background-position: -200% 0;
            }
            100% {
                background-position: 200% 0;
            }
        }
        .loading-dots {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            margin-top: 32px;
            height: 16px;
        }
        .loading-dots span {
            width: 10px;
            height: 10px;
            background: linear-gradient(135deg, #1a1a1a 0%, #3a3a3a 100%);
            border-radius: 50%;
            animation: dotsBounce 1.4s infinite ease-in-out;
            box-shadow: 0 2px 8px rgba(26, 26, 26, 0.2);
        }
        .loading-dots span:nth-child(1) {
            animation-delay: 0s;
        }
        .loading-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .loading-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes dotsBounce {
            0%, 80%, 100% {
                transform: translateY(0) scale(0.8);
                opacity: 0.4;
            }
            40% {
                transform: translateY(-12px) scale(1.1);
                opacity: 1;
            }
        }
        @media (max-width: 768px) {
            .main-container {
                padding: 40px 20px;
            }
            .navbar {
                padding: 15px 20px;
            }
            .user-info {
                gap: 10px;
            }
            .user-info span {
                display: none;
            }
            .page-header {
                text-align: left;
                margin-bottom: 50px;
            }
            .page-header h1 {
                font-size: 2.5rem;
                letter-spacing: -2px;
            }
            .page-header p {
                font-size: 1.1rem;
            }
            .form-row {
                grid-template-columns: 1fr;
                gap: 48px;
            }
            .search-card {
                padding: 0;
            }
            button[type="submit"] {
                width: 100%;
            }
            .loading-text {
                font-size: 1.25rem;
            }
            .loading-subtext {
                font-size: 0.9rem;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">un!mployed</div>
        <div class="user-info">
            <span>Welcome, {{ user_name }}!</span>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </nav>
    
    <div class="main-container">
        <div class="page-header">
            <h1>Find Your Dream Job</h1>
            <p>Search across thousands of opportunities from top companies</p>
        </div>
        
        <div class="search-card">
            <form method="POST" action="/search" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="role">Job Role / Keywords</label>
                    <div class="autocomplete-wrapper">
                        <div class="input-wrapper">
                            <input 
                                type="text" 
                                id="role" 
                                name="role" 
                                placeholder="Software engineer, Python developer, Data scientist"
                                value="{{ role if role else '' }}"
                                autocomplete="off"
                                required
                            >
                        </div>
                        <div class="autocomplete-dropdown" id="roleAutocomplete"></div>
                    </div>
                    <small>Separate multiple keywords with commas</small>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="time_window">Time Window</label>
                        <div class="input-wrapper">
                            <select id="time_window" name="time_window">
                                <option value="24" {{ 'selected' if time_window == '24' else '' }}>Last 24 hours</option>
                                <option value="48" {{ 'selected' if time_window == '48' or not time_window else '' }}>Last 48 hours</option>
                                <option value="72" {{ 'selected' if time_window == '72' else '' }}>Last 72 hours</option>
                                <option value="168" {{ 'selected' if time_window == '168' else '' }}>Last 1 week</option>
                                <option value="336" {{ 'selected' if time_window == '336' else '' }}>Last 2 weeks</option>
                                <option value="504" {{ 'selected' if time_window == '504' else '' }}>Last 3 weeks</option>
                                <option value="720" {{ 'selected' if time_window == '720' else '' }}>Last 1 month</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="location">Location <span style="color: #999; font-weight: 400; text-transform: none; letter-spacing: 0;">(optional)</span></label>
                        <div class="autocomplete-wrapper">
                            <div class="input-wrapper">
                                <input 
                                    type="text" 
                                    id="location" 
                                    name="location" 
                                    placeholder="San Francisco, Remote, New York"
                                    value="{{ location if location else '' }}"
                                    autocomplete="off"
                                >
                            </div>
                            <div class="autocomplete-dropdown" id="locationAutocomplete"></div>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <div class="checkbox-wrapper">
                        <div class="checkbox-group">
                            <div class="custom-checkbox">
                                <input type="checkbox" id="remote_only" name="remote_only" value="1" {{ 'checked' if remote_only else '' }}>
                                <span class="checkmark"></span>
                            </div>
                            <label for="remote_only">Show only remote jobs</label>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="resume">Upload Your Resume <span style="color: #999; font-weight: 400; text-transform: none; letter-spacing: 0;">(optional)</span></label>
                    <div class="file-upload-wrapper">
                        <input 
                            type="file" 
                            id="resume" 
                            name="resume" 
                            accept=".pdf,.doc,.docx,.txt"
                            style="display: none;"
                        >
                        <label for="resume" class="file-upload-label">
                            <span class="file-upload-icon"></span>
                            <span class="file-upload-text" id="fileUploadText">Choose file or drag it here</span>
                        </label>
                    </div>
                    <small>Supported formats: PDF, DOC, DOCX, TXT</small>
                </div>
                
                <div class="submit-wrapper">
                    <button type="submit">Search & Export CSV</button>
                </div>
            </form>
            
            {% if message %}
                <div class="alert {{ message_type }}">
                    {{ message }}
                </div>
            {% endif %}
            
        </div>
    </div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
            <div class="loading-content">
            <div class="loading-spinner">
                <div class="spinner-circle"></div>
                <div class="spinner-inner"></div>
                <div class="spinner-core"></div>
            </div>
            <div class="loading-text" id="loadingStatus">Searching Jobs</div>
            <div class="loading-subtext" id="loadingSubtext">Fetching latest opportunities from all platforms</div>
            <div class="platform-list">
                <span class="platform-tag" id="platform-linkedin">LinkedIn</span>
                <span class="platform-tag" id="platform-indeed">Indeed</span>
                <span class="platform-tag" id="platform-glassdoor">Glassdoor</span>
                <span class="platform-tag" id="platform-handshake">Handshake</span>
                <span class="platform-tag" id="platform-greenhouse">Greenhouse</span>
                <span class="platform-tag" id="platform-lever">Lever</span>
            </div>
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    </div>
    
    <script>
        // Job role suggestions
        const jobRoleSuggestions = [
            'Software Engineer', 'Software Developer', 'Full Stack Developer',
            'Frontend Developer', 'Backend Developer', 'DevOps Engineer',
            'Python Developer', 'JavaScript Developer', 'Java Developer',
            'React Developer', 'Node.js Developer', 'Data Scientist',
            'Data Engineer', 'Data Analyst', 'Machine Learning Engineer',
            'AI Engineer', 'Cloud Engineer', 'Security Engineer',
            'Mobile Developer', 'iOS Developer', 'Android Developer',
            'Product Manager', 'Project Manager', 'Product Designer',
            'UI/UX Designer', 'Graphic Designer', 'Marketing Manager',
            'Sales Manager', 'Business Analyst', 'Financial Analyst',
            'Accountant', 'HR Manager', 'Operations Manager',
            'Customer Success', 'QA Engineer', 'QA Tester',
            'System Administrator', 'Database Administrator', 'Network Engineer',
            'Computer Vision', 'Embedded Systems', 'Robotics Engineer',
            'Blockchain Developer', 'Game Developer', 'Web Developer'
        ];
        
        // Location suggestions
        const locationSuggestions = [
            'Remote', 'San Francisco, CA', 'New York, NY', 'Los Angeles, CA',
            'Chicago, IL', 'Boston, MA', 'Seattle, WA', 'Austin, TX',
            'Denver, CO', 'Portland, OR', 'Washington, DC', 'Atlanta, GA',
            'Miami, FL', 'Dallas, TX', 'Houston, TX', 'Phoenix, AZ',
            'Philadelphia, PA', 'San Diego, CA', 'Minneapolis, MN',
            'Detroit, MI', 'Charlotte, NC', 'Nashville, TN', 'Raleigh, NC',
            'Salt Lake City, UT', 'Orlando, FL', 'Tampa, FL', 'San Jose, CA',
            'Indianapolis, IN', 'Columbus, OH', 'USA', 'United States',
            'Canada', 'Toronto, ON', 'Vancouver, BC', 'London, UK',
            'New York', 'California', 'Texas', 'Florida',
            // All 50 US States
            'Alabama', 'AL', 'Alaska', 'AK', 'Arizona', 'AZ', 'Arkansas', 'AR',
            'California', 'CA', 'Colorado', 'CO', 'Connecticut', 'CT', 'Delaware', 'DE',
            'Florida', 'FL', 'Georgia', 'GA', 'Hawaii', 'HI', 'Idaho', 'ID',
            'Illinois', 'IL', 'Indiana', 'IN', 'Iowa', 'IA', 'Kansas', 'KS',
            'Kentucky', 'KY', 'Louisiana', 'LA', 'Maine', 'ME', 'Maryland', 'MD',
            'Massachusetts', 'MA', 'Michigan', 'MI', 'Minnesota', 'MN', 'Mississippi', 'MS',
            'Missouri', 'MO', 'Montana', 'MT', 'Nebraska', 'NE', 'Nevada', 'NV',
            'New Hampshire', 'NH', 'New Jersey', 'NJ', 'New Mexico', 'NM', 'New York', 'NY',
            'North Carolina', 'NC', 'North Dakota', 'ND', 'Ohio', 'OH', 'Oklahoma', 'OK',
            'Oregon', 'OR', 'Pennsylvania', 'PA', 'Rhode Island', 'RI', 'South Carolina', 'SC',
            'South Dakota', 'SD', 'Tennessee', 'TN', 'Texas', 'TX', 'Utah', 'UT',
            'Vermont', 'VT', 'Virginia', 'VA', 'Washington', 'WA', 'West Virginia', 'WV',
            'Wisconsin', 'WI', 'Wyoming', 'WY'
        ];
        
        // Autocomplete functionality
        function setupAutocomplete(inputId, dropdownId, suggestions) {
            const input = document.getElementById(inputId);
            const dropdown = document.getElementById(dropdownId);
            let selectedIndex = -1;
            
            function filterSuggestions(query) {
                if (!query) return suggestions.slice(0, 8);
                const lowerQuery = query.toLowerCase();
                const words = lowerQuery.split(',').map(w => w.trim()).filter(w => w);
                const lastWord = words[words.length - 1] || '';
                
                return suggestions
                    .filter(suggestion => {
                        const lowerSuggestion = suggestion.toLowerCase();
                        return lowerSuggestion.includes(lastWord) && 
                               !words.slice(0, -1).some(w => lowerSuggestion.includes(w));
                    })
                    .slice(0, 8);
            }
            
            function highlightMatch(text, query) {
                if (!query) return text;
                const words = query.split(',').map(w => w.trim()).filter(w => w);
                const lastWord = words[words.length - 1] || '';
                if (!lastWord) return text;
                
                const regex = new RegExp(`(${lastWord})`, 'gi');
                return text.replace(regex, '<strong>$1</strong>');
            }
            
            function showSuggestions() {
                const value = input.value;
                const filtered = filterSuggestions(value);
                
                if (filtered.length === 0) {
                    dropdown.classList.remove('active');
                    return;
                }
                
                dropdown.innerHTML = filtered.map((suggestion, index) => {
                    const highlighted = highlightMatch(suggestion, value);
                    return `<div class="autocomplete-item" data-index="${index}" data-value="${suggestion}">${highlighted}</div>`;
                }).join('');
                
                dropdown.classList.add('active');
                selectedIndex = -1;
            }
            
            function hideSuggestions() {
                setTimeout(() => {
                    dropdown.classList.remove('active');
                }, 200);
            }
            
            function selectSuggestion(suggestion) {
                const value = input.value;
                const words = value.split(',').map(w => w.trim()).filter(w => w);
                words[words.length - 1] = suggestion;
                input.value = words.join(', ') + (words.length > 0 ? ', ' : '');
                input.focus();
                hideSuggestions();
                
                // Trigger input event to update caret position
                const event = new Event('input', { bubbles: true });
                input.dispatchEvent(event);
            }
            
            input.addEventListener('input', showSuggestions);
            input.addEventListener('focus', showSuggestions);
            input.addEventListener('blur', hideSuggestions);
            
            dropdown.addEventListener('click', (e) => {
                const item = e.target.closest('.autocomplete-item');
                if (item) {
                    selectSuggestion(item.dataset.value);
                }
            });
            
            input.addEventListener('keydown', (e) => {
                const items = dropdown.querySelectorAll('.autocomplete-item');
                
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                    items.forEach((item, idx) => {
                        if (idx === selectedIndex) {
                            item.classList.add('selected');
                        } else {
                            item.classList.remove('selected');
                        }
                    });
                    // Scroll into view if needed
                    if (selectedIndex >= 0 && items[selectedIndex]) {
                        items[selectedIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                    }
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    selectedIndex = Math.max(selectedIndex - 1, -1);
                    items.forEach((item, idx) => {
                        if (idx === selectedIndex) {
                            item.classList.add('selected');
                        } else {
                            item.classList.remove('selected');
                        }
                    });
                    // Scroll into view if needed
                    if (selectedIndex >= 0 && items[selectedIndex]) {
                        items[selectedIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                    }
                } else if (e.key === 'Enter' && selectedIndex >= 0) {
                    e.preventDefault();
                    selectSuggestion(items[selectedIndex].dataset.value);
                }
            });
        }
        
        // Initialize autocomplete on page load
        document.addEventListener('DOMContentLoaded', function() {
            setupAutocomplete('role', 'roleAutocomplete', jobRoleSuggestions);
            setupAutocomplete('location', 'locationAutocomplete', locationSuggestions);
        });
        
        (function() {
            const form = document.querySelector('form[action="/search"]');
            const loadingOverlay = document.getElementById('loadingOverlay');
            const loadingStatus = document.getElementById('loadingStatus');
            const loadingSubtext = document.getElementById('loadingSubtext');
            
            const platforms = [
                { id: 'platform-linkedin', name: 'LinkedIn', delay: 500 },
                { id: 'platform-indeed', name: 'Indeed', delay: 1500 },
                { id: 'platform-glassdoor', name: 'Glassdoor', delay: 2500 },
                { id: 'platform-handshake', name: 'Handshake', delay: 3500 },
                { id: 'platform-greenhouse', name: 'Greenhouse', delay: 4500 },
                { id: 'platform-lever', name: 'Lever', delay: 5500 }
            ];
            
            const statusMessages = [
                { text: 'Connecting to job platforms...', subtext: 'Initializing search...' },
                { text: 'Searching LinkedIn...', subtext: 'Finding opportunities on LinkedIn' },
                { text: 'Searching Indeed...', subtext: 'Scanning Indeed job listings' },
                { text: 'Searching Glassdoor...', subtext: 'Checking Glassdoor opportunities' },
                { text: 'Searching Handshake...', subtext: 'Exploring Handshake jobs' },
                { text: 'Searching Greenhouse...', subtext: 'Accessing Greenhouse boards' },
                { text: 'Searching Lever...', subtext: 'Checking Lever postings' },
                { text: 'Processing results...', subtext: 'Filtering and sorting jobs' },
                { text: 'Finalizing...', subtext: 'Preparing your CSV file' }
            ];
            
            let currentPlatformIndex = 0;
            let currentStatusIndex = 0;
            let platformInterval = null;
            let statusInterval = null;
            
            function activateNextPlatform() {
                // Deactivate previous platform
                if (currentPlatformIndex > 0) {
                    const prevPlatform = document.getElementById(platforms[currentPlatformIndex - 1].id);
                    if (prevPlatform) {
                        prevPlatform.classList.remove('active');
                    }
                }
                
                // Activate current platform
                if (currentPlatformIndex < platforms.length) {
                    const platform = document.getElementById(platforms[currentPlatformIndex].id);
                    if (platform) {
                        platform.classList.add('active');
                    }
                    currentPlatformIndex++;
                } else {
                    // All platforms checked, stop interval
                    if (platformInterval) {
                        clearInterval(platformInterval);
                    }
                }
            }
            
            function updateStatus() {
                if (currentStatusIndex < statusMessages.length) {
                    loadingStatus.textContent = statusMessages[currentStatusIndex].text;
                    loadingSubtext.textContent = statusMessages[currentStatusIndex].subtext;
                    currentStatusIndex++;
                } else {
                    // Reset or stop
                    if (statusInterval) {
                        clearInterval(statusInterval);
                    }
                }
            }
            
            function startLoadingAnimation() {
                // Reset state
                currentPlatformIndex = 0;
                currentStatusIndex = 0;
                
                // Reset all platforms
                platforms.forEach(p => {
                    const el = document.getElementById(p.id);
                    if (el) el.classList.remove('active');
                });
                
                // Start platform animation (every 800ms)
                platformInterval = setInterval(activateNextPlatform, 800);
                
                // Start status updates (every 1.5s)
                statusInterval = setInterval(updateStatus, 1500);
                
                // Initial status
                updateStatus();
            }
            
            function stopLoadingAnimation() {
                if (platformInterval) {
                    clearInterval(platformInterval);
                    platformInterval = null;
                }
                if (statusInterval) {
                    clearInterval(statusInterval);
                    statusInterval = null;
                }
                // Deactivate all platforms
                platforms.forEach(p => {
                    const el = document.getElementById(p.id);
                    if (el) el.classList.remove('active');
                });
            }
            
            // File upload handling (no analysis display)
            const fileInput = document.getElementById('resume');
            const fileUploadLabel = document.querySelector('.file-upload-label');
            const fileUploadText = document.getElementById('fileUploadText');
            
            if (fileInput && fileUploadLabel && fileUploadText) {
                // Handle file selection
                fileInput.addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        fileUploadText.textContent = file.name;
                        fileUploadLabel.classList.add('has-file');
                    } else {
                        fileUploadText.textContent = 'Choose file or drag it here';
                        fileUploadLabel.classList.remove('has-file');
                    }
                });
                
                // Handle drag and drop
                fileUploadLabel.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    fileUploadLabel.classList.add('dragover');
                });
                
                fileUploadLabel.addEventListener('dragleave', function(e) {
                    e.preventDefault();
                    fileUploadLabel.classList.remove('dragover');
                });
                
                fileUploadLabel.addEventListener('drop', function(e) {
                    e.preventDefault();
                    fileUploadLabel.classList.remove('dragover');
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        const file = files[0];
                        fileInput.files = files;
                        fileUploadText.textContent = file.name;
                        fileUploadLabel.classList.add('has-file');
                    }
                });
            }
            
            // Show loading when form is submitted
            if (form) {
                form.addEventListener('submit', function(e) {
                    // Validate form first
                    if (form.checkValidity()) {
                        loadingOverlay.classList.add('active');
                        startLoadingAnimation();
                        // Disable submit button to prevent double submission
                        const submitBtn = form.querySelector('button[type="submit"]');
                        if (submitBtn) {
                            submitBtn.disabled = true;
                            submitBtn.style.opacity = '0.6';
                            submitBtn.style.cursor = 'not-allowed';
                        }
                    }
                });
            }
            
            // Hide loading when page loads (if results are ready)
            window.addEventListener('load', function() {
                // Check if we have results or an error message
                const hasResults = document.querySelector('.success');
                const hasMessage = document.querySelector('.alert');
                
                if (hasResults || hasMessage) {
                    stopLoadingAnimation();
                    // Small delay for smooth transition
                    setTimeout(function() {
                        loadingOverlay.classList.remove('active');
                    }, 300);
                }
            });
            
            // Also hide loading if it's still visible after a timeout (safety measure)
            setTimeout(function() {
                stopLoadingAnimation();
                loadingOverlay.classList.remove('active');
            }, 120000); // 2 minutes max
        })();
    </script>
</body>
</html>
"""

# Store latest CSV in memory for download
_latest_csv_content = None
_latest_csv_filename = None


def require_auth(f):
    """Decorator to require authentication."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('landing'))
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/')
def landing():
    """Landing page with product information."""
    # If already logged in, redirect based on admin status
    if 'user_id' in session:
        if session.get('is_admin', False):
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('search_page'))
    
    # Get user count for display
    user_count = get_user_count(USER_DB_PATH)
    
    return render_template_string(LANDING_PAGE_TEMPLATE, user_count=user_count)


@app.route('/auth')
def auth_page():
    """Sign in/Sign up page."""
    # If already logged in, redirect based on admin status
    if 'user_id' in session:
        if session.get('is_admin', False):
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('search_page'))
    
    message = request.args.get('message', '')
    message_type = request.args.get('message_type', 'success')
    
    return render_template_string(
        AUTH_PAGE_TEMPLATE,
        message=message,
        message_type=message_type,
    )


@app.route('/signup', methods=['POST'])
def signup():
    """Handle user signup."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    success, message = create_user(USER_DB_PATH, email, password, name)
    
    if success:
        # Log the user in automatically
        verified, user_data = verify_user(USER_DB_PATH, email, password)
        if verified and user_data:
            session['user_id'] = user_data['id']
            session['user_email'] = user_data['email']
            session['user_name'] = user_data['name']
            session['is_admin'] = user_data.get('is_admin', False)
            
            # Redirect admin users to admin page, regular users to search page
            if user_data.get('is_admin', False):
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('search_page'))
    
    return redirect(url_for('auth_page', message=message, message_type='error'))


@app.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    verified, user_data = verify_user(USER_DB_PATH, email, password)
    
    if verified and user_data:
        session['user_id'] = user_data['id']
        session['user_email'] = user_data['email']
        session['user_name'] = user_data['name']
        session['is_admin'] = user_data.get('is_admin', False)
        
        # Redirect admin users to admin page, regular users to search page
        if user_data.get('is_admin', False):
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('search_page'))
    else:
        return redirect(url_for('auth_page', message='Invalid email or password', message_type='error'))


@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for('landing'))


# Admin page template
ADMIN_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - un!mployed</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
        }
        .header {
            background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            margin: 0;
            font-size: 1.8rem;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .logout-btn, .back-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 5px;
            text-decoration: none;
            transition: background 0.3s;
            font-size: 0.9rem;
        }
        .logout-btn:hover, .back-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: #f9f9f9;
            padding: 24px;
            border-radius: 8px;
            border: 1px solid #e5e5e5;
        }
        .stat-card h3 {
            margin: 0 0 8px 0;
            font-size: 0.9rem;
            color: #666;
            font-weight: 500;
        }
        .stat-card p {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
            color: #1a1a1a;
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        thead {
            background: #f9f9f9;
            border-bottom: 2px solid #e5e5e5;
        }
        th {
            padding: 16px;
            text-align: left;
            font-weight: 600;
            color: #1a1a1a;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        td {
            padding: 16px;
            border-bottom: 1px solid #e5e5e5;
            color: #333;
        }
        tbody tr:hover {
            background: #f9f9f9;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .badge-active {
            background: #e8f5e9;
            color: #2e7d32;
        }
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            table {
                font-size: 0.85rem;
            }
            th, td {
                padding: 12px 8px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Admin Panel</h1>
        <div class="user-info">
            <span>Welcome, {{ user_name }}!</span>
            <a href="/search" class="back-btn">Back to Search</a>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>Total Users</h3>
                <p>{{ total_users }}</p>
            </div>
        </div>
        
        <h2 style="margin-bottom: 20px; color: #1a1a1a;">All Users</h2>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Created At</th>
                        <th>Last Login</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.id }}</td>
                        <td><strong>{{ user.name }}</strong></td>
                        <td>{{ user.email }}</td>
                        <td>{{ user.created_at_formatted }}</td>
                        <td>{{ user.last_login_formatted }}</td>
                        <td>
                            <span class="badge badge-active">Active</span>
                        </td>
                    </tr>
                    <tr class="user-details-row">
                        <td colspan="6" style="padding: 0; border: none;">
                            <div class="user-details" style="background: #f9f9f9; padding: 20px; border-top: 2px solid #e5e5e5;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                                    <div>
                                        <h3 style="margin: 0 0 15px 0; font-size: 1rem; color: #1a1a1a;">Search History ({{ user.searches|length }})</h3>
                                        {% if user.searches %}
                                        <div style="max-height: 300px; overflow-y: auto;">
                                            {% for search in user.searches %}
                                            <div style="background: white; padding: 12px; margin-bottom: 10px; border-radius: 6px; border: 1px solid #e5e5e5;">
                                                <div style="font-weight: 600; margin-bottom: 6px; color: #1a1a1a;">{{ search.role or 'N/A' }}</div>
                                                <div style="font-size: 0.85rem; color: #666;">
                                                    Time: {{ search.time_window }}h | 
                                                    Location: {{ search.location or 'Any' }} | 
                                                    Remote: {{ 'Yes' if search.remote_only else 'No' }}
                                                </div>
                                                <div style="font-size: 0.8rem; color: #999; margin-top: 4px;">{{ search.searched_at_formatted }}</div>
                                            </div>
                                            {% endfor %}
                                        </div>
                                        {% else %}
                                        <div style="color: #999; font-style: italic;">No searches yet</div>
                                        {% endif %}
                                    </div>
                                    <div>
                                        <h3 style="margin: 0 0 15px 0; font-size: 1rem; color: #1a1a1a;">Resume Uploads ({{ user.resumes|length }})</h3>
                                        {% if user.resumes %}
                                        <div style="max-height: 300px; overflow-y: auto;">
                                            {% for resume in user.resumes %}
                                            <div style="background: white; padding: 12px; margin-bottom: 10px; border-radius: 6px; border: 1px solid #e5e5e5;">
                                                <div style="font-weight: 600; margin-bottom: 6px; color: #1a1a1a;">{{ resume.filename }}</div>
                                                <div style="font-size: 0.8rem; color: #999; margin-bottom: 8px;">{{ resume.uploaded_at_formatted }}</div>
                                                <a href="/admin/download-resume/{{ resume.id }}" style="display: inline-block; padding: 6px 12px; background: #1a1a1a; color: white; text-decoration: none; border-radius: 4px; font-size: 0.85rem;">Download</a>
                                            </div>
                                            {% endfor %}
                                        </div>
                                        {% else %}
                                        <div style="color: #999; font-style: italic;">No resumes uploaded</div>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""


@app.route('/admin')
@require_auth
def admin_page():
    """Admin page to view all users."""
    from datetime import datetime
    
    # Optional: Only allow admins to access this page
    # Uncomment the following lines if you want to restrict access to admins only
    # if not session.get('is_admin', False):
    #     return redirect(url_for('search_page'))
    
    user_name = session.get('user_name', 'User')
    users = get_all_users(USER_DB_PATH)
    
    # Get search history and resumes for all users
    all_searches = get_user_searches(ACTIVITY_DB_PATH)
    all_resumes = get_user_resumes(ACTIVITY_DB_PATH)
    
    # Format dates for display and add activity data
    for user in users:
        if user['created_at']:
            try:
                dt = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
                user['created_at_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                user['created_at_formatted'] = user['created_at']
        else:
            user['created_at_formatted'] = 'N/A'
        
        if user['last_login']:
            try:
                dt = datetime.fromisoformat(user['last_login'].replace('Z', '+00:00'))
                user['last_login_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                user['last_login_formatted'] = user['last_login']
        else:
            user['last_login_formatted'] = 'Never'
        
        # Get user's searches
        user['searches'] = [s for s in all_searches if s['user_id'] == user['id']]
        # Format search dates
        for search in user['searches']:
            if search['searched_at']:
                try:
                    dt = datetime.fromisoformat(search['searched_at'].replace('Z', '+00:00'))
                    search['searched_at_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    search['searched_at_formatted'] = search['searched_at']
            else:
                search['searched_at_formatted'] = 'N/A'
        
        # Get user's resumes
        user['resumes'] = [r for r in all_resumes if r['user_id'] == user['id']]
        # Format resume dates
        for resume in user['resumes']:
            if resume['uploaded_at']:
                try:
                    dt = datetime.fromisoformat(resume['uploaded_at'].replace('Z', '+00:00'))
                    resume['uploaded_at_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    resume['uploaded_at_formatted'] = resume['uploaded_at']
            else:
                resume['uploaded_at_formatted'] = 'N/A'
    
    return render_template_string(
        ADMIN_PAGE_TEMPLATE,
        user_name=user_name,
        users=users,
        total_users=len(users),
    )


@app.route('/search')
@require_auth
def search_page():
    """Render the search page."""
    user_name = session.get('user_name', 'User')
    
    # Get search params from query string (for "try again" feature)
    time_window = request.args.get('time_window', '48')
    location = request.args.get('location', '')
    role = request.args.get('role', '')
    remote_only = request.args.get('remote_only') == '1'
    
    return render_template_string(
        SEARCH_PAGE_TEMPLATE,
        user_name=user_name,
        time_window=time_window,
        location=location,
        role=role,
        remote_only=remote_only,
    )


@app.route('/search', methods=['POST'])
@require_auth
def search():
    """Search for jobs and prepare CSV export."""
    global _latest_csv_content, _latest_csv_filename
    
    role = request.form.get('role', '').strip()
    time_window_str = request.form.get('time_window', '48').strip()
    location_filter = request.form.get('location', '').strip()
    remote_only = request.form.get('remote_only') == '1'
    user_name = session.get('user_name', 'User')
    
    # Handle resume upload if present (process in background, don't block search)
    resume_file = request.files.get('resume')
    resume_processed = False
    user_id = session.get('user_id')
    user_email = session.get('user_email', '')
    
    if resume_file and resume_file.filename and user_id:
        try:
            file_content = resume_file.read()
            filename = resume_file.filename
            
            # Save resume file
            save_resume(ACTIVITY_DB_PATH, user_id, user_email, filename, file_content)
            
            # Parse resume
            resume_data = parse_resume(file_content, filename)
            
            # Store in session for display
            session['resume_data'] = resume_data
            session['resume_filename'] = filename
            resume_processed = True
            logger.info(f"Resume processed successfully: {filename}")
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            # Continue with search even if resume parsing fails
    
    # Convert time window to hours
    try:
        max_age_hours = int(time_window_str)
    except (ValueError, TypeError):
        max_age_hours = 48
    
    if max_age_hours <= 0 or max_age_hours > 720:
        max_age_hours = 48
    
    if not role:
        return render_template_string(
            SEARCH_PAGE_TEMPLATE,
            user_name=user_name,
            message="Please enter a job role/keywords",
            message_type="error",
            time_window=time_window_str,
            location=location_filter,
            remote_only=remote_only,
        )
    
    try:
        logger.info(f"Search requested for role: {role} by user {session.get('user_email')}")
        
        # Load settings
        settings = get_settings()
        
        # Override keywords with search query
        keywords = [kw.strip() for kw in role.split(',') if kw.strip()]
        original_keywords = settings.KEYWORDS
        settings.KEYWORDS = keywords
        
        # Collect jobs from all sources
        all_raw_items = []
        
        # LinkedIn RSS
        if settings.LINKEDIN_RSS_URLS:
            logger.info(f"Fetching LinkedIn RSS: {len(settings.LINKEDIN_RSS_URLS)} feeds")
            raw_items = fetch_linkedin(settings)
            all_raw_items.extend(raw_items)
        
        # Indeed RSS - intelligently match relevant feeds
        if settings.INDEED_RSS_URLS:
            relevant_indeed_feeds = match_indeed_feeds(keywords, settings.INDEED_RSS_URLS)
            logger.info(f"Using {len(relevant_indeed_feeds)} relevant Indeed RSS feeds (from {len(settings.INDEED_RSS_URLS)} total) for keywords: {keywords}")
            
            original_indeed_urls = settings.INDEED_RSS_URLS
            settings.INDEED_RSS_URLS = relevant_indeed_feeds
            
            raw_items = fetch_indeed(settings)
            all_raw_items.extend(raw_items)
            
            settings.INDEED_RSS_URLS = original_indeed_urls
        
        # Greenhouse
        if settings.GREENHOUSE_BOARDS:
            logger.info(f"Fetching Greenhouse: {len(settings.GREENHOUSE_BOARDS)} boards")
            raw_items = fetch_greenhouse(settings)
            all_raw_items.extend(raw_items)
        
        # Lever
        if settings.LEVER_COMPANIES:
            logger.info(f"Fetching Lever: {len(settings.LEVER_COMPANIES)} companies")
            raw_items = fetch_lever(settings)
            all_raw_items.extend(raw_items)
        
        # Glassdoor RSS
        if settings.GLASSDOOR_RSS_URLS:
            relevant_glassdoor_feeds = match_rss_feeds(keywords, settings.GLASSDOOR_RSS_URLS)
            logger.info(f"Using {len(relevant_glassdoor_feeds)} relevant Glassdoor RSS feeds")
            original_glassdoor_urls = settings.GLASSDOOR_RSS_URLS
            settings.GLASSDOOR_RSS_URLS = relevant_glassdoor_feeds
            raw_items = fetch_glassdoor(settings)
            all_raw_items.extend(raw_items)
            settings.GLASSDOOR_RSS_URLS = original_glassdoor_urls
        
        # Handshake RSS
        if settings.HANDSHAKE_RSS_URLS:
            relevant_handshake_feeds = match_rss_feeds(keywords, settings.HANDSHAKE_RSS_URLS)
            logger.info(f"Using {len(relevant_handshake_feeds)} relevant Handshake RSS feeds")
            original_handshake_urls = settings.HANDSHAKE_RSS_URLS
            settings.HANDSHAKE_RSS_URLS = relevant_handshake_feeds
            raw_items = fetch_handshake(settings)
            all_raw_items.extend(raw_items)
            settings.HANDSHAKE_RSS_URLS = original_handshake_urls
        
        if not all_raw_items:
            return render_template_string(
                SEARCH_PAGE_TEMPLATE,
                user_name=user_name,
                role=role,
                message="No jobs found from any source. Please check your configuration.",
                message_type="error",
                time_window=time_window_str,
                location=location_filter,
                remote_only=remote_only,
            )
        
        # Normalize jobs
        jobs = normalize_all(all_raw_items)
        
        if not jobs:
            return render_template_string(
                SEARCH_PAGE_TEMPLATE,
                user_name=user_name,
                role=role,
                message="No jobs could be normalized. Please check the source data.",
                message_type="error",
                time_window=time_window_str,
                location=location_filter,
                remote_only=remote_only,
            )
        
        # Tag jobs with search keywords
        jobs = [tag_job(job, keywords) for job in jobs]
        
        # Filter: Only keep jobs that match keywords
        if keywords:
            matching_jobs = [job for job in jobs if job.tags]
            logger.info(f"Filtered to {len(matching_jobs)} jobs matching keywords (from {len(jobs)} total)")
            
            if not matching_jobs:
                return render_template_string(
                    SEARCH_PAGE_TEMPLATE,
                    user_name=user_name,
                    role=role,
                    message=f"No jobs found matching '{role}' in the selected time window.",
                    message_type="info",
                    time_window=time_window_str,
                    location=location_filter,
                    remote_only=remote_only,
                )
        else:
            matching_jobs = jobs
        
        # Apply location filter
        if location_filter:
            location_lower = location_filter.lower()
            location_normalized = location_lower
            if location_normalized in ['usa', 'us', 'united states']:
                location_variants = ['usa', 'us', 'united states', 'united states of america']
            else:
                location_variants = [location_normalized]
            
            location_filtered = []
            for job in matching_jobs:
                if not job.location:
                    location_filtered.append(job)
                elif any(variant in job.location.lower() for variant in location_variants):
                    location_filtered.append(job)
            
            logger.info(f"Filtered to {len(location_filtered)} jobs matching location '{location_filter}'")
            matching_jobs = location_filtered
        
        # Apply remote-only filter
        if remote_only:
            matching_jobs = [job for job in matching_jobs if job.remote]
            logger.info(f"Filtered to {len(matching_jobs)} remote jobs")
        
        # Filter by freshness
        fresh_jobs = filter_fresh(matching_jobs, max_age_hours)
        
        if not fresh_jobs:
            if max_age_hours == 720:
                time_display = "1 month"
            elif max_age_hours >= 168:
                weeks = max_age_hours // 168
                time_display = f"{weeks} week(s)"
            else:
                time_display = f"{max_age_hours} hours"
            
            filter_msg = ""
            if location_filter:
                filter_msg += f" in '{location_filter}'"
            if remote_only:
                filter_msg += " (remote only)"
            
            return render_template_string(
                SEARCH_PAGE_TEMPLATE,
                user_name=user_name,
                role=role,
                message=f"No fresh jobs found{filter_msg} (posted within last {time_display}).",
                message_type="info",
                time_window=time_window_str,
                location=location_filter,
                remote_only=remote_only,
            )
        
        # Deduplicate
        unique_jobs = deduplicate_jobs(fresh_jobs)
        
        # Sort by score
        sorted_jobs = sort_jobs(unique_jobs)
        
        # Generate CSV
        csv_content = export_jobs_to_csv(sorted_jobs)
        _latest_csv_content = csv_content.encode('utf-8')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        _latest_csv_filename = f"jobs_{role.replace(' ', '_').replace(',', '_')}_{timestamp}.csv"
        
        # Store search params in session for "try again"
        session['last_search'] = {
            'role': role,
            'time_window': time_window_str,
            'location': location_filter,
            'remote_only': remote_only
        }
        
        # Save search history
        user_id = session.get('user_id')
        user_email = session.get('user_email', '')
        if user_id:
            try:
                save_search(ACTIVITY_DB_PATH, user_id, user_email, role, 
                           time_window_str, location_filter, remote_only)
            except Exception as e:
                logger.error(f"Error saving search history: {e}")
        
        # Redirect to results page
        return redirect(url_for('results_page', job_count=len(sorted_jobs)))
    
    except Exception as e:
        logger.error(f"Error during job search: {e}", exc_info=True)
        return render_template_string(
            SEARCH_PAGE_TEMPLATE,
            user_name=user_name,
            role=role,
            message=f"An error occurred: {str(e)}",
            message_type="error",
            time_window=time_window_str,
            location=location_filter,
            remote_only=remote_only,
        )
    finally:
        settings.KEYWORDS = original_keywords


# Results page template
RESULTS_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Results - un!mployed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
            min-height: 100vh;
            color: #1a1a1a;
            overflow-x: hidden;
            position: relative;
        }
        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(26, 26, 26, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: drift 20s linear infinite;
            pointer-events: none;
            z-index: 0;
        }
        @keyframes drift {
            0% {
                transform: translate(0, 0);
            }
            100% {
                transform: translate(50px, 50px);
            }
        }
        .navbar {
            background: white;
            padding: 20px 40px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 800;
            color: #1a1a1a;
            letter-spacing: -1px;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .user-info span {
            color: #666;
            font-weight: 500;
        }
        .logout-btn {
            background: #1a1a1a;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 0;
            font-size: 0.875rem;
            font-weight: 700;
            cursor: pointer;
            text-decoration: none;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
        }
        .logout-btn:hover {
            background: #2a2a2a;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .main-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 80px 40px;
            animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            z-index: 1;
        }
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(50px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        .results-card {
            background: white;
            padding: 60px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(0, 0, 0, 0.05);
            text-align: center;
            position: relative;
            overflow: hidden;
            animation: cardSlideIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.2s backwards;
        }
        @keyframes cardSlideIn {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        .results-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(26, 26, 26, 0.03), transparent);
            animation: shine 3s infinite;
        }
        @keyframes shine {
            0% {
                left: -100%;
            }
            50%, 100% {
                left: 100%;
            }
        }
        .success-icon {
            width: 120px;
            height: 120px;
            margin: 0 auto 40px;
            background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            animation: scaleInBounce 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55), pulse 2s ease-in-out infinite 1s;
            box-shadow: 0 8px 32px rgba(26, 26, 26, 0.2);
        }
        @keyframes scaleInBounce {
            0% {
                transform: scale(0);
                opacity: 0;
            }
            50% {
                transform: scale(1.15);
            }
            100% {
                transform: scale(1);
                opacity: 1;
            }
        }
        @keyframes pulse {
            0%, 100% {
                box-shadow: 0 8px 32px rgba(26, 26, 26, 0.2);
            }
            50% {
                box-shadow: 0 8px 48px rgba(26, 26, 26, 0.3), 0 0 0 20px rgba(26, 26, 26, 0.05);
            }
        }
        .success-icon::before {
            content: '✓';
            font-size: 3.5rem;
            color: white;
            font-weight: 800;
            animation: checkmarkDraw 0.6s ease-out 0.3s backwards;
            position: relative;
            z-index: 1;
        }
        @keyframes checkmarkDraw {
            from {
                opacity: 0;
                transform: scale(0) rotate(-45deg);
            }
            to {
                opacity: 1;
                transform: scale(1) rotate(0deg);
            }
        }
        .success-icon::after {
            content: '';
            position: absolute;
            top: -4px;
            left: -4px;
            right: -4px;
            bottom: -4px;
            border: 3px solid #1a1a1a;
            border-radius: 50%;
            opacity: 0.2;
            animation: ripple 2s ease-out infinite;
        }
        @keyframes ripple {
            0% {
                transform: scale(0.8);
                opacity: 0.6;
            }
            100% {
                transform: scale(1.3);
                opacity: 0;
            }
        }
        .results-header {
            margin-bottom: 32px;
            animation: fadeInUp 0.6s ease-out 0.4s backwards;
        }
        .results-header h1 {
            font-size: 3rem;
            font-weight: 900;
            margin-bottom: 16px;
            letter-spacing: -2px;
            background: linear-gradient(135deg, #1a1a1a 0%, #3a3a3a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            display: inline-block;
            animation: textSlideIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.5s backwards;
        }
        @keyframes textSlideIn {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        .results-header p {
            font-size: 1.25rem;
            color: #666;
            font-weight: 400;
            animation: fadeIn 0.6s ease-out 0.7s backwards;
        }
        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        .job-count {
            font-size: 5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #1a1a1a 0%, #3a3a3a 50%, #1a1a1a 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 40px 0;
            letter-spacing: -4px;
            animation: countUp 1s cubic-bezier(0.4, 0, 0.2, 1) 0.9s backwards, gradientShift 3s ease infinite 2s;
            position: relative;
            display: inline-block;
        }
        @keyframes countUp {
            0% {
                opacity: 0;
                transform: translateY(30px) scale(0.5) rotate(-5deg);
            }
            60% {
                transform: translateY(-10px) scale(1.1) rotate(2deg);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1) rotate(0deg);
            }
        }
        @keyframes gradientShift {
            0%, 100% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
        }
        .job-count::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 4px;
            background: linear-gradient(90deg, transparent, #1a1a1a, transparent);
            animation: lineExpand 0.8s ease-out 1.5s forwards;
        }
        @keyframes lineExpand {
            to {
                width: 80%;
            }
        }
        .job-count-label {
            font-size: 1.125rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            margin-bottom: 48px;
            animation: fadeInUp 0.6s ease-out 1.2s backwards;
        }
        .actions {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 48px;
            animation: fadeInUp 0.6s ease-out 1.4s backwards;
        }
        .btn {
            padding: 18px 40px;
            border: none;
            border-radius: 0;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: relative;
            overflow: hidden;
        }
        .btn-primary {
            background: #1a1a1a;
            color: white;
            box-shadow: 0 4px 16px rgba(26, 26, 26, 0.2);
            animation: buttonBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) 1.6s backwards;
        }
        @keyframes buttonBounce {
            from {
                opacity: 0;
                transform: scale(0.5) translateY(20px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }
        .btn-primary::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
            transition: left 0.6s;
        }
        .btn-primary:hover::before {
            left: 100%;
        }
        .btn-primary:hover {
            background: #2a2a2a;
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 12px 32px rgba(26, 26, 26, 0.35);
        }
        .btn-primary:active {
            transform: translateY(-2px) scale(0.98);
        }
        .btn-secondary {
            background: transparent;
            color: #1a1a1a;
            border: 2px solid #1a1a1a;
            animation: buttonBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) 1.7s backwards;
        }
        .btn-secondary::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 0;
            height: 100%;
            background: #1a1a1a;
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: -1;
        }
        .btn-secondary:hover::before {
            width: 100%;
        }
        .btn-secondary:hover {
            color: white;
            border-color: #1a1a1a;
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 12px 32px rgba(26, 26, 26, 0.2);
        }
        .btn-secondary:active {
            transform: translateY(-2px) scale(0.98);
        }
        @media (max-width: 768px) {
            .main-container {
                padding: 40px 20px;
            }
            .navbar {
                padding: 15px 20px;
            }
            .results-card {
                padding: 40px 24px;
            }
            .results-header h1 {
                font-size: 2rem;
            }
            .job-count {
                font-size: 3rem;
            }
            .actions {
                flex-direction: column;
            }
            .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">un!mployed</div>
        <div class="user-info">
            <span>Welcome, {{ user_name }}!</span>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </nav>
    
    <div class="main-container">
        <div class="results-card">
            <div class="success-icon"></div>
            <div class="results-header">
                <h1>Search Complete!</h1>
                <p>Your job search results are ready</p>
            </div>
            <div class="job-count">{{ job_count }}</div>
            <div class="job-count-label">Jobs Found</div>
            <div class="actions">
                <a href="/download" class="btn btn-primary">Download CSV File</a>
                {% if has_resume %}
                <a href="/resume-analysis" class="btn btn-secondary" style="background: #4a5568; color: white; border: none;">View Resume Analysis</a>
                {% endif %}
                <a href="/search{{ try_again_params }}" class="btn btn-secondary">Try Different Timeline</a>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route('/results')
@require_auth
def results_page():
    """Display the results page with download link."""
    global _latest_csv_content
    
    if _latest_csv_content is None:
        return redirect(url_for('search_page'))
    
    job_count = request.args.get('job_count', '0')
    user_name = session.get('user_name', 'User')
    
    # Check if resume was processed
    has_resume = 'resume_data' in session
    
    # Get last search params for "try again" button
    from urllib.parse import urlencode
    last_search = session.get('last_search', {})
    try_again_params = ''
    if last_search:
        params = {}
        if last_search.get('role'):
            params['role'] = last_search['role']
        if last_search.get('time_window'):
            params['time_window'] = last_search['time_window']
        if last_search.get('location'):
            params['location'] = last_search['location']
        if last_search.get('remote_only'):
            params['remote_only'] = '1'
        if params:
            try_again_params = '?' + urlencode(params)
    
    return render_template_string(
        RESULTS_PAGE_TEMPLATE,
        user_name=user_name,
        job_count=job_count,
        try_again_params=try_again_params,
        has_resume=has_resume
    )


@app.route('/api/parse-resume', methods=['POST'])
@require_auth
def api_parse_resume():
    """API endpoint to parse resume and return JSON."""
    
    resume_file = request.files.get('resume')
    
    if not resume_file or not resume_file.filename:
        return jsonify({'error': 'No file provided'}), 400
    
    try:
        file_content = resume_file.read()
        filename = resume_file.filename
        
        # Save resume file
        user_id = session.get('user_id')
        user_email = session.get('user_email', '')
        if user_id:
            save_resume(ACTIVITY_DB_PATH, user_id, user_email, filename, file_content)
        
        # Parse resume
        resume_data = parse_resume(file_content, filename)
        
        # Store in session for later use
        session['resume_data'] = resume_data
        session['resume_filename'] = filename
        
        logger.info(f"Resume processed successfully via API: {filename}")
        
        # Return JSON response
        return jsonify({
            'success': True,
            'filename': filename,
            'data': resume_data
        })
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/upload-resume', methods=['POST'])
@require_auth
def upload_resume():
    """Handle standalone resume upload and analysis."""
    resume_file = request.files.get('resume')
    
    if not resume_file or not resume_file.filename:
        return redirect(url_for('search_page'))
    
    try:
        file_content = resume_file.read()
        filename = resume_file.filename
        
        # Save resume file
        user_id = session.get('user_id')
        user_email = session.get('user_email', '')
        if user_id:
            save_resume(ACTIVITY_DB_PATH, user_id, user_email, filename, file_content)
        
        # Parse resume
        resume_data = parse_resume(file_content, filename)
        
        # Store in session for display
        session['resume_data'] = resume_data
        session['resume_filename'] = filename
        
        logger.info(f"Resume processed successfully: {filename}")
        
        # Redirect to resume analysis page
        return redirect(url_for('resume_analysis'))
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        user_name = session.get('user_name', 'User')
        return render_template_string(
            SEARCH_PAGE_TEMPLATE,
            user_name=user_name,
            message=f"Error processing resume: {str(e)}",
            message_type="error",
        )


@app.route('/resume-analysis')
@require_auth
def resume_analysis():
    """Display resume analysis results."""
    user_name = session.get('user_name', 'User')
    resume_data = session.get('resume_data')
    resume_filename = session.get('resume_filename', 'resume')
    
    if not resume_data:
        return redirect(url_for('search_page'))
    
    # Create HTML template for resume analysis
    resume_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Analysis - un!mployed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #1a1a1a;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 2rem;
            margin-bottom: 10px;
            color: #1a1a1a;
        }
        .header p {
            color: #666;
            font-size: 1rem;
        }
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .analysis-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .analysis-card h2 {
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #1a1a1a;
            border-bottom: 2px solid #1a1a1a;
            padding-bottom: 10px;
        }
        .skill-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .skill-tag {
            background: #1a1a1a;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .skill-tag.soft-skill {
            background: #4a5568;
        }
        .info-item {
            padding: 10px 0;
            border-bottom: 1px solid #e5e5e5;
        }
        .info-item:last-child {
            border-bottom: none;
        }
        .info-label {
            font-weight: 600;
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        .info-value {
            color: #1a1a1a;
            font-size: 1rem;
        }
        .keywords-section {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .keywords-section h2 {
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #1a1a1a;
            border-bottom: 2px solid #1a1a1a;
            padding-bottom: 10px;
        }
        .keyword-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .keyword-tag {
            background: #f0f0f0;
            color: #1a1a1a;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            border: 1px solid #e5e5e5;
        }
        .actions {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: #1a1a1a;
            color: white;
        }
        .btn-primary:hover {
            background: #333;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .btn-secondary {
            background: white;
            color: #1a1a1a;
            border: 2px solid #1a1a1a;
        }
        .btn-secondary:hover {
            background: #f5f5f5;
        }
        .empty-state {
            color: #999;
            font-style: italic;
            padding: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Resume Analysis</h1>
            <p>Analyzed resume: <strong>{{ resume_filename }}</strong></p>
        </div>
        
        <div class="analysis-grid">
            <div class="analysis-card">
                <h2>Technical Skills</h2>
                {% if resume_data.technical_skills %}
                <div class="skill-list">
                    {% for skill in resume_data.technical_skills %}
                    <span class="skill-tag">{{ skill }}</span>
                    {% endfor %}
                </div>
                {% else %}
                <div class="empty-state">No technical skills detected</div>
                {% endif %}
            </div>
            
            <div class="analysis-card">
                <h2>Soft Skills</h2>
                {% if resume_data.soft_skills %}
                <div class="skill-list">
                    {% for skill in resume_data.soft_skills %}
                    <span class="skill-tag soft-skill">{{ skill }}</span>
                    {% endfor %}
                </div>
                {% else %}
                <div class="empty-state">No soft skills detected</div>
                {% endif %}
            </div>
        </div>
        
        <div class="actions">
            <a href="/search" class="btn btn-primary">Back to Search</a>
            <a href="/" class="btn btn-secondary">Home</a>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(
        resume_template,
        user_name=user_name,
        resume_data=resume_data,
        resume_filename=resume_filename
    )


@app.route('/download')
@require_auth
def download():
    """Download the latest CSV file."""
    global _latest_csv_content, _latest_csv_filename
    
    if _latest_csv_content is None:
        return redirect(url_for('search_page'))
    
    return send_file(
        io.BytesIO(_latest_csv_content),
        mimetype='text/csv',
        as_attachment=True,
        download_name=_latest_csv_filename,
    )


@app.route('/admin/download-resume/<int:resume_id>')
@require_auth
def download_resume(resume_id):
    """Download a user's uploaded resume (admin only)."""
    # Check if user is admin
    if not session.get('is_admin', False):
        return redirect(url_for('search_page'))
    
    try:
        resumes = get_user_resumes(ACTIVITY_DB_PATH)
        resume = next((r for r in resumes if r['id'] == resume_id), None)
        
        if not resume:
            return "Resume not found", 404
        
        # Handle both absolute and relative paths
        file_path_str = resume['file_path']
        
        # Fix incorrect paths that include /app/resumes/ instead of /resumes/
        # This handles old paths that were saved incorrectly
        if '/app/resumes/' in file_path_str:
            file_path_str = file_path_str.replace('/app/resumes/', '/resumes/')
        
        file_path = Path(file_path_str)
        
        # If it's a relative path, try to resolve it relative to project root
        if not file_path.is_absolute():
            project_root = Path(__file__).parent.parent
            file_path = project_root / file_path
        
        # Resolve to absolute path
        file_path = file_path.resolve()
        
        if not file_path.exists():
            logger.error(f"Resume file not found at: {file_path}")
            return f"Resume file not found", 404
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=resume['filename'],
        )
    except Exception as e:
        logger.error(f"Error downloading resume: {e}")
        return f"Error downloading resume: {str(e)}", 500


def run_ui(host=None, port=None, debug=None):
    """Run the Flask UI server."""
    # Use environment variables for production deployment
    host = host or os.environ.get('HOST', '0.0.0.0')
    port = port or int(os.environ.get('PORT', 5001))
    
    # Only enable debug mode if explicitly set or in development
    if debug is None:
        debug = os.environ.get('FLASK_ENV') != 'production' and os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Starting un!mployed UI at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_ui()
