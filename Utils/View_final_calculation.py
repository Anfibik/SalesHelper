def format_price(price):
    return '{:,.2f}'.format(int(price)).replace(',', " ")


title_table = [
    {"name": 'width', "title": 'Ширина'},
    {"name": 'length', "title": 'Длинна'},
    {"name": 'height', "title": 'Высота'},
    {"name": 'area', "title": 'Площадь'},
    {"name": 'price_warehouse', "title": 'Склад нетто'},
    {"name": 'percent_w', "title": 'Маржа %'},
    {"name": 'price_delivery', "title": 'Доставка'},
    {"name": 'price_building', "title": 'Монтаж'},
    {"name": 'price_selling_UA', "title": 'Склад'},
    {"name": 'cost_square_meters_UA', "title": 'Склад 1[m²]'},
    {"name": 'price_foundation', "title": 'Пол'},
    {"name": 'cost_sq_met_found', "title": 'Пол 1[m²]'},
    {"name": 'temperature', "title": 'Температура'},
    {"name": 'final_price_UA', "title": 'Стоимость проекта'},
    {"name": 'final_cost_sq_m_pr', "title": 'За 1[m²]'},
    {"name": 'final_profit_UA', "title": 'Доход'},
    {"name": 'final_profit_percent', "title": 'Доход'},
]


def view_table_warehouse(dbase, current_user, current_lead=None, page=None, sort_info='height'):
    body_table = []
    current_records = {}
    if page == 'show_info_lead':
        if dbase.check_records('my_warehouse'):
            current_records = dbase.get_info_records('my_warehouse',
                                                     current_user.get_user_email(),
                                                     ('client', current_lead['company']))
    elif page == 'pricing':
        if dbase.check_records('archive_calculating'):
            current_records = dbase.get_info_records('archive_calculating', current_user.get_user_email())
            current_records = sorted(current_records, key=lambda x: x[sort_info])

    for record in current_records:
        mask_value_project_in_table = {
            "id": record['id'],
            "unique_ID": record['unique_ID'],
            "width": f"{record['width']} m",
            "length": f"{record['length']} m",
            "height": f"{record['height']} m",
            "area": f"{record['area']} m²",
            "price_warehouse": f"{format_price(record['price_warehouse'])} euro",
            "percent_w": f"{record['percent_w']} %",
            "price_delivery": f"{format_price(record['price_delivery'] * record['exchange_rates_TO'])} грн",
            "price_building": f"{format_price(record['price_building'] * record['exchange_rates_TO'])} грн",
            "price_selling_UA": f"{format_price(record['price_sell_warehouse_UA'])} грн",
            "cost_square_meters_UA": f"{format_price(record['cost_square_meters_UA'])} грн",
            "cost_foundation": f"{format_price(record['cost_foundation'])} грн",
            "cost_sq_met_found": f"{format_price(record['cost_sq_met_found'])} грн",
            "temperature": f"{record['temperature']}",
            "final_price_UA": f"{format_price(record['final_price_UA'])} грн",
            "final_cost_sq_m_pr": f"{format_price(record['final_cost_sq_m_pr'])} грн",
            "final_profit_UA": f"{format_price(record['final_profit_UA'])} грн",
            "final_profit_percent": f"{format_price(record['final_profit_percent'])} %",
            "comments": record['comments'],
        }
        body_table.append(mask_value_project_in_table)

    return title_table, body_table
