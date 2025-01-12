'''
IF YOU WANT TO TEST THE SIMULATION: RUN THIS FILE
this file contains 3 part:
    1- Our handle_arrival and handle_departure function
    2- The events that every event function contains one of the functions in part one
    3- The main Simulation: it starts from line 320
'''
from state import *
from Entity import *
from FEL import *
import random
from posibility import *
import matplotlib.pyplot as plt
from plot import *


# Constants
REPLICATIONS = 20
DAYS_TO_SIMULATE = 30  # days
SIMULATION_TIME = DAYS_TO_SIMULATE * 1440  # minutes in a day

# create excel (T/F)
CREATE_EXCEL = False

# Name of departments
class Names:
    ER = 'emergency room'
    PRE = 'pre surgery room'
    LAB = 'laboratory'
    OR = 'operation room'
    WARD = 'ward'
    ICU = 'ICU'
    CCU = 'CCU'
    
# departments to analyze plot from step zero till the given step
analyze_steps = 20000
analyze = {
    # |department name|:|plot queue?| |plot beds?| -> EXAMPLE : Names.ER : [True,False]
        Names.WARD : [True,False]
}



# Creating the departments
emergency_room, pre_Surgery_room, laboratory, operation_room, ward, icu, ccu = get_departments()
departments_in_hospital = [pre_Surgery_room, emergency_room, laboratory, operation_room, ward, icu, ccu]


# Define constants for patient types
class Types:
    EMERGENCY = 'emergency'
    NORMAL = 'normal'
    SIMPLE = 'simple'
    MODERATE = 'moderate'
    COMPLEX = 'complex'

# Define constants for activity durations and thresholds
class Activity:
    PAPERWORK_EMERGENCY = 10  # Minutes
    PAPERWORK_NORMAL = 60 # Minutes
    NORMAL_SURGERY_WAIT = 2880  # Minutes (2 days)
    PREPARE_SURGERY = 10  # Minutes
    ONE_DAY = 1440 # Minutes
    TEST_LAB_MIN = 28 # Minutes
    TEST_LAB_MAX = 32 # Minutes
    
# Define constants for various actions
class Action:
    ADD = 'add' # when patient gets to a bed
    REMOVE = 'remove' # when patient wants to move to another department
    INCREASE = 'increase' 
    DECREASE = 'decrease'
    WAITING = 'waiting' # when patient needs to wait in line
    SUCCESSFUL = 'successful' # when number of beds or queue changes

# Define constants for probabilities and limits
class Probability:
    SINGLE = 0.995 
    GROUP_MIN = 2
    GROUP_MAX = 5
    DEATH_PERCENTAGE = 0.1
    HEART_SURGERY = 0.25
    REDO_SURGERY = 0.01

    # Probabilities for moderate surgery outcomes
    WARD = 0.7
    ICU = 0.2
    CCU = 0.1

    # Available beds during power shortage
    PS_ICU = int(0.8 * icu.bed_limit)
    PS_CCU = int(0.8 * ccu.bed_limit)

    # Available beds without power shortage
    NPS_ICU = icu.bed_limit
    NPS_CCU = ccu.bed_limit

    @staticmethod
    def select_section_for_moderate_surgeries():
        """Randomly selects a hospital section for moderate surgeries."""
        random_number = random.uniform(0, 1)
        if random_number <= Probability.WARD:
            return 'ward'
        elif random_number > (1 - Probability.CCU):
            return 'ccu'
        else:
            return 'icu'

# Handles patient arrivals to the hospital
def handle_arrivals(clock, fel, department: Department, patient: Patient, time, event_name: str):
    queue_status = department.adjust_queue(patient.type, Action.INCREASE, clock)
    bed_status = department.adjust_beds(Action.INCREASE, clock)

    if bed_status == Action.SUCCESSFUL :
        department.update_patient(clock, patient, Action.ADD)
        fel = create_fel(fel, clock, patient, event_name, time)

    elif queue_status == Action.SUCCESSFUL:
        department.update_patient(clock, patient, Action.WAITING)
    

    return department, fel

