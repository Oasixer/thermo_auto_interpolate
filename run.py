import pandas
import numpy as np

A4_SATURATED_TEMP_CSV = 'a4_saturated_water_temperature.csv'
A5_SATURATED_PRESSURE_CSV = 'a5_saturated_water_pressure.csv'
A6_SUPERHEATED_WATER_CSV = 'a6_superheated_water.csv'

saturated_temperature = pandas.read_csv(A4_SATURATED_TEMP_CSV, header=0, dtype=float, thousands=',')
saturated_pressure = pandas.read_csv(A5_SATURATED_PRESSURE_CSV, header=0, dtype=float, thousands=',')
superheated_water = pandas.read_csv(A6_SUPERHEATED_WATER_CSV, header=0, dtype=float, thousands=',')

# am i in the vapour dome ie. saturated-x=1, or just 0<=x<=1?
    # in vapour dome
        # if given specific volume v_f or v_g, can use that to find quality
        # if given temp or pressure
        

    # not in the vapour dome
        # going to have a P and T. and either be superheated (a6) or compressed (a7) *** figure out how to know which one
            # if superheated
                # you will have a P, and will have any other one of the variables.
            # if compressed

def to_left_edge(var_name):
    return var_name+'_f'

def to_right_edge(var_name):
    return var_name+'_g'

def to_edges(var_name):
    return [to_left_edge(var_name), to_right_edge(var_name)]

def is_left_edge(var_name):
    return var_name.endswith('_f')

def is_right_edge(var_name):
    return var_name.endswith('_g')

A4_A5_INDICES = ['u', 'v', 'P', 'T']

def find_neighbours(value, df, colname):
    #  print(df.head())
    #  print(df[colname])
    #  print(f'look for {value}')
    exactmatch = df[df[colname] == value]
    if not exactmatch.empty:
        return exactmatch.index
    else:
        lowerneighbour_ind = df[df[colname] < value][colname].idxmax()
        upperneighbour_ind = df[df[colname] > value][colname].idxmin()
        return [lowerneighbour_ind, upperneighbour_ind] 

#  def interpolate_rows(value_pairs):

def interp_a4(temperature, others):
    print('a4 lookup')
    indices = find_neighbours(temperature, saturated_temperature, 'T')
    #  print(indices)
    if type(indices) is not list: # exact match
        row = saturated_temperature.loc[indices[0]]
    else:
        row_1 = saturated_temperature.loc[indices[0]]
        row_2 = saturated_temperature.loc[indices[1]]
        x = temperature
        x_1 = saturated_temperature['T'][indices[0]]
        x_2 = saturated_temperature['T'][indices[1]]
        row = row_1 + (x-x_1)*(row_1-row_2)/(x_1-x_2)

    for k, v in others.items():
        if k in A4_A5_INDICES:
            other_var = k
            other_val = v
            break

    edges = to_edges(other_var)
    x_1 = row[edges[0]]
    x_2 = row[edges[1]]
    x = other_val
    left_labels = [i for i in row.index if is_left_edge(i)]
    right_labels = [i for i in row.index if is_right_edge(i)]
    y_1 = np.array(row[left_labels].tolist())
    y_2 = np.array(row[right_labels].tolist())
    vuhs = y_1 + (x-x_1)*(y_2-y_1)/(x_2-x_1)
    v_f = row['v_f']
    v_g = row['v_g']
    v = vuhs[0]
    x = (v - v_f)/(v_g - v_f)
    all_vars = zip(['P=', 'T=', 'v=','u=','h=','s=', 'x='], [row['P'], row['T']]+vuhs.tolist()+[x])
    for s, val in all_vars:
        print(f'{s}{val}')

