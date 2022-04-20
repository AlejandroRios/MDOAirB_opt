"""
MDOAirB

Description:
    - This module computes the required and optimum mission altitude

Reference:
    -

TODO's:
    -

| Authors: Alejandro Rios
| Email: aarc.88@gmail.com
| Creation: January 2021
| Last modification: July 2021
| Language  : Python 3.8 or >
| Aeronautical Institute of Technology - Airbus Brazil

"""

# =============================================================================
# IMPORTS
# =============================================================================
from framework.Attributes.Atmosphere.atmosphere_ISA_deviation import atmosphere_ISA_deviation
from framework.Attributes.Airspeed.airspeed import V_cas_to_mach, mach_to_V_cas, crossover_altitude

from framework.Performance.Engine.engine_performance import turbofan

from framework.Performance.Analysis.climb_to_altitude import rate_of_climb_calculation
from framework.Performance.Analysis.buffet_altitude_constraint import buffet_altitude
from joblib import dump, load
# =============================================================================
# CLASSES
# =============================================================================

# =============================================================================
# FUNCTIONS
# =============================================================================
global GRAVITY
GRAVITY = 9.80665


def maximum_altitude(vehicle, initial_altitude, limit_altitude, mass,
                     climb_V_cas, mach_climb, delta_ISA):
    """
    Description:
        - This function calculates the maximum altitude
    Inputs:
        - vehicle - dictionary containing aircraft parameters
        - initial_altitude
        - limit_altitude
        - mass
        - climb_V_cas - calibrated airspeed during climb [kt]
        - mach - mach number_climb
        - delta_ISA - ISA temperature deviation [deg C]
    Outputs:
        - final_altitude
        - rate_of_climb - aircraft rate of climb [ft/min]
    """
    aircraft = vehicle['aircraft']
    performance = vehicle['performance']
    engine = vehicle['engine']

    if engine['type'] == 1:
        scaler_F = load('Performance/Engine/Turboprop/ANN_skl_force/scaler_force_PW120_in.bin') 
        nn_unit_F = load('Performance/Engine/Turboprop/ANN_skl_force/nn_force_PW120.joblib')

        scaler_FC = load('Performance/Engine/Turboprop/ANN_skl_ff/scaler_ff_PW120_in.bin') 
        nn_unit_FC = load('Performance/Engine/Turboprop/ANN_skl_ff/nn_ff_PW120.joblib')  

    transition_altitude = crossover_altitude(
        mach_climb, climb_V_cas, delta_ISA)
    altitude_step = 100
    residual_rate_of_climb = performance['residual_rate_of_climb']

    time = 0
    distance = 0
    fuel = 0
    rate_of_climb = 9999

    # Climb to 10000 ft with 250KCAS
    initial_altitude = initial_altitude + 1500  # 1500 [ft]
    altitude = initial_altitude
    final_altitude = 10000
    throttle_position = 0.95

    V_cas = 250

    while (rate_of_climb > residual_rate_of_climb and altitude < final_altitude):

        mach = V_cas_to_mach(V_cas, altitude, delta_ISA)

        if engine['type'] == 0:
            thrust_force, fuel_flow , vehicle = turbofan(
                altitude, mach, throttle_position, vehicle)  # force [N], fuel flow [kg/hr]
        else:
            thrust_force = nn_unit_F.predict(scaler_F.transform([(altitude, mach, throttle_position)]))
            fuel_flow = nn_unit_FC.predict(scaler_FC.transform([(altitude, mach, throttle_position)]))

        thrust_to_weight = aircraft['number_of_engines'] * \
            thrust_force/(mass*GRAVITY)

        rate_of_climb, V_tas, _ = rate_of_climb_calculation(
            thrust_to_weight, altitude, delta_ISA, mach, mass, vehicle)

        delta_time = altitude_step/rate_of_climb
        time = time + delta_time
        distance = distance + (V_tas/60)*delta_time
        delta_fuel = (fuel_flow/60)*delta_time
        fuel = fuel+delta_fuel
        mass = mass-delta_fuel
        altitude = altitude + altitude_step

    # Climb to transition altitude at constat CAS

    delta_altitude = 0
    initial_altitude = 10000 + delta_altitude
    altitude = initial_altitude
    final_altitude = transition_altitude

    while (rate_of_climb > residual_rate_of_climb and altitude <= final_altitude):

        mach = V_cas_to_mach(V_cas, altitude, delta_ISA)

        if engine['type'] == 0:
            thrust_force, fuel_flow , vehicle = turbofan(
                altitude, mach, throttle_position, vehicle)  # force [N], fuel flow [kg/hr]
        else:
            thrust_force = nn_unit_F.predict(scaler_F.transform([(altitude, mach, throttle_position)]))
            fuel_flow = nn_unit_FC.predict(scaler_FC.transform([(altitude, mach, throttle_position)]))

        thrust_to_weight = aircraft['number_of_engines'] * \
            thrust_force/(mass*GRAVITY)

        rate_of_climb, V_tas, _ = rate_of_climb_calculation(
            thrust_to_weight, altitude, delta_ISA, mach, mass, vehicle)

        delta_time = altitude_step/rate_of_climb
        time = time + delta_time
        distance = distance + (V_tas/60)*delta_time
        delta_fuel = (fuel_flow/60)*delta_time
        fuel = fuel+delta_fuel
        mass = mass-delta_fuel
        altitude = altitude + altitude_step

    # Climb to transition altitude at constant mach
    final_altitude = limit_altitude
    mach = mach_climb

    buffet_altitude_limit = buffet_altitude(
        vehicle, mass, altitude, limit_altitude, mach_climb)

    while (rate_of_climb > residual_rate_of_climb and altitude <= final_altitude):

        V_cas = mach_to_V_cas(mach, altitude, delta_ISA)

        if engine['type'] == 0:
            thrust_force, fuel_flow , vehicle = turbofan(
                altitude, mach, throttle_position, vehicle)  # force [N], fuel flow [kg/hr]
        else:
            thrust_force = nn_unit_F.predict(scaler_F.transform([(altitude, mach, throttle_position)]))
            fuel_flow = nn_unit_FC.predict(scaler_FC.transform([(altitude, mach, throttle_position)]))

        thrust_to_weight = aircraft['number_of_engines'] * \
            thrust_force/(mass*GRAVITY)

        rate_of_climb, V_tas, _ = rate_of_climb_calculation(
            thrust_to_weight, altitude, delta_ISA, mach, mass, vehicle)

        delta_time = altitude_step/rate_of_climb
        time = time + delta_time
        distance = distance + (V_tas/60)*delta_time
        delta_fuel = (fuel_flow/60)*delta_time
        fuel = fuel+delta_fuel
        mass = mass-delta_fuel
        altitude = altitude + altitude_step

    final_altitude = altitude - altitude_step

    if buffet_altitude_limit < final_altitude:
        final_altitude = buffet_altitude_limit

    return float(final_altitude), float(rate_of_climb)


