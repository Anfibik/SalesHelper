import itertools
import sqlite3
import os

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, g, abort, session, send_file, \
    make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

from Utils.Calculate_BVZ import calculate_BVZ
from Utils.UserLogin import UserLogin
from Utils.FDataBase import FDataBase
from Utils.NumConvert import number_to_words
from Utils.View_final_calculation import view_table_warehouse
from Utils.form import LoginForm, RegistrationForm
from datetime import datetime

# Конфигурация
DATABASE = '/tmp/SH_site.db'
DEBUG = True
SECRET_KEY = 'fdgfh78@#5?>gfhf89dx,v06k'
USERNAME = 'admin'
PASSWORD = '123'

# Инициализируем приложение
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'SH_site.db')))

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для работы в приложении"
login_manager.login_message_category = "success"


# ------------Создаем базу данных----------------------------
def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    """Вспомогательная функция для создания таблиц БД"""
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    """Соединение с БД, если оно еще не установлено"""
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


@app.teardown_appcontext
def close_db(error):
    """Закрываем соединение с БД, если оно было установлено"""
    if hasattr(g, 'link_db'):
        g.link_db.close()


@login_manager.user_loader
def load_user(user_id):
    dbase = FDataBase(get_db())
    return UserLogin().fromDB(user_id, dbase)


menu = [
    {"url": '/', "name": 'Главная'},
    {"url": '/leads', "name": 'Сделки'},
    {"url": '/pricing', "name": 'Расчет стоимостей'},
    {"url": '/morzh', "name": 'Личные финансы'},
    {"url": '/about', "name": 'О программе'}
]


# --------------------Login----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    dbase = FDataBase(get_db())

    if current_user.is_authenticated:
        return redirect(url_for('leads'))

    form = LoginForm()
    if form.validate_on_submit():
        # здесь можно добавить логику для проверки введенных данных
        user = dbase.get_user_by_email(form.email.data)
        if user and check_password_hash(user['psw'], form.password.data):
            user_login = UserLogin().create(user)
            rm = True if form.remember_user.data else False

            login_user(user_login, remember=rm)
            return redirect(url_for('leads'))
        flash("Неверная пара логин/пароль", "error")

    return render_template('login.html', title='Login', form=form, menu=menu)