def interp_a5(pressure, others):
    print('a5 lookup')
    indices = find_neighbours(pressure, saturated_pressure, 'P')
    #  print(indices)
    if type(indices) is not list: # exact match
        row = saturated_pressure.loc[indices[0]]
    else:
        row_1 = saturated_pressure.loc[indices[0]]
        row_2 = saturated_pressure.loc[indices[1]]
        x = pressure
        x_1 = saturated_pressure['P'][indices[0]]
        x_2 = saturated_pressure['P'][indices[1]]
        row = row_1 + (x-x_1)*(row_1-row_2)/(x_1-x_2)

    for k, v in others.items():
        if k in A4_A5_INDICES:
            other_var = k
            other_val = v
            break

    edges = to_edges(other_var)
    x_1 = row[edges[0]]
    x_2 = row[edges[1]]
    x = other_val
    left_labels = [i for i in row.index if is_left_edge(i)]
    right_labels = [i for i in row.index if is_right_edge(i)]
    y_1 = np.array(row[left_labels].tolist())
    y_2 = np.array(row[right_labels].tolist())
    vuhs = y_1 + (x-x_1)*(y_2-y_1)/(x_2-x_1)
    v_f = row['v_f']
    v_g = row['v_g']
    v = vuhs[0]
    x = (v - v_f)/(v_g - v_f)
    all_vars = zip(['P=', 'T=', 'v=','u=','h=','s=', 'x='], [row['P'], row['T']]+vuhs.tolist()+[x])
    for s, val in all_vars:
        print(f'{s}{val}')

def exclude(var, eqn_map):
    return {k: v for k, v in eqn_map.items() if k != var}

def a6_lookup(eqn_map):
    # for now, require P and T
    
    print('a6 lookup')
    P_indices = find_neighbours(eqn_map['P'], superheated_water, 'P')
    #  print(P_indices)
    if type(P_indices) is list: # no exact match. exclude everything that is not the left or right pressure
        left_rows = superheated_water.loc[superheated_water['P'] == superheated_water['P'][P_indices[0]]]
        right_rows = superheated_water.loc[superheated_water['P'] == superheated_water['P'][P_indices[1]]]
        #  print(left_rows)

        collapsed_rows = []
        for group in [left_rows, right_rows]:
            T_indices = find_neighbours(eqn_map['T'], group, 'T')
            #  print(f'T_indices: {T_indices}')
            if type(T_indices) is list: # no exact match. exclude everything that is not the left or right temperature
                x = eqn_map['T']
                x_1 = group['T'][T_indices[0]]
                x_2 = group['T'][T_indices[1]]
                row_1 = group.loc[T_indices[0]]
                row_2 = group.loc[T_indices[1]]
                row = row_1 + (x-x_1)*(row_1-row_2)/(x_1-x_2)
                #  print(row)
                collapsed_rows.append(row)
            else:
                collapsed_rows.append(group.loc[T_indices[0]])
        x = eqn_map['P']
        x_1 = collapsed_rows[0]['P']
        x_2 = collapsed_rows[1]['P']
        row_1 = collapsed_rows[0]
        row_2 = collapsed_rows[1]
        row = row_1 + (x-x_1)*(row_1-row_2)/(x_1-x_2)
    else:
        group = superheated_water.loc[superheated_water['P'] == eqn_map['P']]
        T_indices = find_neighbours(eqn_map['T'], group, 'T')
        #  print(f'T_indices: {T_indices}')
        if type(T_indices) is list: # no exact match. exclude everything that is not the left or right temperature
            x = eqn_map['T']
            x_1 = group['T'][T_indices[0]]
            x_2 = group['T'][T_indices[1]]
            row_1 = group.loc[T_indices[0]]
            row_2 = group.loc[T_indices[1]]
            row = row_1 + (x-x_1)*(row_1-row_2)/(x_1-x_2)
        else:
            row = group.loc[T_indices[0]]

    all_vars = zip(['P=', 'T=', 'v=','u=','h=','s=', 'x='], row.tolist())
    for s, val in all_vars:
        print(f'{s}{val}')


while(1):
    print("vars: P(kPa), T(deg. C), v, u, h, s")
    eqn1 = input("input eqn1: ")
    eqn2 = input("input eqn2: ")
    eqns = [eqn1, eqn2]
    #  eqns = ['P=900', 'T=250']
    eqn_map = {}
    for eqn in eqns:
        split = eqn.split('=')
        eqn_map[split[0]] = float(split[1])

    if 'P' in eqn_map:
        if 'T' in eqn_map:
            print('P and T both provided, assuming superheated (WIP)')
            print(f'P={eqn_map["P"]}kPa={eqn_map["P"]/1000}MPa')
            eqn_map["P"] /= 1000
            a6_lookup(eqn_map)
            break


        # pressure found
        interp_a5(eqn_map['P'], exclude('P', eqn_map))
        break
    elif 'T' in eqn_map:
        # pressure found
        interp_a4(eqn_map['T'], exclude('T', eqn_map))
        break
        

        #  temperature = int(input('T(deg. C):'))
        #  interp_a4(temperature)