# Handles patient departures from the hospital
def handle_departures(clock, fel, department: Department, patient: Patient, time, event_name: str):
    queue_status = department.adjust_queue(patient.type, Action.DECREASE, clock)
    department.update_patient(clock, patient, Action.REMOVE)

    if queue_status == Action.SUCCESSFUL:
        next_patient_inline = department.call_first_queue(clock)
        if next_patient_inline is not None:
            fel = create_fel(fel, clock, next_patient_inline, event_name, time)
    else:
        department.adjust_beds(Action.DECREASE, clock)

    return department, fel

# Handles the arrival of a new patient
def arrival(clock, fel, patient: Patient):
    """Handles patient arrival, updates FEL, and returns updated state."""
    global emergency_room, pre_Surgery_room
    patient.set_arrival_time(clock)

    # Create the next patient for arrival
    
    if patient.type == Types.EMERGENCY:
        next_patient = Patient()
        next_patient.type = Types.EMERGENCY
        add_patient_data(patient)
        fel = create_fel(fel, clock, next_patient, 'arrival', exponential(Arrival_rate.EMERGENCY_RATE))
    elif patient.type == Types.NORMAL:
        next_patient = Patient()
        next_patient.type = Types.NORMAL
        add_patient_data(patient)
        fel = create_fel(fel, clock, next_patient, 'arrival', exponential(Arrival_rate.NORMAL_RATE))

    # Handle the current patient's arrival
    if patient.type == Types.EMERGENCY:
        emergency_room, fel = handle_emergency_arrival(clock, fel, patient)
    elif patient.type == Types.NORMAL:
        pre_Surgery_room, fel = handle_arrivals(clock, fel, pre_Surgery_room, patient, Activity.PAPERWORK_NORMAL, 'lab arrival')

    return emergency_room if patient.type == Types.EMERGENCY else pre_Surgery_room, fel

# Process emergency patient arrival
def handle_emergency_arrival(clock, fel, patient: Patient):
    """Processes an emergency patient based on probability."""
    global emergency_room
    if random.uniform(0, 1) < Probability.SINGLE:
        return handle_arrivals(clock, fel, emergency_room, patient, Activity.PAPERWORK_EMERGENCY, 'lab arrival')
    return handle_group_emergency_patients(clock, fel, patient)

# Process group emergency patients
def handle_group_emergency_patients(clock, fel, patient):
    """Handles a group of emergency patients."""
    global emergency_room
    group_size = random.randint(Probability.GROUP_MIN, Probability.GROUP_MAX)
    patient_list = [patient]

    for _ in range(group_size - 1):
        new_patient = Patient()
        add_patient_data(patient)
        new_patient.set_arrival_time(clock)
        new_patient.type = Types.EMERGENCY
        patient_list.append(new_patient)

    for patients in patient_list:
        emergency_room, fel = handle_arrivals(clock, fel, emergency_room, patients, Activity.PAPERWORK_EMERGENCY, 'lab arrival')

    return emergency_room, fel


def lab_arrival(clock, fel, patient: Patient):
    """Handles the lab arrival of a patient."""
    global laboratory
    lab_test_duration = random.uniform(Activity.TEST_LAB_MIN,Activity.TEST_LAB_MAX)
    laboratory, fel = handle_arrivals(clock, fel, laboratory, patient, lab_test_duration, 'lab departure')
    
    return laboratory ,fel