def optimum_altitude(vehicle, initial_altitude, limit_altitude, mass,
                     climb_V_cas, mach_climb, delta_ISA):
    """
    Description:
        - This function calculates the optimum altitude
    Inputs:
        - vehicle - dictionary containing aircraft parameters
        - initial_altitude - [ft]
        - limit_altitude - maximum altitude [ft]
        - mass - aircraft mass [kg]
        - climb_V_cas - calibrated airspeed during climb [kt]
        - mach - mach number_climb
        - delta_ISA - ISA temperature deviation [deg C]
    Outputs:
        - optimum_altitude - [ft]
        - rate_of_climb - aircraft rate of climb [ft/min]
        - optimum_specific_rate - [kt/(kg/hr)]
    """
    aircraft = vehicle['aircraft']
    performance = vehicle['performance']
    engine = vehicle['engine']

    if engine['type'] == 1:
        scaler_F = load('Performance/Engine/Turboprop/ANN_skl_force/scaler_force_PW120_in.bin') 
        nn_unit_F = load('Performance/Engine/Turboprop/ANN_skl_force/nn_force_PW120.joblib')

        scaler_FC = load('Performance/Engine/Turboprop/ANN_skl_ff/scaler_ff_PW120_in.bin') 
        nn_unit_FC = load('Performance/Engine/Turboprop/ANN_skl_ff/nn_ff_PW120.joblib')   

    transition_altitude = crossover_altitude(
        mach_climb, climb_V_cas, delta_ISA)
    altitude_step = 100
    residual_rate_of_climb = performance['residual_rate_of_climb']

    time = 0
    distance = 0
    fuel = 0
    rate_of_climb = 9999

    # Climb to 10000 ft with 250KCAS
    initial_altitude = initial_altitude + 1500  # 1500 [ft]
    altitude = initial_altitude
    final_altitude = 10000
    throttle_position = 0.95

    optimum_specific_rate = 0

    V_cas = 250

    while (rate_of_climb > residual_rate_of_climb and altitude < final_altitude):

        # print(rate_of_climb)
        # print(altitude)
        mach = V_cas_to_mach(V_cas, altitude, delta_ISA)

        if engine['type'] == 0:
            thrust_force, fuel_flow , vehicle = turbofan(
                altitude, mach, throttle_position, vehicle)  # force [N], fuel flow [kg/hr]
        else:
            thrust_force = nn_unit_F.predict(scaler_F.transform([(altitude, mach, throttle_position)]))
            fuel_flow = nn_unit_FC.predict(scaler_FC.transform([(altitude, mach, throttle_position)]))

        thrust_to_weight = aircraft['number_of_engines'] * \
            thrust_force/(mass*GRAVITY)

        rate_of_climb, V_tas, _ = rate_of_climb_calculation(
            thrust_to_weight, altitude, delta_ISA, mach, mass, vehicle)

        delta_time = altitude_step/rate_of_climb
        time = time + delta_time
        distance = distance + (V_tas/60)*delta_time
        delta_fuel = (fuel_flow/60)*delta_time
        fuel = fuel+delta_fuel
        mass = mass-delta_fuel
        altitude = altitude + altitude_step

        specific_rate = V_tas/fuel_flow
        if specific_rate > optimum_specific_rate:
            optimum_specific_rate = specific_rate
            optimum_altitude = altitude

    # Climb to transition altitude at constat CAS

    delta_altitude = 0
    initial_altitude = 10000 + delta_altitude
    altitude = initial_altitude
    final_altitude = transition_altitude

    while (rate_of_climb > residual_rate_of_climb and altitude <= final_altitude):
        # print(rate_of_climb)
        # print(altitude)
        mach = V_cas_to_mach(V_cas, altitude, delta_ISA)
    
        if engine['type'] == 0:
            thrust_force, fuel_flow , vehicle = turbofan(
                altitude, mach, throttle_position, vehicle)  # force [N], fuel flow [kg/hr]
        else:
            thrust_force = nn_unit_F.predict(scaler_F.transform([(altitude, mach, throttle_position)]))
            fuel_flow = nn_unit_FC.predict(scaler_FC.transform([(altitude, mach, throttle_position)]))

        thrust_to_weight = aircraft['number_of_engines'] * \
            thrust_force/(mass*GRAVITY)

        rate_of_climb, V_tas, _ = rate_of_climb_calculation(
            thrust_to_weight, altitude, delta_ISA, mach, mass, vehicle)

        delta_time = altitude_step/rate_of_climb
        time = time + delta_time
        distance = distance + (V_tas/60)*delta_time
        delta_fuel = (fuel_flow/60)*delta_time
        fuel = fuel+delta_fuel
        mass = mass-delta_fuel
        altitude = altitude + altitude_step

        specific_rate = V_tas/fuel_flow
        if specific_rate > optimum_specific_rate:
            optimum_specific_rate = specific_rate
            optimum_altitude = altitude

    # Climb to transition altitude at constant mach
    final_altitude = limit_altitude
    mach = mach_climb

    buffet_altitude_limit = buffet_altitude(
        vehicle, mass, altitude, limit_altitude, mach_climb)

    while (rate_of_climb > residual_rate_of_climb and altitude <= final_altitude):
        # print(rate_of_climb)
        # print(altitude)

        V_cas = mach_to_V_cas(mach, altitude, delta_ISA)

        if engine['type'] == 0:
            thrust_force, fuel_flow , vehicle = turbofan(
                altitude, mach, throttle_position, vehicle)  # force [N], fuel flow [kg/hr]
        else:
            thrust_force = nn_unit_F.predict(scaler_F.transform([(altitude, mach, throttle_position)]))
            fuel_flow = nn_unit_FC.predict(scaler_FC.transform([(altitude, mach, throttle_position)]))

        thrust_to_weight = aircraft['number_of_engines'] * \
            thrust_force/(mass*GRAVITY)

        rate_of_climb, V_tas, _ = rate_of_climb_calculation(
            thrust_to_weight, altitude, delta_ISA, mach, mass, vehicle)

        delta_time = altitude_step/rate_of_climb
        time = time + delta_time
        distance = distance + (V_tas/60)*delta_time
        delta_fuel = (fuel_flow/60)*delta_time
        fuel = fuel+delta_fuel
        mass = mass-delta_fuel
        altitude = altitude + altitude_step

        specific_rate = V_tas/fuel_flow
        if specific_rate > optimum_specific_rate:
            optimum_specific_rate = specific_rate
            optimum_altitude = altitude

    final_altitude = altitude - altitude_step

    if buffet_altitude_limit < final_altitude:
        final_altitude = buffet_altitude_limit

    optimum_altitude = final_altitude
    return float(optimum_altitude), float(rate_of_climb), float(optimum_specific_rate)


# =============================================================================
# MAIN
# =============================================================================

# =============================================================================
# TEST
# =============================================================================

# initial_altitude = 0
# limit_altitude = 41000
# mass = 43112 # [kg]
# climb_V_cas = 280
# mach_climb = 0.78
# delta_ISA = 0

# altitude, roc =  maximum_altitude(initial_altitude, limit_altitude, mass,
#     climb_V_cas, mach_climb, delta_ISA)

# print(altitude, roc)
