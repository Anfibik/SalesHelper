import itertools
import os
import sqlite3
from string import ascii_lowercase, digits

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, g, session, json
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from pip._vendor import requests
from werkzeug.security import generate_password_hash, check_password_hash

from Utils.Calculate_BVZ import calculate_BVZ
from Utils.Calculate_Equipment import calculate_Equipment
from Utils.Calculate_Pallets import calculate_Pallets
from Utils.Calculate_Racks import calculate_Racks
from Utils.Calculate_Plastic_container import calculate_Plastic_container
from Utils.Calculate_Trash_can import calculate_Trash_can
from Utils.FDataBase import FDataBase
from Utils.NumConvert import number_to_words
from Utils.UserLogin import UserLogin
from Utils.View_final_calculation import view_table_warehouse
from Utils.form import LoginForm, RegistrationForm

# Конфигурация
DATABASE = '/tmp/SH_site.db'
DEBUG = True
SECRET_KEY = 'fdgfh78@#5?>gfhf89dx,v06k'
USERNAME = 'admin'
PASSWORD = '123'

# Инициализируем приложение
app = Flask(__name__)
app.static_folder = 'static'
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
    {"url": '/project_accept', "name": 'Запущенные проекты'},
    {"url": '/testpage', "name": 'Тестовая среда'},
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
    button_sort_company = dbase.get_record('users', ('email', current_user.get_user_email()))['sort_value']
    check_filter = False

    # Добавление лидов в базу данных
    if request.method == "POST":
        checkbox_value_id_lead = request.form.getlist('check-lead')
        button_delete = request.form.get('button-delete-lead')
        button_add = request.form.get('button-add-lead')
        if request.form.get('lead_qualiti'):
            dbase.update_record('users', 'sort_value', button_sort_company,
                                {'sort_value': request.form.get('lead_qualiti')})
            button_sort_company = request.form.get('lead_qualiti')
        check_filter = request.form.get('filter')

        if checkbox_value_id_lead and button_delete:
            dbase.del_records('lead', checkbox_value_id_lead)
            if len(checkbox_value_id_lead) > 1:
                flash("Записи успешно удалены")
            else:
                flash("Запись успешно удалена")
            records_del_calk = []
            for id_lead in checkbox_value_id_lead:
                records_del_calk.append(dbase.get_info_records('my_warehouse',
                                                               current_user.get_user_email(),
                                                               ('lead_ID', id_lead)))
            records_del_calk = list(map(lambda x: x['id'], itertools.chain.from_iterable(records_del_calk)))
            if len(records_del_calk) > 0:
                dbase.del_records('my_warehouse', records_del_calk)

        if button_add:
            name_company = request.form.get('company')
            symbols = ascii_lowercase + digits + "йцукенгшщзхъэждлорпавыфячсмитьбюёії'"
            for s in name_company:
                if s.lower() not in symbols:
                    name_company = name_company.replace(s, ' ')
            name_company = name_company.split()
            name_company = "_".join(name_company)
            res = dbase.set_new_lead(name_company, request.form.get('name'), request.form.get('phone'),
                                     request.form.get('mail'), request.form.get('project'),
                                     current_user.get_user_email(),
                                     )
            if not res:
                flash('Ошибка добавления сделки')
            else:
                flash(f'Сделка {name_company} добавлена успешно')

    # Чтение лидов из базы данных
    get_new_lead = dbase.get_info_records('lead', current_user.get_user_email())
    get_new_lead = [[row[column_name] for column_name in row.keys()] for row in get_new_lead]
    get_new_lead.reverse()

    # Определение количества расчетов
    for lead in get_new_lead:
        amount_calc = dbase.get_amount_records('my_warehouse', 'lead_ID', lead[0])
        dbase.update_record("lead", 'id', lead[0], {'amount_calc': amount_calc})
        lead[7] = amount_calc

    #  Сортировка сделок по их значимости

    if int(button_sort_company) == 1:
        if check_filter:
            get_new_lead = sorted(filter(lambda x: x[10] == 1, get_new_lead), reverse=True)
        else:
            get_new_lead = sorted(get_new_lead, key=lambda x: x[10])

    if int(button_sort_company) == 2:
        if check_filter:
            get_new_lead = sorted(filter(lambda x: x[10] == 2, get_new_lead), reverse=True)
        else:
            get_new_lead = sorted(get_new_lead, key=lambda x: x[10])

    if int(button_sort_company) == 3:
        if check_filter:
            get_new_lead = sorted(filter(lambda x: x[10] == 3, get_new_lead), reverse=True)
        else:
            get_new_lead = sorted(get_new_lead, key=lambda x: x[10], reverse=True)

    return render_template('leads.html', title='My Trades', menu=menu,
                           title_table_leads=title_table_leads,
                           get_new_lead=get_new_lead,
                           current_user=current_user.get_user_name()
                           )