def lab_departure(clock ,fel ,patient: Patient):
    """Handles the departure of a patient from the lab."""
    global laboratory
    # this part handles the proccess of calling the next patient in the line
    lab_test_time = random.uniform(Activity.TEST_LAB_MIN,Activity.TEST_LAB_MAX)
    laboratory, fel = handle_departures(clock, fel, laboratory, patient, lab_test_time, 'lab departure')
        
    # this part handles the departured patient and make him/her ready for surgery
    laboratory.update_patient(clock, patient, Action.REMOVE)
    if patient.type == Types.EMERGENCY:
        fel = create_fel(fel, clock, patient, 'surgery arrival', triangular_distribution_time())
    elif patient.type == Types.NORMAL:
        fel = create_fel(fel, clock, patient, 'surgery arrival', Activity.NORMAL_SURGERY_WAIT)
    
    return laboratory, fel

def surgery_arrival(clock, fel, patient: Patient):
    global operation_room , emergency_room, pre_Surgery_room
    if patient.type == Types.EMERGENCY:
        # patient arrivals to operation room
        operation_room, fel = handle_arrivals(clock, fel, operation_room, patient, Activity.PREPARE_SURGERY, 'do surgery')
        # next emergency patient takes it bed in emergency room
        emergency_room, fel = handle_departures(clock, fel, emergency_room, patient, Activity.PAPERWORK_EMERGENCY, 'lab arrival')
            
    elif patient.type == Types.NORMAL:
        # patient arrivals to operation room
        operation_room, fel = handle_arrivals(clock, fel, operation_room, patient, Activity.PREPARE_SURGERY, 'do surgery')
        # next normal patient takes it bed in pre surgery room
        pre_Surgery_room, fel = handle_departures(clock, fel, pre_Surgery_room, patient, Activity.PAPERWORK_NORMAL, 'lab arrival')
        
    return operation_room, fel
            
def do_surgery(clock, fel, patient: Patient):
    global operation_room
    if patient.surgery == Types.COMPLEX:
        death_var = random.uniform(0,1)
        if death_var <= Probability.DEATH_PERCENTAGE:
            operation_room.update_patient(clock, patient, Action.REMOVE)
        else:
            heart_surgery_var = random.uniform(0,1)
            if heart_surgery_var <= Probability.HEART_SURGERY:
                fel = create_fel(fel, clock, patient, 'ccu arrival', complex_surgery_time())
            else:
                fel = create_fel(fel, clock, patient, 'icu arrival', complex_surgery_time())
    
    elif patient.surgery == Types.MODERATE:
        section = Probability().select_section_for_moderate_surgeries()
        if section == 'ward':
            fel = create_fel(fel, clock, patient, 'ward arrival', moderate_surgery_time())
        elif section == 'icu':
            fel = create_fel(fel, clock, patient, 'icu arrival', moderate_surgery_time())
        elif section == 'ccu':
            fel = create_fel(fel, clock, patient, 'ccu arrival', moderate_surgery_time())
            
    elif patient.surgery == Types.SIMPLE:
        fel = create_fel(fel, clock, patient, 'ward arrival', simple_surgery_time())
    
    operation_room, fel = handle_departures(clock, fel, operation_room, patient, Activity.PREPARE_SURGERY, 'do surgery')
        
    return operation_room, fel

def icu_arrival(clock, fel, patient: Patient):
    global icu
    redo_surgery = random.uniform(0,1)
    if patient.surgery == Types.COMPLEX and redo_surgery <= Probability.REDO_SURGERY:
        patient.redo_surgeries += 1
        patient.type = Types.EMERGENCY
        fel = create_fel(fel, clock, patient, 'surgery arrival', triangular_distribution_time())
        
    patient.type = Types.NORMAL
    
    icu , fel = handle_arrivals(clock, fel, icu, patient, exponential(Icu_and_ccu_stay_parameters.LAMBDA), 'icu departure')
    
    return icu, fel
    
