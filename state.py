'''
This file handles every created departments in the hospital simulation

DEPARTMENT : 
    FUNCTIONALITIES:        1) stores bed and queue information
        
                            2) ajusts the number used beds and queue length with a dynamic system for increasing or decreasing beds and 
                                queue by it given initial state. examples: department queue has limit, there should a priority line, etc.
                                
                            3) stores the data of the patients with 3 different values:
                                data['patinets'] = stores the Patient and its time when he/she gets into bed
                                data['waiting list] = stores the list of patients that are in line and sorted by time
                                data['waiting times'] = stores the patinets wainting time in the queue
                            
                            4) calculates metrics:
                                    a) max queue that the department had during the simulation
                                    b) average queue the department had during simulation
                                    c) bed efficiency : time that beds are busy / simulation time

BED : 
    FUNCTIONALITIES:        1) it has a ONE-TO-MANY relationship with the Department class

                            2) stores every bed starting time and ending time for calculating the metrics
'''
class Bed:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.occupied = 0
        self.stay_time = []
     
    def calculate_stay_time(self):
        time_diff = self.end_time - self.start_time
        self.stay_time.append(time_diff)
    
class Department:
    def __init__(self,
                 name: str,
                 beds: int,
                 bed_limit: int,
                 normal_queue: int,
                 priority_queue: int,
                 queue_limit: int):
        
        self.name           = name
        self.beds           = beds # Number of beds that are in use
        self.bed_limit      = bed_limit
        self.normal_queue   = normal_queue
        self.priority_queue = priority_queue
        self.queue_limit    = queue_limit
        
        # databases: saves queue and bed in each time of the simulation
        self.bed_database = dict()
        self.queue_step = dict()
        self.bed_step = dict()
        
        for i in range(self.bed_limit):
            self.bed_database[i+1] = Bed()
            
        self.data = dict()
        self.data['patients'] = dict()      # { 'patient' : service time begins for the patient}
        self.data['waiting list'] = {'priority': dict(), 'normal': dict()}  # { 'patient' : arrival time of the patient }
        self.data['waiting time'] = dict() # { 'patient' : waiting times in the queue }
        
        self.last_full_time = None
        self.time_intervals = []
         
    def report(self):
        return {
            'name' : self.name,
            'normal queue length' : self.normal_queue,
            'pr queue' : self.priority_queue,
            'beds' : self.beds
            }
        
    # detemines if the patient should wait in line or get a bed or he should get out of its bed
    def update_patient(self, clock, patient, action: str):
        if action == 'add':
            self.data['patients'][patient] = {'time service begins': clock}
        elif action == 'remove':
            if patient in self.data['patients']:
                del self.data['patients'][patient]
        elif action == 'waiting':
            if patient.type == 'emergency':
                self.data['waiting list']['priority'][patient] = clock
                self.data['waiting list']['priority'] = dict(
                sorted(self.data['waiting list']['priority'].items(), key=lambda item: item[1])
                )
            elif patient.type == 'normal':
                self.data['waiting list']['normal'][patient] = clock
                self.data['waiting list']['normal'] = dict(
                sorted(self.data['waiting list']['normal'].items(), key=lambda item: item[1])
                )
        
    # calling the first paitent that waited in the queue
    def call_first_queue(self, clock):
        if len(self.data['waiting list']['priority']) > 0:
            # Get and remove the first key from the priority dictionary
            next_patient = next(iter(self.data['waiting list']['priority']))
            
            self.data['waiting time'][next_patient] = clock - self.data['waiting list']['priority'][next_patient]
            # Remove the key from the dictionary
            del self.data['waiting list']['priority'][next_patient]
            return next_patient
        elif len(self.data['waiting list']['normal']) > 0:
            # Get and remove the first key from the normal dictionary
            next_patient = next(iter(self.data['waiting list']['normal']), None)  # Using None as a default if empty
            
            self.data['waiting time'][next_patient] = clock - self.data['waiting list']['normal'][next_patient]
            
            if next_patient is not None:  # Check if there was a key to remove
                del self.data['waiting list']['normal'][next_patient]
            return next_patient

    def update_database(self, step):
        self.queue_step[step] = ((self.priority_queue if self.priority_queue is not None else 0) + (self.normal_queue if self.normal_queue is not None else 0))
        self.bed_step[step] = self.beds
        

    def adjust_queue(self, patient_type: str, action: str, clock):
        '''Adjusts the queue length based on patient type and action (increase/decrease).'''
        if patient_type == 'emergency':
            if self.priority_queue is not None:
                if action == 'increase':
                    # Check if we can increase the priority queue
                    if self.priority_queue > 0 or self.beds == self.bed_limit:
                        if ((self.queue_limit is not None) and (self.priority_queue +(self.normal_queue if self.normal_queue else 0) < self.queue_limit)) or (self.queue_limit is None):
                            self.priority_queue += 1
                            if (self.queue_limit is not None) and ((self.normal_queue if self.normal_queue else 0) + self.priority_queue) == self.queue_limit:
                                self.last_full_time = clock
                            return 'successful'
                        else:
                            return 'failed'
                    
        if patient_type == 'normal':
            if self.normal_queue is not None:
                if action == 'increase':
                    if (self.priority_queue and self.priority_queue > 0) or self.beds == self.bed_limit or self.normal_queue > 0:
                        if ((self.queue_limit is not None) and (self.normal_queue +(self.priority_queue if self.priority_queue else 0) < self.queue_limit)) or (self.queue_limit is None):
                            self.normal_queue += 1
                            # if the queue reached the queue limit save the time
                            if (self.queue_limit is not None) and ((self.priority_queue if self.priority_queue else 0) + self.normal_queue) == self.queue_limit:
                                self.last_full_time = clock
                            return 'successful'
                        else:
                            return 'failed'

        if action == 'decrease':
            if self.priority_queue and self.priority_queue > 0:
                if (self.queue_limit is not None) and ((self.normal_queue if self.normal_queue else 0) + self.priority_queue) == self.queue_limit:
                    diff_time = clock - self.last_full_time
                    self.time_intervals.append(diff_time)
                self.priority_queue -= 1
                return 'successful'
            if self.normal_queue and self.normal_queue > 0:
                if (self.queue_limit is not None) and ((self.priority_queue if self.priority_queue else 0) + self.normal_queue) == self.queue_limit:
                    diff_time = clock - self.last_full_time
                    self.time_intervals.append(diff_time)
                self.normal_queue -= 1
                return 'successful'
            
                    
    def adjust_beds(self, action: str, clock):
        '''Adjusts the number of beds based on action (increase/decrease).'''
        if action == 'increase':
            if self.beds < self.bed_limit:
                self.beds += 1
                # assigning a bed for patient
                for id in self.bed_database:
                    bed = self.bed_database[id]
                    if bed.occupied == 0:
                        bed.occupied = 1
                        bed.start_time = clock
                        break
                return 'successful'
            
        elif action == 'decrease' and self.beds > 0:
            self.beds -= 1
            for id in self.bed_database:
                    bed = self.bed_database[id]
                    if bed.occupied == 1:
                        bed.occupied = 0
                        bed.end_time = clock
                        bed.calculate_stay_time()
                        break
            return 'successful'
        
    def max_queue(self):
        return max(self.queue_step.values())
    
    def average_queue(self):
        return sum(self.queue_step.values())/len(self.queue_step.values())
    
    # retuns: [times that (used)beds are busy / simulation time] & [unused beds]
    def bed_efficiency_and_unused_beds(self, clock, simulation_time):
        unused_bed_counter = 0
        bed_occupation_percentage = dict()
        for id in self.bed_database:
            bed = self.bed_database[id]
            if bed.start_time and bed.end_time == None and bed.occupied == 1:
                bed.end_time = clock
                bed.calculate_stay_time()
            bed_occupation_percentage[id] = sum(bed.stay_time)/simulation_time
            
        id_to_delete = []
        
        for id in bed_occupation_percentage:
            if bed_occupation_percentage[id] == 0.0:
                unused_bed_counter += 1
                id_to_delete.append(id)
     
        #for id in id_to_delete:
        #    del bed_occupation_percentage[id]
        
        percentage_efficiency = round(100*sum(bed_occupation_percentage.values())/len(bed_occupation_percentage))
                                      
        return [percentage_efficiency, unused_bed_counter]

            
def get_departments():
    #   |Variable|                        |Name|          |beds| |limit| |queue|  |proirity queue|  |queue limit|
    #----------------------------------------------------------------------------------------------------------------
    emergency_room   = Department(   'emergency room',       0,     10,    None,         0,              10)  # queue length can't be over 10
    pre_Surgery_room = Department(  'pre surgery room',      0,     25,     0,          None,           None) 
    laboratory       = Department(     'laboratory',         0,     3,      0,           0,             None) # this department has priority over some patients
    operation_room   = Department(   'operation room',       0,     30,     0,           0,             None) # this department has priority over some patients
    ward             = Department(       'ward',             0,     40,     0,          None,           None)
    icu              = Department(        'ICU',             0,     20,     0,          None,           None)
    ccu              = Department(        'CCU',             0,     15,      0,          None,           None)
    return emergency_room, pre_Surgery_room, laboratory, operation_room, ward, icu, ccu
