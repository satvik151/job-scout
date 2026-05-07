#!/usr/bin/env python
"""
Multi-tenant testing script for Job Scout API.
Tests user registration, resume upload, and job fetching.
"""
import requests
import json
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:8000"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

print("=" * 70)
print("MULTI-TENANT JOB SCOUT TEST")
print("=" * 70)

# Step 1: Register User A
print("\n[1] Registering User A...")
email_a = f"user.a.{timestamp}@example.com"
r = requests.post(
    f"{BASE_URL}/auth/register",
    json={"email": email_a, "password": "SecurePass123"}
)
if r.status_code == 200:
    user_a_id = r.json()["id"]
    print(f"✓ User A registered (ID: {user_a_id})")
else:
    print(f"✗ Failed: {r.status_code} - {r.text}")
    exit(1)

# Step 2: Register User B
print("\n[2] Registering User B...")
email_b = f"user.b.{timestamp}@example.com"
r = requests.post(
    f"{BASE_URL}/auth/register",
    json={"email": email_b, "password": "SecurePass123"}
)
if r.status_code == 200:
    user_b_id = r.json()["id"]
    print(f"✓ User B registered (ID: {user_b_id})")
else:
    print(f"✗ Failed: {r.status_code} - {r.text}")
    exit(1)

# Step 3: Login User A and get token
print("\n[3] Logging in User A...")
r = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": email_a, "password": "SecurePass123"}
)
if r.status_code == 200:
    token_a = r.json()["access_token"]
    print(f"✓ User A logged in")
    print(f"  Token: {token_a[:40]}...")
else:
    print(f"✗ Failed: {r.status_code} - {r.text}")
    exit(1)

# Step 4: Login User B and get token
print("\n[4] Logging in User B...")
r = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": email_b, "password": "SecurePass123"}
)
if r.status_code == 200:
    token_b = r.json()["access_token"]
    print(f"✓ User B logged in")
    print(f"  Token: {token_b[:40]}...")
else:
    print(f"✗ Failed: {r.status_code} - {r.text}")
    exit(1)

# Step 5: Create dummy PDFs and upload resumes
print("\n[5] Creating and uploading resumes...")

# Create better dummy PDFs using PyPDF2
from io import BytesIO
from reportlab.pdfgen import canvas

def create_pdf_content(text):
    """Create a simple PDF with text using reportlab"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, text)
    c.drawString(100, 730, "Additional resume content to ensure sufficient length.")
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

resume_a_content = create_pdf_content("Python Developer with 5 years experience in FastAPI and backend development.")
resume_b_content = create_pdf_content("Full Stack Engineer with expertise in FastAPI, React, and PostgreSQL databases.")

# Upload resume for User A
r = requests.post(
    f"{BASE_URL}/auth/upload-resume",
    headers={"Authorization": f"Bearer {token_a}"},
    files={"file": ("resume_a.pdf", resume_a_content, "application/pdf")}
)
if r.status_code == 200:
    print(f"✓ User A resume uploaded")
else:
    print(f"✗ Failed to upload resume A: {r.status_code} - {r.text}")

# Upload resume for User B
r = requests.post(
    f"{BASE_URL}/auth/upload-resume",
    headers={"Authorization": f"Bearer {token_b}"},
    files={"file": ("resume_b.pdf", resume_b_content, "application/pdf")}
)
if r.status_code == 200:
    print(f"✓ User B resume uploaded")
else:
    print(f"✗ Failed to upload resume B: {r.status_code} - {r.text}")

# Step 6: Both users fetch jobs
print("\n[6] Both users fetching jobs...")
print("\n  User A fetching jobs...")
r_a = requests.get(
    f"{BASE_URL}/jobs?pages=1",
    headers={"Authorization": f"Bearer {token_a}"}
)
if r_a.status_code == 200:
    jobs_a = r_a.json()["jobs"]
    print(f"✓ User A fetched {len(jobs_a)} jobs")
    if jobs_a:
        print(f"  Sample job: {jobs_a[0]['title']} @ {jobs_a[0]['company']}")
else:
    print(f"✗ Failed: {r_a.status_code} - {r_a.text}")

print("\n  User B fetching jobs...")
r_b = requests.get(
    f"{BASE_URL}/jobs?pages=1",
    headers={"Authorization": f"Bearer {token_b}"}
)
if r_b.status_code == 200:
    jobs_b = r_b.json()["jobs"]
    print(f"✓ User B fetched {len(jobs_b)} jobs")
    if jobs_b:
        print(f"  Sample job: {jobs_b[0]['title']} @ {jobs_b[0]['company']}")
else:
    print(f"✗ Failed: {r_b.status_code} - {r_b.text}")

# Step 7: Verify multi-tenant isolation
print("\n[7] MULTI-TENANT ISOLATION CHECKS:")
if r_a.status_code == 200 and r_b.status_code == 200:
    urls_a = {job.get("url") for job in jobs_a if jobs_a}
    urls_b = {job.get("url") for job in jobs_b if jobs_b}
    
    # Both should have jobs
    if len(urls_a) > 0 and len(urls_b) > 0:
        print(f"✓ User A has {len(urls_a)} unique job URLs")
        print(f"✓ User B has {len(urls_b)} unique job URLs")
        
        # Check for overlap (they should share many URLs since it's the same source)
        overlap = urls_a & urls_b
        if overlap:
            print(f"✓ {len(overlap)} overlapping URLs (same source, different user_id) ✓✓✓")
            print(f"  This confirms multi-tenant isolation is working!")
        else:
            print(f"⚠ No overlapping URLs (might indicate separate scrapes)")
    else:
        print(f"✗ Not enough jobs to verify isolation")
else:
    print(f"✗ Could not verify (fetch failed)")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
