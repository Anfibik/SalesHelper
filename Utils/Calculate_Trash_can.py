from flask import render_template


def calculate_Trash_can(dbase, request_form, menu, current_user):
    return render_template('Trash_can.html', title='Trash_can', menu=menu)