def ccu_arrival(clock, fel, patient: Patient):
    global ccu
    redo_surgery = random.uniform(0,1)
    if patient.surgery == Types.COMPLEX and redo_surgery <= Probability.REDO_SURGERY:
        patient.redo_surgeries += 1
        patient.type = Types.EMERGENCY
        fel = create_fel(fel, clock, patient, 'surgery arrival', triangular_distribution_time())
        
    patient.type = Types.NORMAL
    
    ccu , fel = handle_arrivals(clock, fel, ccu, patient, exponential(Icu_and_ccu_stay_parameters.LAMBDA), 'ccu departure')
    
    return ccu, fel

def ward_arrival(clock, fel, patient: Patient):
    global ward
    ward, fel = handle_arrivals(clock, fel, ward, patient, exponential(Ward_stay_time.LAMBDA), 'ward departure')
    return ward, fel

def icu_departure(clock, fel, patient: Patient):
    global icu
    icu, fel = handle_departures(clock, fel, icu, patient, exponential(Icu_and_ccu_stay_parameters.LAMBDA), 'icu departure')
    
    fel = create_fel(fel, clock, patient, 'ward arrival', exponential(Icu_and_ccu_stay_parameters.LAMBDA))
    
    return icu, fel

def ccu_departure(clock, fel, patient: Patient):
    global ccu
    ccu, fel = handle_departures(clock, fel, ccu, patient, exponential(Icu_and_ccu_stay_parameters.LAMBDA), 'ccu departure')
    
    fel = create_fel(fel, clock, patient, 'ward arrival', exponential(Icu_and_ccu_stay_parameters.LAMBDA))
    
    return ccu, fel

def ward_departure(clock, fel, patient: Patient, stay_time_list):
    global ward
    ward, fel = handle_departures(clock, fel, ward, patient, exponential(Ward_stay_time.LAMBDA), 'ward departure')
    
    patient.set_departure_time(clock)
    stay_time_list = patient.staying_in_system(stay_time_list)
    return ward, fel, stay_time_list

def calculate_queue_full_probability(department: Department, total_simulation_time: float):
    total_full_time = sum(department.time_intervals)
    probability = total_full_time / total_simulation_time
    return probability


def convert_minutes_to_format(minutes):
    # Define the number of minutes in a month, day, and hour
    minutes_in_month = 30 * 24 * 60
    minutes_in_day = 24 * 60
    minutes_in_hour = 60

    # Calculate the number of months, days, hours, and remaining minutes
    months = minutes // minutes_in_month
    minutes %= minutes_in_month
    days = minutes // minutes_in_day
    minutes %= minutes_in_day
    hours = minutes // minutes_in_hour
    minutes %= minutes_in_hour

    # Return the formatted string
    return f"{int(months)}/{int(days)}/{int(hours)}/{round(minutes,2)}"


# Import Statements
import time
from excel import *

# Function Definitions
def get_tracker():
    return {
        'step': [],
        'clock': [],
        'event': [],
        'patient': [],
        'patient type': [],
        'power shortage': [],
        'pre surgery room beds': [],
        'pre surgery room queue': [],
        'emergency room beds': [],
        'emergency room queue': [],
        'laboratory beds': [],
        'laboratory normal queue': [],
        'laboratory priority queue': [],
        'operation room beds': [],
        'operation room normal queue': [],
        'operation room priority queue': [],
        'icu beds': [],
        'icu queue': [],
        'ccu beds': [],
        'ccu queue': [],
        'ward beds': [],
        'ward queue': [],
        'cumulative stats: ER times queue full': [],
        'future event list': [],
    }

