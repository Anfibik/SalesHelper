from flask import render_template


def calculate_Racks(dbase, request_form, menu, current_user):
    return render_template('Racks.html', title='Racks', menu=menu)