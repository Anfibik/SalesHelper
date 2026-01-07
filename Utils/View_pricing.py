from flask import render_template


def view_pricing(menu, choose_project='Empty'):
    choose_product = [
        {"name": 'БВЗ', "product": 'BVZ'},
        {"name": 'Стеллажи', "product": 'Racks'},
        {"name": 'Мусорные баки', "product": 'Trash_can'},
        {"name": 'Поддоны', "product": 'Pallets'},
        {"name": 'Пластиковая тара', "product": 'Plastic_container'},
        {"name": 'Техника', "product": 'Equipment'},
    ]

    return render_template('pricing.html', title='My PRICING', menu=menu,

                           choose_product=choose_product,
                           choose_project=choose_project,

                           )
