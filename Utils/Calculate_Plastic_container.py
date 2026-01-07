from flask import render_template


def calculate_Plastic_container(dbase, request_form, menu, current_user):
    return render_template('Plastic_container.html', title='Plastic_container', menu=menu)