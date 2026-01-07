from flask import render_template


def format_price(price):
    return '{:,.2f}'.format(price).replace(',', " ")


def view_BVZ(menu, update_dict=None, accept_index=None):
    accepts = ['none'] * 8
    if accept_index < 2:
        accepts[-1] = 'block'

    if accept_index is not None:
        for i in range(accept_index):
            accepts[i] = "block"
    accept_1, accept_2, accept_3, accept_4, accept_5, accept_6, accept_7, accept_s = accepts

    m_dict = {'width': False, 'length': False, 'height': False, 'area': False, 'volume': False,
              'temperature': False, 'client': False, 'price_project': False,
              'price_square_meters': False, 'price_cubic_meters': False,
              'price_cost': False, "cost_sq_m_w": False, 'price_VAT': False, 'profit_UA': False,
              'cost_price': False, 'profit_EU': False, 'price_selling_EU': False, 'price_selling_UA': False,
              'price_delivery': False, 'price_warehouse': False, 'price_building': False,
              'price_foundation': False, 'price_sq_met_found': 0, 'price_light': False, 'price_rack': False,
              'dimension_found': 0, 'area_found': 0, 'percent_w': False, 'percent_f': False, 'percent_o': False,
              'price_selling': False, 'amount_calc': 0, 'comments': 'no comments', 'test': 0,
              'exchange_rates_from': False, 'exchange_rates_TO': False, 'profit_percent': False,
              'cost_square_meters_EU': False, 'cost_cubic_meters_EU': False, 'price_sendvich': 0,
              'cost_square_meters_UA': False, 'cost_cubic_meters_UA': False, 'price_gate': 0,
              'cost_foundation': False, 'cost_option': False, 'cost_sq_met_found': False,
              'final_price_UA': False, 'final_profit_UA': False, 'final_profit_percent': False,
              'unique_ID': 'Empty', 'final_cost_sq_m_pr': False, 'product': False, 'project': False,
              'S_panel': False, 'H_skate': False, 'wall': False, 'lighting': False, 'racks': False,
              'sendvich': False, 'gates': False, 'price_sq_met_sendvich': False, 'profit_warehouse_UA': 0,
              'price_sell_sendvich_UA': 0, 'price_sell_light_UA': 0, 'price_sell_gate_UA': 0, 'price_sell_rack_UA': 0,
              'profit_sendvich_UA': 0,  'profit_light_UA': 0, 'profit_gate_UA': 0, 'profit_rack_UA': 0,
              'price_sell_warehouse_UA': 0, 'price_sell_warehouse_EU': 0,
              'price_sell_warehouse_option_EU': 0, 'profit_warehouse_option_EU': 0,
              'price_sell_warehouse_option_UA': 0, 'profit_warehouse_option_UA': 0,
              }

    if update_dict is not None:
        for key, vol in update_dict.items():
            m_dict[key] = vol

    if m_dict["price_light"] == '':
        m_dict["price_light"] = 0

    if m_dict["price_rack"] == '':
        m_dict["price_rack"] = 0

    if m_dict["price_foundation"] == '':
        m_dict["price_foundation"] = 0

    # ОТОБРАЖЕНИЕ БЛОКА С ВВОДОМ ДАННЫХ--------------------------------------------------------------------------------
    # 1 - блок ввода размеров
    set_title_table_dimension = [
        {"name": 'width', "title": 'ширина', "placeholder": 'метры', "current_vol": m_dict['width']},
        {"name": 'length', "title": 'длинна', "placeholder": 'метры', "current_vol": m_dict['length']},
        {"name": 'height', "title": 'высота', "placeholder": 'метры', "current_vol": m_dict['height']}
    ]

    # 2 - блок ввода стоимостей склада
    set_title_table_pricing = [
        {"name": 'price_warehouse', "title": 'склад', "placeholder": 'евро', "current_vol": m_dict['price_warehouse']},
        {"name": 'price_delivery', "title": 'доставка', "placeholder": 'евро', "current_vol": m_dict['price_delivery']},
        {"name": 'price_building', "title": 'монтаж', "placeholder": 'евро', "current_vol": m_dict['price_building']},
    ]

    # 3 - блок ввода дополнительных стоимостей и фундамента
    set_title_table_second_pricing = [
        {"name": 'price_sq_met_found', "title": 'полы 1m²', "placeholder": 'евро',
         "current_vol": m_dict['price_sq_met_found'], "display": True},

        {"name": 'price_light', "title": 'освещение', "placeholder": 'евро',
         "current_vol": m_dict['price_light'], "display": bool(m_dict['lighting'])},

        {"name": 'price_rack', "title": 'стеллажи', "placeholder": 'евро',
         "current_vol": m_dict['price_rack'], "display": bool(m_dict['racks'])},

        {"name": 'price_sq_met_sendvich', "title": 'стены 1m²', "placeholder": 'евро',
         "current_vol": m_dict['price_sq_met_sendvich'], "display": bool(m_dict['sendvich'])},

        {"name": 'price_gate', "title": 'ворота', "placeholder": 'евро',
         "current_vol": m_dict['price_gate'], "display": bool(m_dict['gates'])}
    ]

    # 3 - блок ввода маржинальности
    set_profit = [
        {"name": 'percent_w', "title": 'склад', "placeholder": '%', "current_vol": m_dict['percent_w']},
        {"name": 'percent_f', "title": 'фундамент', "placeholder": '%', "current_vol": m_dict['percent_f']},
        {"name": 'percent_o', "title": 'опции', "placeholder": '%', "current_vol": m_dict['percent_o']},

        {"name": 'exchange_rates_from', "title": 'поставщик', "placeholder": 'Евро', "current_vol": m_dict['exchange_rates_from']},
        {"name": 'exchange_rates_TO', "title": 'клиент', "placeholder": 'Евро', "current_vol": m_dict['exchange_rates_TO']},
    ]

    # ОТОБРАЖЕНИЕ БЛОКА С ВЫВОДОМ ВЫЧИСЛЕНИЙ---------------------------------------------------------------------------
    # 0 - блок с информацией о параметрах склада и проекта
    get_final_setting = [
        {"name": 'product', "title": 'Продукт: ', "value": m_dict['product'],
         "description": 'Быстровозводимая конструкция, подходящая для складов и производственных помещений'},

        {"name": 'client', "title": 'Клиент: ', "value": m_dict['client'],
         "description": 'Клиент, для которого делается расчет стоимости'},

        {"name": 'project', "title": 'Проект: ', "value": m_dict['project'],
         "description": 'Название рассчитываемого проекта'},

        {"name": 'temperature', "title": 'Температура: ', "value": m_dict['temperature'],
         "description": 'Теплый - сендвич-панели и крыша с изоляцией.\n'
                        'Холодный - ПВХ и профнастил.\n'
                        'Зерно - конструктив с опорными стенами.'},

        {"name": 'wall', "title": 'Поставщик стен: ', "value": m_dict['wall'],
         "description": 'Материалы для стен закупаются у данного поставщика'},
    ]

    # 1 - блок с размерами
    get_title_table_dimension = [
        {"result": f"Ш: {m_dict['width']}m | Д: {m_dict['length']}m | В: {m_dict['height']}m", "title": 'Размеры склада: '},

        {"result": f"{m_dict['area']} m²", "title": 'Площадь: '},
        {"result": f"{m_dict['volume']} m³", "title": 'Объем: '},

        {"result": f"{m_dict['S_panel']} m²", "title": 'Сэндвич [S]: '},
        {"result": f"{m_dict['H_skate']} m", "title": 'Конёк [H]: '},
    ]

    # 2 - блок с затратами
    get_title_table_pricing = [
        {"name": 'price_warehouse', "title": 'Склад без НДС: ', "result": f"{format_price(m_dict['price_warehouse'])} €"},
        {"name": 'price_customs', "title": '1 [m²] без НДС: ', "result": f"{format_price(m_dict['cost_sq_m_w'])} €"},
        {"name": 'price_VAT', "title": 'НДС: ', "result": f"{format_price(m_dict['price_VAT'])} €"},

        {"name": 'cost_price', "title": 'На таможне: ', "result": f"{format_price(m_dict['cost_price'])} €"},
        {"name": 'price_square_meters', "title": '1 [m²] с НДС: ', "result": f"{format_price(m_dict['price_square_meters'])} €"},
        {"name": 'price_cubic_meters', "title": '1 [m³] с НДС: ', "result": f"{format_price(m_dict['price_cubic_meters'])} €"},

        {"name": 'price_project', "title": 'Доп затраты ',
         "result": f"{format_price(m_dict['price_delivery'] + m_dict['price_building'])} €"},
        {"name": 'price_delivery', "title": 'Доставка: ', "result": f"{format_price(m_dict['price_delivery'])} €"},
        {"name": 'price_building', "title": 'Монтаж: ', "result": f"{format_price(m_dict['price_building'])} €"},
    ]

    # 3 - блок фундамента и доп затрат
    get_title_table_cost = [
        {"name": 'dimension_found', "title": 'Пятно : ', "result": f"{m_dict['dimension_found']}"},
        {"name": 'area_found', "title": 'Пятно [S]: ', "result": f"{m_dict['area_found']} m²"},

        {"name": 'price_foundation', "title": 'Фундамент: ', "result": f"{format_price(m_dict['price_foundation'])} €"},
        {"name": 'price_sq_met_found', "title": '1 [m²] с НДС: ', "result": f"{m_dict['price_sq_met_found']} €"},

        {"name": 'price_sendvich', "title": 'Стены: ', "result": f"{format_price(m_dict['price_sendvich'])} €",
         "display": bool(m_dict['price_sendvich'])},

        {"name": 'price_light', "title": 'Освещение: ', "result": f"{format_price(m_dict['price_light'])} €",
         "display": bool(m_dict['lighting'])},

        {"name": 'price_gate', "title": 'Ворота: ', "result": f"{format_price(m_dict['price_gate'])} €",
         "display": bool(m_dict['price_gate'])},

        {"name": 'price_rack', "title": 'Стеллажи: ', "result": f"{format_price(m_dict['price_rack'])} €",
         "display": bool(m_dict['price_rack'])}
    ]

    # 4 - блок с результатами расчетов цены продажи
    get_title_table_total_coast = [
        {"name": 'price_sell_warehouse_UA', "title": 'Склад: ', "result": f"{format_price(m_dict['price_sell_warehouse_UA'])} грн"},
        {"name": 'price_sell_sendvich', "title": 'Стены: ', "result": f"{format_price(m_dict['price_sell_sendvich_UA'])} грн"},
        {"name": 'price_sell_light', "title": 'Освещение: ', "result": f"{format_price(m_dict['price_sell_light_UA'])} грн"},
        {"name": 'price_sell_gate', "title": 'Ворота: ', "result": f"{format_price(m_dict['price_sell_gate_UA'])} грн"},
        {"name": 'price_sell_rack_UA', "title": 'Стеллажи: ', "result": f"{format_price(m_dict['price_sell_rack_UA'])} грн"},

        {"name": 'profit_warehouse_UA', "title": 'маржа: ', "result": f"{format_price(m_dict['profit_warehouse_UA'])} грн"},
        {"name": 'profit_sendvich_UA', "title": 'маржа: ', "result": f"{format_price(m_dict['profit_sendvich_UA'])} грн"},
        {"name": 'profit_light_UA', "title": 'маржа: ', "result": f"{format_price(m_dict['profit_light_UA'])} грн"},
        {"name": 'profit_gate_UA', "title": 'маржа: ', "result": f"{format_price(m_dict['profit_gate_UA'])} грн"},
        {"name": 'profit_rack_UA', "title": 'маржа: ', "result": f"{format_price(m_dict['profit_rack_UA'])} грн"},

        {"name": 'price_selling_EU', "title": 'Склад EU: ', "result": f"{format_price(m_dict['price_sell_warehouse_option_EU'])} €"},
        {"name": 'profit_EU', "title": 'Маржа EU: ', "result": f"{format_price(m_dict['profit_warehouse_option_EU'])} €"},
        {"name": 'cost_square_meters_EU', "title": 'цена 1 [m²]: ', "result": f"{format_price(m_dict['cost_square_meters_EU'])} €"},


        {"name": 'price_selling_UA', "title": 'Склад UA: ', "result": f"{format_price(m_dict['price_sell_warehouse_option_UA'])} грн"},
        {"name": 'profit_UA', "title": 'Маржа UA: ', "result": f"{format_price(m_dict['profit_warehouse_option_UA'])} грн"},
        {"name": 'cost_square_meters_UA', "title": 'цена 1 [m²]: ', "result": f"{format_price(m_dict['cost_square_meters_UA'])} грн"},

        {"name": 'cost_foundation', "title": 'Фундамент: ', "result": f"{format_price(m_dict['cost_foundation'])} грн"},
        {"name": 'cost_option', "title": 'Маржа: ', "result": f"{format_price(m_dict['cost_option'])} грн"},
        {"name": 'cost_sq_met_found', "title": 'цена 1 [m²]: ', "result": f"{format_price(m_dict['cost_sq_met_found'])} грн"},
    ]

    final_price_warehouse = [
        {"name": 'final_price_UA', "title": 'СТОИМОСТЬ ПРОЕКТА', "result": f"{format_price(m_dict['final_price_UA'])} грн"},
        {"name": 'final_profit_UA', "title": 'МАРЖИНАЛЬНОСТЬ ПРОЕКТА', "result": f"{format_price(m_dict['final_profit_UA'])} грн"},
        {"name": 'final_cost_sq_m_pr', "title": 'Цена 1 [m²]', "result": f"{format_price(m_dict['final_cost_sq_m_pr'])} грн"},
        {"name": 'final_profit_percent', "title": 'ДОХОДНОСТЬ', "result": f"{format_price(m_dict['final_profit_percent'])} %"},
    ]

    title_table = [
        {"name": 'width', "title": 'Ширина'},
        {"name": 'length', "title": 'Длинна'},
        {"name": 'height', "title": 'Высота'},
        {"name": 'area', "title": 'Площадь'},
        {"name": 'price_warehouse', "title": 'Цена склада'},
        {"name": 'price_delivery', "title": 'Цена доставки'},
        {"name": 'price_building', "title": 'Цена монтажа'},
        {"name": 'cost_foundation', "title": 'Цена фундамента'},
        {"name": 'cost_option', "title": 'Цена опций'},
        {"name": 'final_profit_UA', "title": 'Маржа'},
        {"name": 'final_price_UA', "title": 'Цена проекта'},
        {"name": 'cost_square_meters_UA', "title": 'Цена 1 [m²]'},
        {"name": 'final_profit_percent', "title": 'Доход'},
    ]

    return render_template('warehouse.html',
                           title='BVZ',
                           menu=menu,
                           accept_s=accept_s,
                           accept_1=accept_1,
                           accept_2=accept_2,
                           accept_3=accept_3,
                           accept_4=accept_4,
                           accept_5=accept_5,
                           accept_6=accept_6,
                           accept_7=accept_7,
                           set_title_table_dimension=set_title_table_dimension,
                           set_title_table_pricing=set_title_table_pricing,
                           set_title_table_second_pricing=set_title_table_second_pricing,
                           set_profit=set_profit,
                           get_title_table_cost=get_title_table_cost,
                           get_title_table_dimension=get_title_table_dimension,
                           get_title_table_pricing=get_title_table_pricing,
                           get_title_table_total_coast=get_title_table_total_coast,
                           title_table=title_table,
                           m_dict=m_dict,
                           final_price_warehouse=final_price_warehouse,
                           product=m_dict['product'],
                           get_final_setting=get_final_setting,
                           current_lead=m_dict['client'],
                           )