# ---Экран информации о лиде----------------------------------
@app.route("/lead/<alias>", methods=["POST", "GET"])
def show_info_lead(alias):
    def download_files(project_path, work_folder):
        layout = request.files.getlist('file')
        project_path = os.path.join('static', project_path, work_folder)
        os.makedirs(project_path, exist_ok=True)
        for file in layout:
            file_path = os.path.join(project_path, file.filename)
            file.save(file_path)

    dbase = FDataBase(get_db())
    current_lead = dbase.get_lead(alias, current_user.get_user_email())

    project_folder = '/'.join(['Project_OFFERS', alias])
    description = current_lead['description']
    lead_qualiti = current_lead['lead_qualiti']
    button_add_final_data_project = None
    edit_description_on = 0

    try:
        folder_path = 'static/' + project_folder + '/Offers'
        files_offer = os.listdir(folder_path)
        files_offer = sorted(files_offer, key=lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)
    except FileNotFoundError:
        files_offer = []

    try:
        folder_path = 'static/' + project_folder + '/Layout'
        files_layout = os.listdir(folder_path)
        files_layout = sorted(files_layout, key=lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)
    except FileNotFoundError:
        files_layout = []

    try:
        folder_path = 'static/' + project_folder + '/Photos'
        files_photos = os.listdir(folder_path)
        files_photos = sorted(files_photos, key=lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)
    except FileNotFoundError:
        files_photos = []

    try:
        folder_path = 'static/' + project_folder + '/Client_Info'
        files_client_info = os.listdir(folder_path)
        files_client_info = sorted(files_client_info, key=lambda x: os.path.getctime(os.path.join(folder_path, x)),
                                   reverse=True)
    except FileNotFoundError:
        files_client_info = []

    try:
        folder_path = 'static/' + project_folder + '/Layout_Protan'
        files_layout_protan = os.listdir(folder_path)
        files_layout_protan = sorted(files_layout_protan, key=lambda x: os.path.getctime(os.path.join(folder_path, x)),
                                     reverse=True)
    except FileNotFoundError:
        files_layout_protan = []

    try:
        folder_path = 'static/' + project_folder + '/Contract'
        files_contract = os.listdir(folder_path)
        files_contract = sorted(files_contract, key=lambda x: os.path.getctime(os.path.join(folder_path, x)),
                                reverse=True)
    except FileNotFoundError:
        files_contract = []

    if current_lead['comments_history']:
        history_comments = current_lead['comments_history'].split(' $END_COMMENTS$ \n')
        history_event = current_lead['event'].split(' $END_EVENT$ \n')
    else:
        history_comments = []
        history_event = []

    if request.method == 'POST':
        checkbox_value = request.form.getlist('check-lead')

        button_delete = request.form.get('button-delete-calc')
        button_lead_comment = request.form.get('button-accept-comments')
        button_description_save = request.form.get('description')
        button_description_edit = request.form.get('edit_description')
        button_upload = request.form.get('button-upload')

        button_add_final_data_project = request.form.get('add-final-data-project', )
        button_watch_final_data_project = request.form.get('watch-final-data-project')
        button_delete_comment = request.form.get('delete_comment')

        if request.form.get('lead_qualiti'):
            lead_qualiti = request.form.get('lead_qualiti')
            dbase.update_record('lead', 'id', current_lead['id'], {'lead_qualiti': lead_qualiti})

        if button_upload:
            download_files(project_folder, button_upload)

        if checkbox_value and button_delete:
            dbase.del_records('my_warehouse', checkbox_value)

        if button_description_save:
            description = request.form.get('description')
            dbase.update_record('lead', 'id', current_lead['id'], {'description': description})

        if button_description_edit:
            edit_description_on = 1

        if button_delete_comment:
            history_comments.pop()
            history_event.pop()
            comment = ' $END_COMMENTS$ \n'.join(history_comments)
            lead_event = ' $END_EVENT$ \n'.join(history_event)
            dbase.update_record('lead', 'id', current_lead['id'], {'comments_history': comment,
                                                                   'event': lead_event})

        if button_lead_comment:
            if request.form.get('comment-for-lead').replace(' ', ''):
                current_datetime = button_lead_comment
                event = request.form.get('event-comments')
                history_comments.append(
                    f"<strong>[{current_datetime[:-3]}] {event}:</strong> \n{request.form.get('comment-for-lead')}")
                history_event.append(request.form.get('input-field-event'))
                comment = ' $END_COMMENTS$ \n'.join(history_comments)
                lead_event = ' $END_EVENT$ \n'.join(history_event)
                dbase.update_record('lead', 'id', current_lead['id'], {'comments_history': comment,
                                                                       'event': lead_event})

    title_table_calc_BVZ, value_table_calc_BVZ = view_table_warehouse(dbase, current_user, current_lead,
                                                                      'show_info_lead')
    value_table_calc_BVZ = [list(record.values()) for record in value_table_calc_BVZ]

    history_comments.reverse()
    history_event.reverse()

    if button_add_final_data_project:
        return render_template('add_project_accept_info.html', menu=menu, title=current_lead['company'],
                               current_lead=current_lead,
                               title_table_calc_BVZ=title_table_calc_BVZ,
                               value_table_calc_BVZ=value_table_calc_BVZ,

                               )

    history_lead = list(zip(history_comments, history_event))
    return render_template('lead.html', menu=menu, title=current_lead['company'], current_lead=current_lead,
                           title_table_calc_BVZ=title_table_calc_BVZ,
                           value_table_calc_BVZ=value_table_calc_BVZ,
                           history_lead=history_lead,
                           description=description,
                           edit_description_on=edit_description_on,
                           lead_qualiti=lead_qualiti,
                           files_layout=files_layout,
                           files_client_info=files_client_info,
                           files_offer=files_offer,
                           files_contract=files_contract,
                           files_photos=files_photos,
                           files_layout_protan=files_layout_protan,
                           project_folder=project_folder
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

        elif alias == 'Racks':
            request_form = dict(request.form)
            return calculate_Racks(dbase, request_form, menu, current_user)

        elif alias == 'Equipment':
            request_form = dict(request.form)
            return calculate_Equipment(dbase, request_form, menu, current_user)

        elif alias == 'Plastic_container':
            request_form = dict(request.form)
            return calculate_Plastic_container(dbase, request_form, menu, current_user)

        elif alias == 'Pallets':
            request_form = dict(request.form)
            return calculate_Pallets(dbase, request_form, menu, current_user)

        elif alias == 'Trash_can':
            request_form = dict(request.form)
            return calculate_Trash_can(dbase, request_form, menu, current_user)


@app.route('/pricing', methods=["POST", "GET"])
@login_required
def pricing():
    dbase = FDataBase(get_db())
    sort_info = 'height'
    if request.method == 'POST':  # Удаление выбранных расчетов из архива
        checkbox_value = request.form.getlist('check-lead')
        button_delete = request.form.get('button-delete-calc')
        if not request.form.get('button-sort'):
            sort_info = 'height'
        else:
            sort_info = request.form.get('button-sort')
        if checkbox_value and button_delete:
            dbase.del_records('archive_calculating', checkbox_value)

    choose_product = [
        {"name": 'БВЗ', "product": 'BVZ'},
        {"name": 'Стеллажи', "product": 'Racks'},
        {"name": 'Мусорные баки', "product": 'Trash_can'},
        {"name": 'Поддоны', "product": 'Pallets'},
        {"name": 'Пластиковая тара', "product": 'Plastic_container'},
        {"name": 'Техника', "product": 'Equipment'},
    ]
    choose_project = []
    for row in dbase.get_info_records('lead', current_user.get_user_email()):
        if str(request.form.get('button-add-calculation')) == str(row['id']):
            choose_project.append({"project": row['project'], "lead": row['company'], "selected": 1})
        else:
            choose_project.append(
                {"project": row['project'], "lead": row['company'], "selected": 0})

    title_table_calc_BVZ, value_table_calc_BVZ = view_table_warehouse(dbase, current_user, page='pricing',
                                                                      sort_info=sort_info)
    value_table_calc_BVZ = [list(record.values()) for record in value_table_calc_BVZ]
    choose_project.reverse()

    return render_template('pricing.html', title='My PRICING', menu=menu,

                           choose_product=choose_product,
                           choose_project=choose_project,
                           title_table_calc_BVZ=title_table_calc_BVZ,
                           value_table_calc_BVZ=value_table_calc_BVZ
                           )


@app.route('/project_accept', methods=['POST', 'GET'])
def project_accept():
    return render_template('project_accept.html', menu=menu)


@app.route('/add_project_accept_info', methods=['POST', 'GET'])
def add_project_accept_info():
    print('test', request.form.get('test'))
    return render_template('add_project_accept_info.html', menu=menu)


@app.route('/testpage', methods=['POST', 'GET'])
def testpage():
    dbase = FDataBase(get_db())
    button_currency = request.form.get('button-currency')

    if button_currency:
        print(button_currency)
        url = 'http://api.minfin.com.ua/summary/0353484a4845311e26f59a3296e6b297655e3736/'

        try:
            response = requests.get(url).json()
            print(response)
            euro_sell = response[0]['ask']
            euro_buy = response[0]['bid']
            usd_sell = response[1]['ask']
            usd_buy = response[1]['bid']

            dbase.add_record('updated_information',
                             {
                                 'currency_euro_sell': euro_sell,
                                 'currency_euro_buy': euro_buy,
                                 'currency_usd_sell': usd_sell,
                                 'currency_usd_buy': usd_buy
                             })

            result = (f"Курсы валют: евро продажа: {euro_sell}, покупка {euro_buy} "
                      f"доллар продажа: {usd_sell}, покупка {usd_buy}")

            return render_template('testpage.html', menu=menu, result=result)

        except Exception as e:
            error = f'Данные от минфин не получены'
            res = dbase.get_all_value('updated_information')
            result = (
                f"Архив курса валют: евро продажа: {res['currency_euro_sell']}, покупка {res['currency_euro_buy']} "
                f"доллар продажа: {res['currency_usd_sell']}, покупка {res['currency_usd_buy']} <p>{error}</p>")
            return render_template('testpage.html', menu=menu, result=result)

    return render_template('testpage.html', menu=menu)


@app.errorhandler(404)
def pageNot(error):
    text = "You have to wright correctly site address"
    return f"<h3>Page not found</h3>\n <p>{text}", 404


@app.route('/about')
def about():
    about_page = render_template('about.html', title='ABOUT', menu=menu)
    print(about_page)
    return about_page


# -----------------Модальное окно----------------------------------------
@app.route('/convert_num', methods=['POST'])
def multiply_by_10():
    data = request.json
    input_value = data['input']
    output_value = number_to_words(int(input_value))
    return jsonify({'result': output_value})