def update_tracker(tracker, step, clock, event, patient, amareh, ps_variable, fel):
    tracker['step'].append(step)
    tracker['clock'].append(clock)
    tracker['event'].append(event)
    tracker['patient'].append(patient.id)
    tracker['patient type'].append(patient.type)
    tracker['pre surgery room beds'].append(pre_Surgery_room.beds)
    tracker['pre surgery room queue'].append(pre_Surgery_room.normal_queue)
    tracker['emergency room beds'].append(emergency_room.beds)
    tracker['emergency room queue'].append(emergency_room.priority_queue)
    tracker['laboratory beds'].append(laboratory.beds)
    tracker['laboratory normal queue'].append(laboratory.normal_queue)
    tracker['laboratory priority queue'].append(laboratory.priority_queue)
    tracker['operation room beds'].append(operation_room.beds)
    tracker['operation room normal queue'].append(operation_room.normal_queue)
    tracker['operation room priority queue'].append(operation_room.priority_queue)
    tracker['icu beds'].append(icu.beds)
    tracker['icu queue'].append(icu.normal_queue)
    tracker['ccu beds'].append(ccu.beds)
    tracker['ccu queue'].append(ccu.normal_queue)
    tracker['ward beds'].append(ward.beds)
    tracker['ward queue'].append(ward.normal_queue)
    tracker['cumulative stats: ER times queue full'].append(amareh)
    tracker['power shortage'].append(ps_variable)

    excel_fel = [{'patient': e['patient'].id, 'event': e['event'], 'time': e['time']} for e in fel]
    tracker['future event list'].append(excel_fel)
    return tracker

def update_estimators(estimators, clock, simulation_time, replication, avg_stay, prob_emergency_queue, redo_avg, one_day_wait, departments):
   
    estimators['replication'].append(replication)
    estimators['average staying time is system'].append(avg_stay)
    estimators['probability of full emergency room queue'].append(prob_emergency_queue)
    estimators['pre surgery room max queue'].append(departments[0].max_queue())
    estimators['pre surgery room average queue'].append(departments[0].average_queue())
    estimators['pre surgery room bed efficiency'].append(departments[0].bed_efficiency_and_unused_beds(clock, simulation_time)[0])
    estimators['pre surgery room unused beds'].append(departments[0].bed_efficiency_and_unused_beds(clock, simulation_time)[1])
    estimators['emergency room bed efficiency'].append(departments[1].bed_efficiency_and_unused_beds(clock, simulation_time)[0])
    estimators['emergency room unused beds'].append(departments[1].bed_efficiency_and_unused_beds(clock, simulation_time)[1])
    estimators['laboratory max queue'].append(departments[2].max_queue())
    estimators['laboratory average queue'].append(departments[2].average_queue())
    estimators['laboratory bed efficiency'].append(departments[2].bed_efficiency_and_unused_beds(clock, simulation_time)[0])
    estimators['laboratory unused beds'].append(departments[2].bed_efficiency_and_unused_beds(clock, simulation_time)[1])
    estimators['operation room max queue'].append(departments[3].max_queue())
    estimators['operation room average queue'].append(departments[3].average_queue())
    estimators['operation room bed efficiency'].append(departments[3].bed_efficiency_and_unused_beds(clock, simulation_time)[0])
    estimators['operation room unused beds'].append(departments[3].bed_efficiency_and_unused_beds(clock, simulation_time)[1])
    estimators['icu max queue'].append(departments[5].max_queue())
    estimators['icu average queue'].append(departments[5].average_queue())
    estimators['icu bed efficiency'].append(departments[5].bed_efficiency_and_unused_beds(clock, simulation_time)[0])
    estimators['icu unused beds'].append(departments[5].bed_efficiency_and_unused_beds(clock, simulation_time)[1])
    estimators['ccu max queue'].append(departments[6].max_queue())
    estimators['ccu average queue'].append(departments[6].average_queue())
    estimators['ccu bed efficiency'].append(departments[6].bed_efficiency_and_unused_beds(clock, simulation_time)[0])
    estimators['ccu unused beds'].append(departments[6].bed_efficiency_and_unused_beds(clock, simulation_time)[1])
    estimators['ward bed efficiency'].append(departments[4].bed_efficiency_and_unused_beds(clock, simulation_time)[0])
    estimators['ward unused beds'].append(departments[4].bed_efficiency_and_unused_beds(clock, simulation_time)[1])
    estimators['average redo surgeries'].append(redo_avg)
    estimators['percentage of normal patients waiting more than one day in operation room queue'].append(one_day_wait)
    return estimators

