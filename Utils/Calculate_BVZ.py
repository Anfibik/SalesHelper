"""Форма расчета бюджета БВЗ, все ключевые расчетные процессы, происходящие под капотом. Результат выдается в View"""

from math import ceil

from Utils.Calculate_S_panel import calculate_S_panel
from Utils.View_BVZ import view_BVZ
from Utils.UniqueID import string_to_ID


def calculate_BVZ(dbase, request_form, menu, current_user):
    # ----------------- Выбор продукта и проекта---------------------------------------------------------------------
    if "button-accept-settings" in request_form:
        dbase.del_records('warehouse')
        request_form['user_email'] = current_user.get_user_email()
        request_form['selected'] = True
        request_form['lead_ID'] = dbase.get_record('lead', ('company', request_form['client']))['id']
        del request_form['button-accept-settings']
        dbase.add_record('warehouse', request_form)
        return view_BVZ(menu, request_form, accept_index=1)

    #  ----------------Выбор опций склада---------------------------------------------------------------------
    if "button-accept-temperature" in request_form:
        del request_form['button-accept-temperature']
        record = dbase.get_last_record('warehouse')
        lead_ID = dbase.get_record('lead', ('company', record['client']))['id']
        request_form['lead_ID'] = lead_ID

        dbase.update_record('warehouse', 'id', record['id'], request_form)

        last_data = dict(list(dict(dbase.get_last_record("warehouse")).items())[1::])
        return view_BVZ(menu, last_data, accept_index=2)

    #  ----------------------Ввод размеров и вывод площадей---------------------------------------------------------
    if "button-accept-dimension" in request_form:
        dimension = dict(list(request_form.items())[:-1])
        dimension['area'] = float(dimension['width']) * float(dimension['length'])
        dimension['volume'] = float(dimension['width']) * float(dimension['length']) * float(dimension['height'])
        value_S_H = calculate_S_panel(float(dimension['width']), float(dimension['length']), float(dimension['height']))
        dimension['S_panel'] = value_S_H[0]
        dimension['H_skate'] = value_S_H[1]
        dbase.update_record('warehouse', 'id', dbase.get_last_record("warehouse")['id'], dimension)
        last_data = dict(list(dict(dbase.get_last_record("warehouse")).items())[1::])
        return view_BVZ(menu, last_data, accept_index=3)

    #  ----------------------Ввод и вывод основных стоимостей--------------------------------------------------------
    if "button-accept-pricing" in request_form:
        price = dict(list(request_form.items())[:-1])
        dbase.update_record("warehouse", 'id', dbase.get_last_record("warehouse")['id'], price)
        last_data = dict(list(dict(dbase.get_last_record("warehouse")).items())[1::])

        last_data["cost_sq_m_w"] = last_data["price_warehouse"] / last_data["area"]
        last_data["price_VAT"] = last_data["price_warehouse"] * 20 / 100
        last_data["cost_price"] = last_data["price_warehouse"] + (last_data["price_warehouse"] * 1 / 100) + last_data[
            "price_VAT"]
        last_data["price_square_meters"] = round(last_data["cost_price"] / last_data['area'], 2)
        last_data["price_cubic_meters"] = round(last_data["cost_price"] / last_data['volume'], 2)
        last_data["price_project"] = last_data["cost_price"] + last_data["price_delivery"] + last_data["price_building"]
        dbase.update_record("warehouse", 'id', dbase.get_last_record("warehouse")['id'], last_data)
        return view_BVZ(menu, last_data, accept_index=4)

    # ------ Ввод и вывод дополнительных стоимостей ------------------------------------------------------------------
    if "button-accept-cost" in request_form:
        advance_price = dict(list(request_form.items())[:-1])
        for key in advance_price:
            if advance_price[key] == '':
                advance_price[key] = 0
        dbase.update_record("warehouse", 'id', dbase.get_last_record("warehouse")['id'], advance_price)
        last_data = dict(list(dict(dbase.get_last_record("warehouse")).items())[1::])

        if last_data['price_sq_met_found'] != '':
            wf = last_data['width'] + 1
            lf = last_data['length'] + 1
            last_data['dimension_found'] = f"Ш: {wf}m | Д: {lf}m"
            area_found = last_data['area_found'] = wf * lf
            last_data['price_foundation'] = last_data["price_sq_met_found"] * area_found

        if last_data['price_sq_met_sendvich'] >= 0:
            last_data['price_sendvich'] = last_data['price_sq_met_sendvich'] * last_data['S_panel']

        dbase.update_record("warehouse", 'id', dbase.get_last_record("warehouse")['id'], last_data)
        return view_BVZ(menu, last_data, accept_index=5)

    #  -------------------Ввод и вывод финальных расчетов---------------------------------------------
    if "button-accept-percent" in request_form:
        last_data = dict(list(dict(dbase.get_last_record("warehouse")).items())[1::])  # словарь данных

        percent_w = int(request_form["percent_w"]) if request_form["percent_w"] != '' else 0
        percent_f = int(request_form["percent_f"]) if request_form["percent_f"] != '' else 0
        percent_o = int(request_form["percent_o"]) if request_form["percent_o"] != '' else 0
        exch_rate_from = float(request_form['exchange_rates_from'])
        exch_rate_to = float(request_form['exchange_rates_TO'])

        #  ----------- Расчет стоимости склада в ЕВРО для клиента (стоит на локации)------------------------------------
        price_sell_w_sq_m_EU = round(
            (last_data["price_square_meters"] * percent_w / 100) + last_data["price_square_meters"], 2)
        price_sell_w_sq_m_EU = round(price_sell_w_sq_m_EU * exch_rate_to / exch_rate_from, 3)  # курсовая разница
        price_sell_wdb_EU = price_sell_w_sq_m_EU * last_data["area"] + last_data["price_delivery"] + last_data[
            "price_building"]
        price_sell_wdb_sq_m_EU = round(price_sell_wdb_EU / last_data["area"], 2)
        price_sell_wdb_EU = price_sell_wdb_sq_m_EU * last_data["area"]
        profit_wdb_EU = round(price_sell_wdb_EU - last_data["price_project"], 2)

        #  ----------- Расчет стоимости склада в ГРН для клиента (стоит на локации)-------------------------------------
        # блок расчета финальной стоимости склада в ГРН от Протана, без опций, без сендвича на основе цены евро
        price_sell_wdb_sq_m_UA = round(price_sell_wdb_sq_m_EU * exch_rate_to, 2)
        price_sell_wdb_UA = round(price_sell_wdb_sq_m_UA * last_data["area"], 2)
        profit_wdb_UA = profit_wdb_EU * exch_rate_to

        #  ----------- Расчет стоимости СЭНДВИЧ ПАНЕЛЕЙ ----------------------------------------------------------------
        # блок расчета финальной стоимости СЭНДВИЧ ПАНЕЛЕЙ ГРН
        if last_data["price_sendvich"] > 0:
            price_sell_sendvich_EU = (last_data["price_sendvich"] * percent_w / 100) + last_data["price_sendvich"]
            price_sell_sendvich_EU = round(price_sell_sendvich_EU * exch_rate_to / exch_rate_from, 2)
            price_sell_sendvich_UA = ceil(price_sell_sendvich_EU * exch_rate_to)
            profit_sendvich_EU = price_sell_sendvich_EU - last_data["price_sendvich"]
            profit_sendvich_UA = profit_sendvich_EU * exch_rate_from
        else:
            price_sell_sendvich_EU = price_sell_sendvich_UA = profit_sendvich_EU = profit_sendvich_UA = 0

        #  ----------- Расчет стоимости ОСВЕЩЕНИЯ ----------------------------------------------------------------
        # блок расчета финальной стоимости ОСВЕЩЕНИЯ ГРН
        if last_data["price_light"] > 0:
            price_sell_light_EU = (last_data["price_light"] * percent_o / 100) + last_data["price_light"]
            price_sell_light_EU = round(price_sell_light_EU * exch_rate_to / exch_rate_from, 2)
            price_sell_light_UA = ceil(price_sell_light_EU * exch_rate_to)
            profit_light_EU = price_sell_light_EU - last_data["price_light"]
            profit_light_UA = profit_light_EU * exch_rate_from
        else:
            price_sell_light_EU = price_sell_light_UA = profit_light_EU = profit_light_UA = 0

        #  ----------- Расчет стоимости ВОРОТ ----------------------------------------------------------------
        # блок расчета финальной стоимости ВОРОТ ГРН
        if last_data["price_gate"] > 0:
            price_sell_gate_EU = (last_data["price_gate"] * percent_o / 100) + last_data["price_gate"]
            price_sell_gate_EU = round(price_sell_gate_EU * exch_rate_to / exch_rate_from, 2)
            price_sell_gate_UA = ceil(price_sell_gate_EU * exch_rate_to)
            profit_gate_EU = price_sell_gate_EU - last_data["price_gate"]
            profit_gate_UA = profit_gate_EU * exch_rate_from
        else:
            price_sell_gate_EU = price_sell_gate_UA = profit_gate_EU = profit_gate_UA = 0

        #  ----------- Расчет стоимости СТЕЛЛАЖЕЙ-----------------------------------------------------------
        # блок расчета финальной стоимости СТЕЛЛАЖЕЙ ГРН
        if last_data["price_rack"] > 0:
            price_sell_rack_EU = (last_data["price_rack"] * percent_o / 100) + last_data["price_rack"]
            price_sell_rack_EU = round(price_sell_rack_EU * exch_rate_to / exch_rate_from, 2)
            price_sell_rack_UA = round(price_sell_rack_EU * exch_rate_to, 2)
            profit_rack_EU = price_sell_rack_EU - last_data["price_rack"]
            profit_rack_UA = profit_rack_EU * exch_rate_from
        else:
            price_sell_rack_EU = price_sell_rack_UA = profit_rack_EU = profit_rack_UA = 0

        #  ----------- Расчет стоимости ФУНДАМЕНТА ---------------------------------------------------------------------
        # Цена 1м.кв фундамент ЕВРО
        price_f_sq_m_EU = (last_data["price_sq_met_found"] * percent_f / 100) + last_data["price_sq_met_found"]
        price_sell_f_sq_m_EU = round(price_f_sq_m_EU * exch_rate_to / exch_rate_from, 2)
        price_sell_f_sq_m_UA = price_sell_f_sq_m_EU * exch_rate_from
        price_sell_f_UA = price_sell_f_sq_m_UA * last_data["area_found"]
        profit_f_UA = price_sell_f_UA - (last_data["price_foundation"] * exch_rate_from)

        final_sell_wsdbo_EU = price_sell_wdb_EU + price_sell_sendvich_EU + price_sell_light_EU + price_sell_gate_EU
        final_sell_wsdbo_sq_m_EU = round(final_sell_wsdbo_EU / last_data["area"], 2)
        final_sell_wsdbo_EU = final_sell_wsdbo_sq_m_EU * last_data["area"]
        final_profit_wsdbo_EU = profit_wdb_EU + profit_sendvich_EU + profit_light_EU + profit_gate_EU

        final_sell_wsdbo_UA = final_sell_wsdbo_EU * exch_rate_to
        final_sell_wsdbo_sq_m_UA = final_sell_wsdbo_sq_m_EU * exch_rate_to
        final_profit_wsdbo_UA = final_profit_wsdbo_EU * exch_rate_to

        project_sell_UA_1 = final_sell_wsdbo_UA + price_sell_rack_UA + price_sell_f_UA
        project_sell_sq_m_UA = ceil(project_sell_UA_1 / last_data["area"])
        project_sell_UA = project_sell_sq_m_UA * last_data["area"]
        project_profit_UA = final_profit_wsdbo_UA + profit_rack_UA + profit_f_UA + (project_sell_UA - project_sell_UA_1)
        instrument_fund = project_sell_UA / 100
        to_the_risks = last_data['area'] * 100
        on_the_plinth = last_data['area'] * 150
        if to_the_risks < 100000:
            to_the_risks = 100000
        price_delivery = (last_data["price_delivery"] * 0.2) * exch_rate_to
        project_profit_UA = project_profit_UA - instrument_fund - price_delivery - to_the_risks - on_the_plinth

        # ---------- Добавляем в словарь данные -------------------------------------------------------------
        last_data["percent_w"] = int(percent_w)  # Добавляем в словарь Процент склада
        last_data["percent_f"] = int(percent_f)  # Добавляем в словарь Процент фундамента
        last_data["percent_o"] = int(percent_o)  # Добавляем в словарь Процент освещения + стеллажи
        last_data["exchange_rates_from"] = exch_rate_from  # Добавляем в словарь Курс поставщика
        last_data["exchange_rates_TO"] = exch_rate_to  # Добавляем в словарь Курс клиента

        #  Блок с расчетами по стоимости и марже опций и склада отдельно
        last_data["price_sell_warehouse_UA"] = price_sell_wdb_UA
        last_data["price_sell_sendvich_UA"] = price_sell_sendvich_UA
        last_data["price_sell_light_UA"] = price_sell_light_UA
        last_data["price_sell_gate_UA"] = price_sell_gate_UA
        last_data["price_sell_rack_UA"] = price_sell_rack_UA

        last_data["profit_warehouse_UA"] = profit_wdb_UA
        last_data["profit_sendvich_UA"] = profit_sendvich_UA
        last_data["profit_light_UA"] = profit_light_UA
        last_data["profit_gate_UA"] = profit_gate_UA
        last_data["profit_rack_UA"] = profit_rack_UA

        #  Колонка стоимости склада в ЕВРО с опциями (склад, сэндвич, свет, ворота)
        last_data["price_sell_warehouse_option_EU"] = final_sell_wsdbo_EU
        last_data["profit_warehouse_option_EU"] = final_profit_wsdbo_EU
        last_data["cost_square_meters_EU"] = final_sell_wsdbo_sq_m_EU
        last_data["cost_cubic_meters_EU"] = round(price_sell_wdb_EU / last_data["volume"], 2)

        #  Колонка стоимости склада в ГРН с опциями (склад, сэндвич, свет, ворота)
        last_data["price_sell_warehouse_option_UA"] = final_sell_wsdbo_UA
        last_data["profit_warehouse_option_UA"] = final_profit_wsdbo_UA
        last_data["cost_square_meters_UA"] = final_sell_wsdbo_sq_m_UA
        last_data["cost_cubic_meters_UA"] = round(last_data["price_sell_warehouse_option_UA"] / last_data["volume"], 2)

        last_data["cost_foundation"] = price_sell_f_UA
        last_data["cost_sq_met_found"] = price_sell_f_sq_m_UA

        if last_data["price_sell_warehouse_option_EU"] > 0:
            last_data["profit_percent"] = round(
                last_data["profit_warehouse_option_EU"] / last_data["price_sell_warehouse_option_EU"] * 100, 2)
        else:
            last_data["profit_percent"] = 0

        last_data["cost_option"] = profit_f_UA

        last_data['final_cost_sq_m_pr'] = project_sell_sq_m_UA
        last_data['final_price_UA'] = project_sell_UA
        last_data['final_profit_UA'] = project_profit_UA
        if last_data['final_price_UA'] > 0:
            last_data['final_profit_percent'] = round(last_data['final_profit_UA'] / last_data['final_price_UA'] * 100,
                                                      2)
        else:
            last_data['final_profit_percent'] = 0

        string = string_to_ID(last_data['user_email'] + last_data['client'] +
                              last_data['project'] + str(last_data['final_price_UA']) +
                              str(last_data['final_profit_UA']) + str(last_data['final_profit_percent']))
        user_id = current_user.get_id()
        lead_id = dbase.get_record('lead', ('company', dbase.get_last_record('warehouse')['client']),
                                   ('user_email', current_user.get_user_email()))['id']
        last_data['unique_ID'] = str(user_id) + '_' + str(lead_id) + '_' + string
        dbase.update_record("warehouse", 'id', dbase.get_last_record("warehouse")['id'], last_data)

        return view_BVZ(menu, last_data, accept_index=6)

    #  -------Сохраняем полученный результат в постоянную БД-----------------------------------------------
    if "button-save-pricing" in request_form:
        current_calc = dict(dbase.get_last_record("warehouse"))

        title_comment = (f"{current_calc['client']} {current_calc['project']}\n"
                         f"Температура: {current_calc['temperature']}, Стены: {current_calc['wall']} \n")

        body_comment = request_form['input-field-comment-calc']
        dbase.update_record('warehouse', 'id', dbase.get_last_record("warehouse")['id'],
                            {'comments': title_comment + body_comment})

        last_data = dict(list(dict(dbase.get_last_record("warehouse")).items())[1::])

        if dbase.check_records('my_warehouse'):
            warehouse_ID = dbase.get_last_record('warehouse')['id']
            if dbase.get_amount_records('my_warehouse', 'id', warehouse_ID):
                dbase.update_record('my_warehouse', 'id', warehouse_ID, last_data)
                try:
                    dbase.update_record('archive_calculating', 'id', warehouse_ID, last_data)
                except:
                    dbase.save_warehouse('archive_calculating')
            else:
                dbase.save_warehouse('my_warehouse')
                dbase.save_warehouse('archive_calculating')
        else:
            dbase.save_warehouse('my_warehouse')
            dbase.save_warehouse('archive_calculating')

        return view_BVZ(menu, last_data, accept_index=7)

    #  ---------Начинаем новый расчет для данного проекта-------------------------------------------------
    if "button-update-pricing" in request_form:
        request_form = {
            'user_email': current_user.get_user_email(),
            'client': dbase.get_last_record('warehouse')['client'],
            'project': dbase.get_last_record('warehouse')['project'],
            'selected': dbase.get_last_record('warehouse')['selected'],
            'product': dbase.get_last_record('warehouse')['product'],
        }
        dbase.del_records('warehouse', dbase.get_last_record('warehouse')['id'])
        dbase.add_record('warehouse', request_form)

        return view_BVZ(menu, accept_index=1)

    if "button-raw-accept" in list(request_form.values()):
        try:
            del request_form['button_raw']
            warehouse_data = request_form
        except:
            return view_BVZ(menu, accept_index=0)

        dbase.del_records('warehouse')
        dbase.add_record('warehouse', warehouse_data)

        return view_BVZ(menu, warehouse_data, accept_index=7)
