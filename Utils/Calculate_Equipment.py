from flask import render_template


def calculate_Equipment(dbase, request_form, menu, current_user):
    return render_template('Equipment.html', title='Equipment', menu=menu)