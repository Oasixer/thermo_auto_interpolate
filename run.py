import pandas
import numpy as np

A4_SATURATED_TEMP_CSV = 'a4_saturated_water_temperature.csv'
A5_SATURATED_PRESSURE_CSV = 'a5_saturated_water_pressure.csv'
A6_SUPERHEATED_WATER_CSV = 'a6_superheated_water.csv'

saturated_temperature = pandas.read_csv(A4_SATURATED_TEMP_CSV, header=0, dtype=float, thousands=',')
saturated_pressure = pandas.read_csv(A5_SATURATED_PRESSURE_CSV, header=0, dtype=float, thousands=',')
superheated_water = pandas.read_csv(A6_SUPERHEATED_WATER_CSV, header=0, dtype=float, thousands=',')

VARS = {'P': {'symbol': 'P',
              'table_name': 'a5',
              'table': saturated_pressure,
              'var_desc': 'pressure',
              'units': 'kPa'},
        'T': {'symbol': 'T',
              'table_name': 'a4',
              'table': saturated_temperature,
              'var_desc': 'temperature',
              'units': '°C'},
        'v': {'symbol': 'v',
              'table_name': None,
              'table': None,
              'var_desc': 'specific volume',
              'units': 'm^3/kg',
              'symbol_left': 'v_f',
              'symbol_right': 'v_g'},
        'u': {'symbol': 'u',
              'table_name': None,
              'table': None,
              'var_desc': 'specific internal energy',
              'units': 'kJ/kg',
              'symbol_left':'u_f',
              'symbol_right':'u_g'},
        'h': {'symbol': 'h',
              'table_name': None,
              'table': None,
              'var_desc': 'specific enthalpy',
              'units': 'kJ/kg',
              'symbol_left': 'h_f',
              'symbol_right': 'h_g'},
        's': {'symbol': 's',
              'table_name': None,
              'table': None,
              'var_desc': 'specific entropy',
              'units': 'kJ/(kg*K)',
              'symbol_left':'s_f',
             'symbol_right':'s_g'
              },
         'x': {'symbol': 'x',
              'table_name': None,
              'table': None,
              'var_desc': 'quality',
              'units': ''}
        }

def to_left_edge(var_symbol):
    return var_symbol+'_f'

def to_right_edge(var_symbol):
    return var_symbol+'_g'

def to_edges(var_symbol):
    return [to_left_edge(var_symbol), to_right_edge(var_symbol)]

def is_left_edge(var_symbol):
    return var_symbol.endswith('_f')

def is_right_edge(var_symbol):
    return var_symbol.endswith('_g')
    
def print_row(row, use_mpa=False): # use_mpa is for table a6 which is in MPa
    for var in VARS.values():
        factor = 1 # for unit conversion
        units = var["units"]
        if var['symbol'] == 'P':
            if use_mpa:
                #  factor = 1/1000
                units = 'MPa'

        if 'symbol_left' in var and var['symbol_left'] in (row if type(row) is dict else row.index):
            print(f'{var["symbol_left"]}={row[var["symbol_left"]]}, ',end='')
            if 'symbol_right' in var:
                print(f'{var["symbol_right"]}={row[var["symbol_right"]]} {units}')
        else:
            try:
                print(f'{var["symbol"]}={row[var["symbol"]]} {units}')
            except:
                continue

def is_var_outside_row_vals(indices,
                            var,
                            val
                              ):
    side = ''
    if val < indices[0]:
        side = 'less than'
        edge_val_name = var['symbol_left']
        edge_val = indices[0]
    elif val > indices[1]:
        side = 'greater than'
        edge_val_name = var['symbol_right']
        edge_val = indices[1]
    if side:
        print(f'Value {var["symbol"]}={val} {var["units"]} is {side} {edge_val_name}={edge_val} {var["units"]}')
        return True
    return False
def is_var_outside_table_rows(indices,
                              var,
                              val,
                              table=None,
                              table_name=None
                              ):
    if table is None:
        table = var['table']
        table_name = var['table_name']
    if None in indices:
        print(f'Value {var["symbol"]}={val} ({var["units"]}) is {"below" if indices[0] is None else "above"} the {"lowest" if indices[0] is None else "highest"} value in {table_name}, which is {table[var["symbol"]].min() if indices[0] is None else table[var["symbol"]].max()} {var["units"]}')
        return True
    return False

