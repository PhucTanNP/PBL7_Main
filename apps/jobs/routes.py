from flask import Blueprint, request, redirect, url_for, flash, render_template, session
from flask_login import login_required, current_user
from datetime import datetime, date
from apps import db
from apps.jobs.models import Job
from apps.list_seeker.models import ListSeeker
from apps.notifications.models import Notification
from apps.authentication.models import User

jobs_blueprint = Blueprint('jobs_blueprint', __name__)

# -------------------------------
# HR đăng bài mới
# -------------------------------
@jobs_blueprint.route('/post_job', methods=['POST'])
@login_required
def post_job():
    try:
        job = Job(
            job_title=request.form['job_title'],
            company_name=request.form['company_name'],
            job_type='online',
            location=request.form['location'],
            salary=request.form.get('salary'),
            experience=request.form.get('experience'),
            deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d'),
            id_hr=current_user.id_user,
            industry=request.form.get('industry')  # ✅ Thêm ngành nghề
        )
        db.session.add(job)
        db.session.commit()
        flash("Đăng bài thành công", "success")
    except Exception as e:
        print(">>> Exception:", e)
        db.session.rollback()
        flash("Lỗi đăng bài: " + str(e), "danger")

    return redirect(url_for('home_blueprint.index'))

# -------------------------------
# Ứng viên apply job
# -------------------------------
@jobs_blueprint.route('/apply_job/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    print(">>> Apply Job ID:", job_id)

    try:
        new_apply = ListSeeker(
            id_job=job_id,
            id_seeker=current_user.id_user,
            status='applied',
            apply_date=date.today()
        )
        db.session.add(new_apply)

        job = Job.query.filter_by(id_job=job_id).first()
        if job:
            notification = Notification(
                user_id=job.id_hr,
                job_id=job_id,
                applicant_id=current_user.id_user,
                type='new_application',
                status='unread'
            )
            db.session.add(notification)

        db.session.commit()
        flash("Ứng tuyển thành công!", "success")

    except Exception as e:
        db.session.rollback()
        print(">>> Apply Error:", e)
        flash("Có lỗi khi ứng tuyển: " + str(e), "danger")

    return redirect(url_for('home_blueprint.index'))

# -------------------------------
# HÀM TIỆN ÍCH DÙNG CHO ADMIN
# -------------------------------

def get_all_jobs_with_applicants():
    jobs = Job.query.all()
    job_applicants = {}
    print("🧪 JOB DEBUG:", jobs)

    for job in jobs:
        applications = ListSeeker.query.filter_by(id_job=job.id_job).all()
        applicants = []
        for app in applications:
            user = User.query.filter_by(id_user=app.id_seeker).first()
            if user:
                applicants.append({
                    'id_user': user.id_user,
                    'full_name': user.full_name,
                    'email': user.email,
                    'phone': user.phone,
                    'avatar_file': user.avatar_file,
                    'cv_file': user.cv_file,
                    'apply_time': app.apply_date.strftime('%d %b %H:%M'),
                    'status': app.status
                })
        job_applicants[job.id_job] = {
            'industry': job.industry,  # ✅ Thêm industry
            'applicants': applicants
        }

    return jobs, job_applicants

def create_job_from_form(form_data):
    deadline = datetime.strptime(form_data['deadline'], '%Y-%m-%d')
    job = Job(
        job_title=form_data['job_title'],
        company_name=form_data['company_name'],
        job_type=form_data.get('job_type', 'online'),
        location=form_data['location'],
        salary=form_data.get('salary'),
        experience=form_data.get('experience'),
        deadline=deadline,
        id_hr=None,
        industry=form_data.get('industry')  # ✅ Thêm industry
    )
    db.session.add(job)
    db.session.commit()
    return job

def update_job_from_form(job_id, form_data):
    job = Job.query.get_or_404(job_id)
    job.job_title = form_data['job_title']
    job.company_name = form_data['company_name']
    job.job_type = form_data.get('job_type', 'online')
    job.location = form_data['location']
    job.salary = form_data.get('salary')
    job.experience = form_data.get('experience')
    job.deadline = datetime.strptime(form_data['deadline'], '%Y-%m-%d')
    job.industry = form_data.get('industry')  # ✅ Thêm industry
    db.session.commit()
    return job

def delete_job_with_applicants(job_id):
    Notification.query.filter_by(job_id=job_id).delete()
    ListSeeker.query.filter_by(id_job=job_id).delete()
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()

# -------------------------------
# HR xem các job đã đăng
# -------------------------------
@jobs_blueprint.route("/my-jobs")
@login_required
def my_jobs():
    if session.get('role') != 'HR':
        return "Unauthorized", 403

    job_list = Job.query.filter_by(id_hr=current_user.id_user).all()
    job_applicants = {}

    for job in job_list:
        applications = ListSeeker.query.filter_by(id_job=job.id_job).all()
        applicants = []

        for app in applications:
            user = User.query.filter_by(id_user=app.id_seeker).first()
            if user:
                applicants.append({
                    'id_user': user.id_user,
                    'full_name': user.full_name,
                    'email': user.email,
                    'phone': user.phone,
                    'avatar_file': user.avatar_file,
                    'cv_file': user.cv_file,
                    'note': 'Ứng tuyển vị trí này',
                    'apply_time': app.apply_date.strftime('%d %b %H:%M'),
                    'status': app.status,
                    'status_color': 'text-success' if app.status == 'applied' else 'text-danger'
                })

        job_applicants[job.id_job] = {
            'industry': job.industry,  # ✅ Thêm industry
            'applicants': applicants
        }

    return render_template(
        "hr_role/your_posts.html",
        jobs=job_list,
        job_applicants=job_applicants
    )
@jobs_blueprint.route("/crawler")
@login_required
def crawler():
    
    return render_template("admin/crawler.html")