from flask import render_template


def calculate_Pallets(dbase, request_form, menu, current_user):
    return render_template('Pallets.html', title='Pallets', menu=menu)