def find_neighbours(value, df, colname):
    exactmatch = df[df[colname] == value]
    if not exactmatch.empty:
        return exactmatch.index
    else:
        #  print(f'looking for neighbors of {colname}={value} in ')
        #  print(df)
        try:
            lowerneighbour_ind = df[df[colname] < value][colname].idxmax()
        except ValueError:
            # just set lower neighbor to None if we are looking up a value too high
            lowerneighbour_ind = None
        try:
            upperneighbour_ind = df[df[colname] > value][colname].idxmin()
        except ValueError:
            # just set upper neighbor to None if we are looking up a value too high
            #  print('heck')
            upperneighbour_ind = None
        return [lowerneighbour_ind, upperneighbour_ind] 

def interp_a4_a5(eqn_map):
    for name, v in eqn_map.items():
        if name in ['P', 'T']:
            primary_var = VARS[name]
            table = primary_var['table']
            primary_val = v
        else:
            secondary_var = VARS[name]
            secondary_val = v

    print(f'Performing {primary_var["table_name"]} lookup.\n')
    indices = find_neighbours(primary_val, table, primary_var["symbol"])
    if type(indices) is not list: # exact match
        print(f'Found exact match for {primary_var["var_desc"]} {primary_var["symbol"]}={primary_val} {(primary_var["units"])}:')
        row = table.loc[indices[0]]
        print_row(row)
    else:
        if is_var_outside_table_rows(
            indices=indices,
            var=primary_var,
            val=primary_val):
            print(f'min: {superheated_water[primary_var["symbol"]].min()}')

            # Handle P seperately as a lazy way of handling the fact that a4/a5 use kPa and a6 uses MPa
            if primary_var['symbol'] == 'P':
                primary_val_mpa = primary_val / 1000
                if superheated_water[primary_var['symbol']].min() > primary_val_mpa:
                    print(f'Value {primary_var["symbol"]}={primary_val_mpa} (MPa) is below the lowest value in a6, which is {superheated_water.iloc[-1][0]} (MPa).\n\nRestarting program.')
                    return
                elif superheated_water[primary_var['symbol']].max() < primary_val_mpa:
                    print(f'Value {primary_var["symbol"]}={primary_val_mpa} (MPa) is above the highest value in a6, which is {superheated_water.iloc[-1][0]} (MPa).\n\nRestarting program.')
                    return
            else: # anything other than P => no unit conversion needed
                if superheated_water[primary_var['symbol']].min() > primary_val:
                    print(f'Value {primary_var["symbol"]}={primary_val} ({primary_var["units"]}) is below the lowest value in a6, which is {superheated_water.iloc[-1][0]} ({primary_var["units"]}).\n\nRestarting program.')
                    return
                elif superheated_water[primary_var['symbol']].max() < primary_val:
                    print(f'Value {primary_var["symbol"]}={primary_val} ({primary_var["units"]}) is above the highest value in a6, which is {superheated_water.iloc[-1][0]} ({primary_var["units"]}).\n\nRestarting program.')
                    return

                print("DOING SUPERHEATED LOOKUP I GUESS (WIP)")
                a6_lookup(eqn_map)

        row_1 = table.loc[indices[0]]
        row_2 = table.loc[indices[1]]
        #  print(row_1)
        #  print(row_2)
        index = primary_val
        index_1 = table[primary_var["symbol"]][indices[0]]
        index_2 = table[primary_var["symbol"]][indices[1]]
        print(f'Interpolating between {primary_var["symbol"]}={index_1}{primary_var["units"]} and {primary_var["symbol"]}={index_2}{primary_var["units"]}:')
        row = row_1 + (index-index_1)*(row_1-row_2)/(index_1-index_2)
        print_row(row)

    index_left = row[secondary_var['symbol_left']]
    index_right = row[secondary_var['symbol_right']]
    index = secondary_val
    if is_var_outside_row_vals([index_left, index_right], secondary_var, secondary_val):
        if index > index_right:
            print('Lets do superheated woooooooooooooo\n\n')
            if 'P' in eqn_map:
                print(f'Converting P={eqn_map["P"]} KPa to P={eqn_map["P"]/1000} MPa.')
                eqn_map['P'] /= 1000
            a6_lookup(eqn_map)
            return
    left_labels = [i for i in row.index if is_left_edge(i)]
    right_labels = [i for i in row.index if is_right_edge(i)]
    y_1 = np.array(row[left_labels].tolist())
    y_2 = np.array(row[right_labels].tolist())
    vuhs = y_1 + (index-index_left)*(y_2-y_1)/(index_right-index_left)
    v_f = row['v_f']
    v_g = row['v_g']
    v = vuhs[0]
    u = vuhs[1]
    h = vuhs[2]
    s = vuhs[3]
    x = (v - v_f)/(v_g - v_f)
    all_vars = {'P': row['P'], 'T': row['T'], 'v': v, 'u': u, 'h': h, 's': s, 'x': x}
    print("\nFinal values:")
    print_row(all_vars)
    print('')


