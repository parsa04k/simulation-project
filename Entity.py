'''
this is file of the Entity of our simulation
    IMPORTANT VARIABLES :
    
        1- data_patients: this stores complex patients so that it could be extracted in end of simluation for metrics
        
        2- class Patient: our entity(patient) in simulation contains...
                Attributes    = [ type(emergency or normal) | type of surgery | ID | starting time(Entering the system) | ending time(Exiting the system)]
                Functions     = [ Saves Stating time and Ending time ]
                Probabilities = [ you can change the probability of patient type and surgery ]
        
'''

import random

data_patients = {'redo surgeries': []}

class PatientType:
    EMERGENCY = 'emergency'
    NORMAL = 'normal'

class SurgeryType:
    SIMPLE = 'simple'
    MODERATE = 'moderate'
    COMPLEX = 'complex'

class Patient:
    _id_counter = 0
    _probabilities = {
        # emergency variable
        'emergency': 0.25,
        
        # surgery type
        'simple': 0.5,
        'moderate': 0.45,
        'complex': 0.05
    }
    
    def __init__(self):
        self.id = self._generate_id()
        self.type = self.select_type()
        self.surgery = self.select_surgery()
        
        self.time_arrival: float | None = None
        self.time_departure: float | None = None
        
        self.time_of_surgery: float | None = None
        
        if self.surgery == SurgeryType.COMPLEX:
            self.redo_surgeries = 0
    
    @classmethod
    def _generate_id(cls) -> int:
        '''Generates a unique patient ID'''
        cls._id_counter += 1
        return cls._id_counter
    
    def select_type(self) -> PatientType:
        '''Selects patient type based on given probability'''
        return PatientType.EMERGENCY if random.uniform(0, 1) < self._probabilities['emergency'] else PatientType.NORMAL
    
    def select_surgery(self) -> SurgeryType:
        '''Selects surgery type based on given probabilities'''
        
        random_value = random.uniform(0, 1)
        if random_value <= self._probabilities['simple']:
            return SurgeryType.SIMPLE
        elif random_value <= (self._probabilities['moderate'] + self._probabilities['simple']):
            return SurgeryType.MODERATE
        else:
            return SurgeryType.COMPLEX
    
    def info(self) -> dict:
        '''Returns patient information as a dictionary'''
        return {
            'Patient id': self.id,
            'Patient type': self.type.value,
            'Patient Surgery': self.surgery.value
        }

    def set_arrival_time(self, time: int):
        '''Sets the arrival time of the patient'''
        self.time_arrival = time
        
    def set_departure_time(self, time: int):
        '''Sets the departure time of the patient'''
        self.time_departure = time
        
    def staying_in_system(self, staying_list: list) -> list:
        '''Calculates and appends the staying time to the list'''
        if self.time_arrival is not None and self.time_departure is not None:
            time_spent = self.time_departure - self.time_arrival
            staying_list.append(time_spent)
        return staying_list
    
    @classmethod
    def reset(cls):
        '''Reset the ID counter to 0'''
        cls._id_counter = 0


def add_patient_data(patient: Patient):
    global data_patients
    if patient.surgery == SurgeryType.COMPLEX:
        data_patients['redo surgeries'].append(patient)
    
    