# -----------------LOGOUT------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --------------------Registration----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    dbase = FDataBase(get_db())

    form = RegistrationForm()
    if form.validate_on_submit():
        session.pop('_flashes', None)
        # здесь можно добавить логику для создания нового пользователя
        hash = generate_password_hash(form.password.data)
        res = dbase.add_user(form.username.data, form.email.data, hash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", "error")
    else:
        flash("Неверно заполнены поля", "error")

    return render_template('register.html', title='Register', form=form, menu=menu)


# --------------Домашняя страница--------------------------------------
@app.route('/')
def main_space():
    return render_template('base.html', title='My site', menu=menu)


# --------------Экран добавления лидов--------------------------------------
title_table_leads = [
    {"name": 'company', "type": 'text', "placeholder": 'Компания'},
    {"name": 'name', "type": 'text', "placeholder": 'ФИО'},
    {"name": 'phone', "type": 'tel', "placeholder": 'Телефон'},
    {"name": 'mail', "type": 'email', "placeholder": 'Почта'},
    {"name": 'project', "type": 'text', "placeholder": 'Проект'},
    {"name": 'amount_calc', "type": 'number', "placeholder": 'Количество расчетов'},
]


@app.route('/leads', methods=["POST", "GET"])
@login_required
def leads():
    dbase = FDataBase(get_db())
    # Добавление лидов в базу данных
    if request.method == "POST":
        checkbox_value_id_lead = request.form.getlist('check-lead')
        button_delete = request.form.get('button-delete-lead')
        button_add = request.form.get('button-add-lead')

        if checkbox_value_id_lead and button_delete:
            dbase.del_records('lead', checkbox_value_id_lead)
            records_del_calk = []
            for id_lead in checkbox_value_id_lead:
                records_del_calk.append(dbase.get_info_records('my_warehouse',
                                                               current_user.get_user_email(),
                                                               ('lead_ID', id_lead)))
            records_del_calk = list(map(lambda x: x['id'], itertools.chain.from_iterable(records_del_calk)))

            if len(records_del_calk) > 0:
                dbase.del_records('my_warehouse', records_del_calk)

        if button_add:
            res = dbase.set_new_lead(request.form.get('company'), request.form.get('name'), request.form.get('phone'),
                                     request.form.get('mail'), request.form.get('project'),
                                     current_user.get_user_email(),
                                     )
            if not res:
                flash('Ошибка добавления лида', category='error')
            else:
                flash('Лид добавлен успешно', category='success')

    # Чтение лидов из базы данных
    get_new_lead = dbase.get_info_records('lead', current_user.get_user_email())
    get_new_lead = [[row[column_name] for column_name in row.keys()] for row in get_new_lead]

    # Определение количества расчетов
    for lead in get_new_lead:
        amount_calc = dbase.get_amount_records('my_warehouse', 'lead_ID', lead[0])
        dbase.update_record("lead", 'id', lead[0], {'amount_calc': amount_calc})
        lead[7] = amount_calc

    return render_template('leads.html', title='My LEADS', menu=menu,
                           title_table_leads=title_table_leads,
                           get_new_lead=get_new_lead,
                           current_user=current_user.get_user_name(),
                           )


# ---Экран информации о лиде----------------------------------
@app.route("/lead/<alias>", methods=["POST", "GET"])
def show_info_lead(alias):
    dbase = FDataBase(get_db())
    current_lead = dbase.get_lead(alias, current_user.get_user_email())
    project_folder = os.path.join('Project_OFFERS', current_lead['company'])

    try:
        files_layout = os.listdir(project_folder + '/Layout')
    except FileNotFoundError:
        files_layout = []

    try:
        files_offer = os.listdir(project_folder + '/Offers')
    except FileNotFoundError:
        files_offer = []

    if current_lead['comments_history']:
        history_comments = current_lead['comments_history'].split(' $END_COMMENTS$ \n')
        history_event = current_lead['event'].split(' $END_EVENT$ \n')
    else:
        history_comments = []
        history_event = []

    if not current_lead:
        abort(404)

    if request.method == 'POST':
        checkbox_value = request.form.getlist('check-lead')
        button_delete = request.form.get('button-delete-calc')
        button_lead_comment = request.form.get('button-accept-comments')
        button_upload_layout = request.form.get('button-upload-layout')
        button_upload_offer = request.form.get('button-upload-offer')
        button_load_layout = request.form.get('button-load-layout')
        button_load_offer = request.form.get('button-load-offer')

        if checkbox_value and button_delete:
            dbase.del_records('my_warehouse', checkbox_value)

        if button_lead_comment:
            if request.form.get('comment-for-lead').replace(' ', ''):
                current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
                event = request.form.get('event-comments')
                history_comments.append(
                    f"<strong>{current_datetime} ({event}):</strong> \n{request.form.get('comment-for-lead')}")
                history_event.append(request.form.get('input-field-event'))
                comment = ' $END_COMMENTS$ \n'.join(history_comments)
                lead_event = ' $END_EVENT$ \n'.join(history_event)
                dbase.update_record('lead', 'id', current_lead['id'], {'comments_history': comment,
                                                                       'event': lead_event})
        #  Выгрузка макета на сервер
        if button_upload_layout:
            layout = request.files['file-layout']
            project_folder = os.path.join(project_folder, 'Layout')
            os.makedirs(project_folder, exist_ok=True)
            file_path = os.path.join(project_folder, layout.filename)
            layout.save(file_path)

        #  Выгрузка офера на сервер
        if button_upload_offer:
            # request_form = dict(request.form)
            offer = request.files['file-offer']
            project_folder = os.path.join(project_folder, 'Offers')
            os.makedirs(project_folder, exist_ok=True)
            file_path = os.path.join(project_folder, offer.filename)
            offer.save(file_path)

        #  Загрузка файла с сервера на локальный ПК
        if button_load_layout:
            filename = request.form.get('button-load-layout')
            project_folder = os.path.join('Project_OFFERS', alias, 'Layout')
            file_path = os.path.join(project_folder, filename)
            return send_file(file_path, as_attachment=True)

        #  Загрузка файла с сервера на локальный ПК
        if button_load_offer:
            filename = request.form.get('button-load-offer')
            project_folder = os.path.join('Project_OFFERS', alias, 'Offers')
            file_path = os.path.join(project_folder, filename)
            return send_file(file_path, as_attachment=True)

    title_table_calc_BVZ, value_table_calc_BVZ = view_table_warehouse(dbase, current_user, current_lead,
                                                                      'show_info_lead')
    value_table_calc_BVZ = [list(record.values()) for record in value_table_calc_BVZ]

    history_comments.reverse()
    history_event.reverse()

    history_lead = list(zip(history_comments, history_event))
    return render_template('lead.html', menu=menu, title=current_lead['company'], current_lead=current_lead,
                           title_table_calc_BVZ=title_table_calc_BVZ,
                           value_table_calc_BVZ=value_table_calc_BVZ,
                           history_lead=history_lead,
                           files_layout=files_layout,
                           files_offer=files_offer
                           )

# -----PRICING форма расчетов----------------------------------------------------->
@app.route('/pricing/<alias>', methods=["POST", "GET"])
@login_required
def calculation_product(alias):
    dbase = FDataBase(get_db())
    calc_ID = request.args.get('calc_ID')

    if calc_ID:
        request_form = dict(dbase.get_record('archive_calculating', ('id', calc_ID)))
        request_form['button_raw'] = 'button-raw-accept'
        return calculate_BVZ(dbase, request_form, menu, current_user)

    if request.method == 'POST':
        if alias == 'BVZ':
            request_form = dict(request.form)
            try:
                request_form['project'], request_form['client'] = request_form['project'].split(':-:')
            except KeyError:
                return calculate_BVZ(dbase, request_form, menu, current_user)

            return calculate_BVZ(dbase, request_form, menu, current_user)

    return 'search'
    # return view_pricing(menu)


@app.route('/pricing', methods=["POST", "GET"])
@login_required
def pricing():
    dbase = FDataBase(get_db())

    if request.method == 'POST':
        checkbox_value = request.form.getlist('check-lead')
        button_delete = request.form.get('button-delete-calc')
        if checkbox_value and button_delete:
            dbase.del_records('my_warehouse', checkbox_value)

    choose_product = [
        {"name": 'БВЗ', "product": 'BVZ'},
        {"name": 'Стеллажи', "product": 'Racks'},
        {"name": 'Мусорные баки', "product": 'Trash-can'},
        {"name": 'Поддоны', "product": 'Pallets'},
        {"name": 'Пластиковая тара', "product": 'Plastic-container'},
        {"name": 'Техника', "product": 'Equipment'},
    ]
    choose_project = []
    for row in dbase.get_info_records('lead', current_user.get_user_email()):
        if str(request.form.get('button-add-calculation')) == str(row['id']):
            choose_project.append({"project": row['project'], "lead": row['company'], "selected": 1})
        else:
            choose_project.append(
                {"project": row['project'], "lead": row['company'], "selected": 0})

    title_table_calc_BVZ, value_table_calc_BVZ = view_table_warehouse(dbase, current_user, page='pricing')
    value_table_calc_BVZ = [list(record.values()) for record in value_table_calc_BVZ]

    return render_template('pricing.html', title='My PRICING', menu=menu,

                           choose_product=choose_product,
                           choose_project=choose_project,
                           title_table_calc_BVZ=title_table_calc_BVZ,
                           value_table_calc_BVZ=value_table_calc_BVZ
                           )


# <-------------------------------------------------------------------------------->
# @app.route('/morzh', methods=["POST", "GET"])
# @login_required
# def morzh():
#     img = None
#     with app.open_resource(app.root_path + "Project")
#     return res
#     # return render_template('morzh.html', title='My MONEY', menu=menu, result=res)


@app.route('/about')
def about():
    return render_template('about.html', title='ABOUT', menu=menu)


# -----------------Модальное окно----------------------------------------
@app.route('/convert_num', methods=['POST'])
def multiply_by_10():
    data = request.json
    input_value = data['input']
    output_value = number_to_words(int(input_value))
    return jsonify({'result': output_value})