def get_secondary_row(group, secondary_var, secondary_val, primary_val, primary_var):
    secondary_indices = find_neighbours(secondary_val, group, secondary_var['symbol'])
    if type(secondary_indices) is list: # no exact match. exclude everything that is not the left or right temperature
        index = secondary_val
        #  print(secondary_indices)
        index_left = group[secondary_var['symbol']][secondary_indices[0]]
        #  print(index_left)
        index_right = group[secondary_var['symbol']][secondary_indices[1]]
        print(f'Interpolating between {secondary_var["symbol"]}={index_left}{secondary_var["units"]} and {secondary_var["symbol"]}={index_right}{secondary_var["units"]} for {primary_var["symbol"]}={group[primary_var["symbol"]].tolist()[0]}')
        row_1 = group.loc[secondary_indices[0]]
        row_2 = group.loc[secondary_indices[1]]
        row = row_1 + (index-index_left)*(row_1-row_2)/(index_left-index_right)
        return row
    else:
        row = group.loc[secondary_indices[0]]
        print(f'Found exact match for {secondary_var["symbol"]}={row[secondary_var["symbol"]]} {secondary_var["units"]} for {primary_var["symbol"]}={row[primary_var["symbol"]]}')

def a6_lookup(eqn_map):
    # for now, require P and T
    print('a6 lookup.')
    first = list(eqn_map.keys())[0]
    primary_name = first if first in ['P', 'T'] else list(eqn_map.keys())[1]
    secondary_name = list(eqn_map.keys())[1] if first in ['P', 'T'] else first
    primary_var = VARS[primary_name]
    primary_val = eqn_map[primary_name]
    primary_indices = find_neighbours(primary_val, superheated_water, primary_var['symbol'])

    secondary_var = VARS[secondary_name] # copy so that we can fix the table variable units (lazy hacky solution) but whatever
    secondary_val = eqn_map[secondary_name]

    for var in [primary_var, secondary_var]: #extremely cringe hacky workaround
        if var['symbol'] == 'P':
            var['units'] = 'MPa'

    if None in primary_indices:
        print('Error: your shit is outside the bounds of the superheated table.')

    if type(primary_indices) is list: # no exact match. exclude everything that is not the left or right pressure
        left_rows = superheated_water.loc[superheated_water[primary_var['symbol']] == superheated_water[primary_var['symbol']][primary_indices[0]]]
        right_rows = superheated_water.loc[superheated_water[primary_var['symbol']] == superheated_water[primary_var['symbol']][primary_indices[1]]]

        rows = []
        for group in [left_rows, right_rows]:
            rows.append(get_secondary_row(group=group,
                                          secondary_val=secondary_val,
                                          secondary_var=secondary_var,
                                          primary_var=primary_var,
                                          primary_val=primary_val))
        index = primary_val
        index_1 = rows[0][primary_var['symbol']]
        index_2 = rows[1][primary_var['symbol']]
        row_1 = rows[0]
        row_2 = rows[1]
        row = row_1 + (index-index_1)*(row_1-row_2)/(index_1-index_2)
        print(f'Interpolating between {primary_var["symbol"]}={index_1} {primary_var["units"]} and {primary_var["symbol"]}={index_2} {primary_var["units"]}, using the interpolated value of {secondary_var["symbol"]} ({secondary_var["units"]}) above.')
    else:
        print(f'Found exact match for {primary_var["symbol"]}={primary_val} {primary_var["units"]}')
        group = superheated_water.loc[superheated_water[primary_var['symbol']] == primary_val]
        row = get_secondary_row(group=group,
                                secondary_val=secondary_val,
                                secondary_var=secondary_var,
                                primary_var=primary_var,
                                primary_val=primary_val)

    print('\nFinal result:')
    print_row(row, use_mpa=True)


while(1):
    print("Variables: P(kPa), T(deg. C), v, u, h, s")
    print("Input equations in the form P=100, etc.")
    eqn1 = input("input eqn1: ")
    eqn2 = input("input eqn2: ")
    eqns = [eqn1, eqn2]
    #  eqns = ['v=17.2', 'P=10']
    eqn_map = {}
    for eqn in eqns:
        split = eqn.split('=')
        eqn_map[split[0]] = float(split[1])

    if 'P' in eqn_map and 'T' in eqn_map:
        print('P and T both provided, assuming superheated.')
        print(f'P={eqn_map["P"]}kPa={eqn_map["P"]/1000}MPa')
        eqn_map["P"] /= 1000
        a6_lookup(eqn_map)

    elif 'P' in eqn_map or 'T' in eqn_map:
        interp_a4_a5(eqn_map)