# Main Simulation Loop
a = time.time()

estimators = {
    'replication': [],
    'average staying time is system': [],
    'probability of full emergency room queue': [],
    'emergency room bed efficiency': [],
    'emergency room unused beds': [],
    'pre surgery room max queue': [],
    'pre surgery room average queue': [],
    'pre surgery room bed efficiency': [],
    'pre surgery room unused beds': [],
    'laboratory max queue': [],
    'laboratory average queue': [],
    'laboratory bed efficiency': [],
    'laboratory unused beds': [],
    'operation room max queue': [],
    'operation room average queue': [],
    'operation room bed efficiency': [],
    'operation room unused beds': [],
    'average redo surgeries': [],
    'icu max queue': [],
    'icu average queue': [],
    'icu bed efficiency': [],
    'icu unused beds': [],
    'ccu max queue': [],
    'ccu average queue': [],
    'ccu bed efficiency': [],
    'ccu unused beds': [],
    'ward bed efficiency': [],
    'ward unused beds': [],
    'percentage of normal patients waiting more than one day in operation room queue': []
}

event_handlers = {
    'arrival': arrival,
    'lab arrival': lab_arrival,
    'lab departure': lab_departure,
    'surgery arrival': surgery_arrival,
    'do surgery': do_surgery,
    'icu arrival': icu_arrival,
    'ccu arrival': ccu_arrival,
    'ward arrival': ward_arrival,
    'icu departure': icu_departure,
    'ccu departure': ccu_departure,
    'ward departure': ward_departure,
}

big_data = {'queue':{},'beds':{}}
for dep in departments_in_hospital:
    if dep.name in analyze:
        if analyze[dep.name][0] == True:
            big_data['queue'][dep.name] = list()
        if analyze[dep.name][1] == True:
            big_data['beds'][dep.name] = list()

for rep in range(REPLICATIONS):
    print(f"\nReplication {rep + 1}")
    print('-' * 40)

    clock = 0
    step = 1
    time_to_stay_in_hospital = []
    waiting_time_or_normal = []

    # reseting the id counter for simulation start
    Patient.reset()
    # Creating 1 normal and 1 emergency patient
    patient1, patient2 = Patient(), Patient()
    patient1.type, patient2.type = Types.EMERGENCY, Types.NORMAL
    add_patient_data(patient1)
    add_patient_data(patient2)

    # starting FEL
    fel = [{'patient': patient1, 'event': 'arrival', 'time': clock},
           {'patient': patient2, 'event': 'arrival', 'time': clock}]

    # Selecting a random day for power shortage
    month = starting_month = 0
    day_of_power_shortage = random.randint(0, 29)
    printed = False

    # Creating a tracker for simulation
    tracker = get_tracker()
    
    while clock < SIMULATION_TIME:
        # Extracting the first FEL(FEL items are sorted by time)
        patient, event, clock = fel[0]['patient'], fel[0]['event'], fel[0]['time']
        # Convert clock into a format of (MM/DD/HH/MIN) for easier understanding
        formated = convert_minutes_to_format(clock).split('/')

        if int(formated[1]) == day_of_power_shortage:
            if not printed: # starting power shortage
                print(f"We have power shortage in month {month} on day {formated[1]}")
                printed = True
            # if the patients in ICU & CCU are more than the power shortage limit their beds covers power temporary
            icu.bed_limit = min(icu.beds, Probability.PS_ICU)
            ccu.bed_limit = min(ccu.beds, Probability.PS_CCU)
        else:
            icu.bed_limit, ccu.bed_limit = Probability.NPS_ICU, Probability.NPS_CCU
            printed = False

        # Creating the next power shortage for the next month
        if int(formated[0]) > month:
            month += 1
            day_of_power_shortage = random.randint(0, 29)

        # running events
        if event == 'ward departure':
            department_reported, fel, time_to_stay_in_hospital = ward_departure(clock, fel, patient, time_to_stay_in_hospital)
        else: 
            department_reported, fel = event_handlers[event](clock, fel, patient)
            
        for dep in departments_in_hospital:
            dep.update_database(step)
            
        'this is for debug(simply ignore)'
        #print(str(convert_minutes_to_format(clock)).ljust(10) + '\t' + str(event).ljust(10) + '\t' + str(department_reported.report()).ljust(10) + 
        #        '\t' + str(patient.id).ljust(10) + '\t' + str(patient.type).ljust(10) + '\t' + str(patient.surgery).ljust(10))
        
        # Clearing the the first FEL(also sorting again by time)
        fel = remove_fel(fel)
        tracker = update_tracker(tracker, step, clock, event, patient, sum(emergency_room.time_intervals), printed, fel)
        step += 1
        
    # End of simulation
    if CREATE_EXCEL == True:
        xlsx_writer(tracker, f'replication {rep+1}')
    
    # calculating metrics
    
    for deps in big_data['queue']:
        for d in departments_in_hospital:
            if d.name == deps:
                big_data['queue'][deps].append(dict(list(d.queue_step.items())[:analyze_steps]))
    for deps in big_data['beds']:
        for d in departments_in_hospital:
            if d.name == deps:
                big_data['beds'][deps].append(dict(list(d.bed_step.items())[:analyze_steps]))
    
    for dep in departments_in_hospital:
        if dep.name == operation_room.name:
            for pat in dep.data['waiting time']:
                if pat.type == Types.EMERGENCY:
                    # calculate the number of patients that have waited more than one day in operation room queue
                    waiting_time_or_normal.append(dep.data['waiting time'][pat])
        
    # calculate average time of spent in system   
    avg_stay = sum(time_to_stay_in_hospital) / len(time_to_stay_in_hospital)
    
    # calculate average redo surgeries that patients with complex surgeries had
    l = []
    for i in data_patients['redo surgeries']:
            if i.redo_surgeries > 0:
                l.append(i.redo_surgeries)
    redo_avg = sum(i.redo_surgeries for i in data_patients['redo surgeries'] if i.redo_surgeries > 0) / len(l) if len(l)!=0 else 0
    
    # calculate probability of emergency room queue reached the limit
    prob_emergency_queue_full = calculate_queue_full_probability(emergency_room, SIMULATION_TIME)

    one_day_wait = sum(waiting_time_or_normal) / len(waiting_time_or_normal) if len(waiting_time_or_normal)!=0 else 0
    
    # Saving collected metrics
    estimators = update_estimators(estimators, clock, SIMULATION_TIME, rep + 1, avg_stay, prob_emergency_queue_full, redo_avg, one_day_wait, departments_in_hospital)

    # reseting the departments for new replication
    emergency_room, pre_Surgery_room, laboratory, operation_room, ward, icu, ccu = get_departments()
    departments_in_hospital = [pre_Surgery_room, emergency_room, laboratory, operation_room, ward, icu, ccu]

    
# end of replications
# calculating mean and confidence intervals
for key in estimators:
    if key=='replication':
        estimators[key].append('average')
        estimators[key].append('confidence interval')
    else:
        mean, confidence_interval = mean_and_confidence_interval(estimators[key])
        estimators[key].append(mean)
        estimators[key].append(f'{confidence_interval}')
 
# writing the excel file for metrics
if CREATE_EXCEL == True:
    xlsx_writer(estimators, 'metrics')

for dep in big_data['queue']:
    create_queue_plot(dep, big_data['queue'][dep])
for dep in big_data['beds']:
    create_bed_plot(dep, big_data['beds'][dep])

b = time.time()
# calculating time of simluation
print('Total simulation time:', b - a)
